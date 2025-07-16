"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from .celery_app import app
from .generator import MockupGenerator
from .prompt_builder import PromptContext, build_prompt
from .post_processor import (
    convert_to_cmyk,
    ensure_not_nsfw,
    remove_background,
    validate_dpi,
)


generator = MockupGenerator()


@app.task  # type: ignore[misc]
def generate_mockup(keywords: list[str], output_dir: str) -> str:
    """Generate a mockup asynchronously."""
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
    return str(result.image_path)
