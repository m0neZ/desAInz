"""Unit tests for model repository helpers."""

from pathlib import Path

from mockup_generation.model_repository import (
    get_default_model_id,
    list_models,
    set_default,
)

from backend.shared.db import session_scope
from backend.shared.db.models import AIModel


def test_default_model_switch(tmp_path: Path) -> None:
    """Verify ``set_default`` updates the active model."""
    with session_scope() as session:
        session.add(
            AIModel(id=1, name="base", version="1", model_id="model/a", is_default=True)
        )
        session.add(
            AIModel(id=2, name="new", version="2", model_id="model/b", is_default=False)
        )
        session.flush()

    assert get_default_model_id() == "model/a"
    set_default(2)
    assert get_default_model_id() == "model/b"
    models = list_models()
    assert len(models) == 2
