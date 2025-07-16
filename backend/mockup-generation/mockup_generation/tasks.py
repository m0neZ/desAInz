"""Celery tasks for mockup generation."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image
from backend.shared.logging_config import configure_logging
from .celery_app import app
from .generator import MockupGenerator
from .prompt_builder import PromptContext, build_prompt
from .post_processor import (
    convert_to_cmyk,
    ensure_not_nsfw,
    remove_background,
    validate_dpi,
)


configure_logging()
logger = logging.getLogger(__name__)
generator = MockupGenerator()


@app.task  # type: ignore[misc]
def generate_mockup(keywords: list[str], output_dir: str) -> str:
    """Generate a mockup asynchronously."""
    import uuid

    correlation_id = str(uuid.uuid4())
    logger.info("task received", extra={"correlation_id": correlation_id})
    context = PromptContext(keywords=keywords)
    prompt = build_prompt(context)
    output_path = Path(output_dir) / "mockup.png"
    result = generator.generate(prompt, str(output_path))

    processed = remove_background(Image.open(result.image_path))
    processed = convert_to_cmyk(processed)
    ensure_not_nsfw(processed)
    processed.save(result.image_path)
    if not validate_dpi(result.image_path):
        raise ValueError("Invalid DPI")
    logger.info(
        "task completed",
        extra={"correlation_id": correlation_id, "path": str(result.image_path)},
    )
    return str(result.image_path)
