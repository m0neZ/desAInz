"""Database helpers for managing AI model metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from sqlalchemy import delete, select, update

from backend.shared.db import engine, session_scope
from backend.shared.db.base import Base
from backend.shared.db.models import AIModel, GeneratedMockup

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


@dataclass
class GeneratedMockupInfo:
    """Dataclass representing a generated mockup entry."""

    id: int
    prompt: str
    num_inference_steps: int
    seed: int
    image_uri: str
    title: str
    description: str
    tags: list[str]


def register_model(
    name: str,
    version: str,
    model_id: str,
    *,
    details: dict[str, object] | None = None,
    is_default: bool = False,
) -> int:
    """Register a new model and return its database id."""
    with session_scope() as session:
        if is_default:
            session.execute(update(AIModel).values(is_default=False))
        obj = AIModel(
            name=name,
            version=version,
            model_id=model_id,
            details=details,
            is_default=is_default,
        )
        session.add(obj)
        session.flush()
        return int(obj.id)


def remove_model(model_id: int) -> None:
    """Delete the model with ``model_id`` from the database."""
    with session_scope() as session:
        session.execute(delete(AIModel).where(AIModel.id == model_id))


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


def get_model(model_id: int) -> Optional[ModelInfo]:
    """Return a model entry by primary key."""
    with session_scope() as session:
        row = session.get(AIModel, model_id)
        if row is None:
            return None
        return ModelInfo(
            id=row.id,
            name=row.name,
            version=row.version,
            model_id=row.model_id,
            details=row.details,
            is_default=row.is_default,
        )


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


def save_generated_mockup(
    prompt: str,
    num_inference_steps: int,
    seed: int,
    image_uri: str,
    title: str,
    description: str,
    tags: list[str],
) -> int:
    """Persist generation parameters and return the created row id."""
    with session_scope() as session:
        obj = GeneratedMockup(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            seed=seed,
            image_uri=image_uri,
            title=title,
            description=description,
            tags=tags,
        )
        session.add(obj)
        session.flush()
        return int(obj.id)


def list_generated_mockups() -> List[GeneratedMockupInfo]:
    """Return all stored generation parameter entries."""
    with session_scope() as session:
        rows: Iterable[GeneratedMockup] = session.scalars(select(GeneratedMockup)).all()
        return [
            GeneratedMockupInfo(
                id=row.id,
                prompt=row.prompt,
                num_inference_steps=row.num_inference_steps,
                seed=row.seed,
                image_uri=row.image_uri,
                title=row.title,
                description=row.description,
                tags=row.tags,
            )
            for row in rows
        ]
