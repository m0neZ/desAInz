"""Database helpers for managing AI model metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from sqlalchemy import select, update

from backend.shared.db import engine, session_scope
from backend.shared.db.base import Base
from backend.shared.db.models import AIModel

Base.metadata.create_all(bind=engine)


@dataclass
class ModelInfo:
    """Dataclass representing an AI model entry."""

    id: int
    name: str
    version: str
    model_id: str
    details: dict[str, object] | None
    is_default: bool


def list_models() -> List[ModelInfo]:
    """Return all registered models."""
    with session_scope() as session:
        rows: Iterable[AIModel] = session.scalars(select(AIModel)).all()
        return [
            ModelInfo(
                id=row.id,
                name=row.name,
                version=row.version,
                model_id=row.model_id,
                details=row.details,
                is_default=row.is_default,
            )
            for row in rows
        ]


def set_default(model_id: int) -> None:
    """Set ``model_id`` as the default model."""
    with session_scope() as session:
        if session.get(AIModel, model_id) is None:
            raise ValueError("model not found")
        session.execute(update(AIModel).values(is_default=False))
        session.execute(
            update(AIModel).where(AIModel.id == model_id).values(is_default=True)
        )


def get_default_model_id() -> str:
    """Return the current default model identifier."""
    with session_scope() as session:
        ident = session.scalar(select(AIModel.model_id).where(AIModel.is_default))
    return ident or "stabilityai/stable-diffusion-xl-base-1.0"
