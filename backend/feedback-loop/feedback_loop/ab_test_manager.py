"""A/B test manager using PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import DateTime, Float, Integer, MetaData, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Base class for declarative models."""

    metadata = MetaData()


class ABTestResult(Base):
    """SQLAlchemy model for A/B test results."""

    __tablename__ = "ab_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    variant: Mapped[str] = mapped_column(String, nullable=False)
    reward: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)


def get_engine(dsn: str):
    """Create a SQLAlchemy engine."""
    return create_engine(dsn)


@dataclass
class ABTestManager:
    """Manage A/B test results storage."""

    engine_dsn: str

    def __post_init__(self) -> None:
        """Initialize database engine and create tables."""
        self.engine = get_engine(self.engine_dsn)
        Base.metadata.create_all(self.engine)

    def record_result(self, variant: str, reward: float, timestamp) -> None:
        """Store a new A/B test result."""
        with Session(self.engine) as session:
            session.add(
                ABTestResult(variant=variant, reward=reward, timestamp=timestamp)
            )
            session.commit()

    def results(self, variant: Optional[str] = None) -> Iterable[ABTestResult]:
        """Yield stored results filtered by variant if provided."""
        with Session(self.engine) as session:
            query = session.query(ABTestResult)
            if variant:
                query = query.filter_by(variant=variant)
            yield from query.all()
