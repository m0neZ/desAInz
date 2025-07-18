"""Utilities for A/B testing and budget allocation."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from typing import Iterator, Mapping

from sqlalchemy import Boolean, Integer, String, create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
import numpy as np


class Base(DeclarativeBase):
    """Base class for ORM models."""


class TestResult(Base):
    """Record of an A/B test interaction."""

    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    variant: Mapped[str] = mapped_column(String(1))
    success: Mapped[bool] = mapped_column(Boolean)


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
