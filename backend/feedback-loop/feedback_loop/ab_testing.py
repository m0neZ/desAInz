"""Utilities for A/B testing and budget allocation."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Iterator, Mapping

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
import numpy as np


class Base(DeclarativeBase):
    """Base class for ORM models."""


class TestResult(Base):
    """Record of an A/B test interaction."""

    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    variant: Mapped[str] = mapped_column(String(1))
    success: Mapped[bool] = mapped_column(Boolean)


class DailySummary(Base):
    """Aggregated conversions for a single day."""

    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True)
    conversions_a: Mapped[int] = mapped_column(Integer, default=0)
    conversions_b: Mapped[int] = mapped_column(Integer, default=0)


@dataclass
class BudgetAllocation:
    """Promotion budget allocation for variants."""

    variant_a: float
    variant_b: float


def create_engine_and_session(url: str) -> tuple[Session, sessionmaker]:
    """Create SQLAlchemy engine and session factory."""
    if url.startswith("sqlite") and ":memory:" in url:
        engine = create_engine(
            url,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    return engine, SessionLocal


class ABTestManager:
    """Manage A/B test results and compute budget allocation."""

    def __init__(self, database_url: str = "sqlite:///abtest.db") -> None:
        """Initialize manager with given database URL."""
        self.engine, self.SessionLocal = create_engine_and_session(database_url)
        self.daily_summary_class = DailySummary

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional session scope."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def record_result(self, variant: str, success: bool) -> None:
        """Store the result of showing a variant."""
        with self.session_scope() as session:
            session.add(TestResult(variant=variant, success=success))

    def conversion_totals(self) -> Mapping[str, int]:
        """Return cumulative conversions for each variant."""
        with self.session_scope() as session:
            results = session.execute(
                select(TestResult.variant, func.count())
                .where(TestResult.success.is_(True))
                .group_by(TestResult.variant)
            ).all()
        totals: dict[str, int] = {"A": 0, "B": 0}
        for variant, count in results:
            totals[variant] = int(count)
        return totals

    def _variant_stats(self) -> Mapping[str, tuple[int, int]]:
        """Return successes and failures for each variant."""
        with self.session_scope() as session:
            results = session.execute(
                select(TestResult.variant, TestResult.success)
            ).all()
        stats: dict[str, tuple[int, int]] = {"A": (0, 0), "B": (0, 0)}
        for variant, success in results:
            succ, fail = stats[variant]
            if success:
                succ += 1
            else:
                fail += 1
            stats[variant] = (succ, fail)
        return stats

    def allocate_budget(self, total_budget: float) -> BudgetAllocation:
        """Allocate budget between variants using Thompson Sampling."""
        stats = self._variant_stats()
        samples = {}
        for variant, (succ, fail) in stats.items():
            samples[variant] = np.random.beta(succ + 1, fail + 1)
        total_sample = sum(samples.values())
        if total_sample == 0:
            share_a = share_b = 0.5
        else:
            share_a = samples["A"] / total_sample
            share_b = samples["B"] / total_sample
        return BudgetAllocation(
            variant_a=total_budget * share_a,
            variant_b=total_budget * share_b,
        )

    def record_summary(self) -> None:
        """Aggregate today's conversions and persist them."""
        today = date.today()
        with self.session_scope() as session:
            counts = {"A": 0, "B": 0}
            stmt = (
                select(TestResult.variant, func.count())
                .where(
                    TestResult.success.is_(True),
                    func.date(TestResult.timestamp) == today,
                )
                .group_by(TestResult.variant)
            )
            for variant, cnt in session.execute(stmt):
                counts[variant] = int(cnt)
            if counts["A"] == 0 and counts["B"] == 0:
                return
            summary = session.execute(
                select(DailySummary).where(DailySummary.day == today)
            ).scalar_one_or_none()
            if summary is None:
                summary = DailySummary(day=today)
                session.add(summary)
            summary.conversions_a = counts["A"]
            summary.conversions_b = counts["B"]
