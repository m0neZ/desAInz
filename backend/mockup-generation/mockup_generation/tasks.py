"""Celery tasks for mockup generation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from .celery_app import app
from .generator import MockupGenerator
from .prompt_builder import PromptContext, build_prompt
from .post_processor import (
    compress_lossless,
    convert_to_cmyk,
    ensure_not_nsfw,
    remove_background,
    validate_color_space,
    validate_dpi_image,
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
    if not validate_dpi_image(processed):
        raise ValueError("Invalid DPI")
    if not validate_color_space(processed):
        raise ValueError("Invalid color space")
    compress_lossless(processed, output_path)
    return str(output_path)
