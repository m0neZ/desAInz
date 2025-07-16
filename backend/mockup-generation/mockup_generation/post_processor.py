"""Post-processing pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, cast

import torch
from transformers import CLIPModel, CLIPProcessor

import cv2
import numpy
from PIL import Image


def remove_background(image: Image.Image) -> Image.Image:
    """Remove white background using OpenCV."""
    open_cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = numpy.zeros_like(gray)
    cv2.drawContours(mask, contours, -1, 255, -1)
    result = cv2.bitwise_and(open_cv_image, open_cv_image, mask=mask)
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))


def convert_to_cmyk(image: Image.Image) -> Image.Image:
    """Convert image to CMYK mode."""
    return image.convert("CMYK")


def validate_dpi(image_path: Path, expected_dpi: Tuple[int, int] = (300, 300)) -> bool:
    """Validate that image has the required DPI."""
    image = Image.open(image_path)
    dpi = cast(Tuple[int, int], image.info.get("dpi", expected_dpi))
    return dpi == expected_dpi


_clip_model: CLIPModel | None = None
_clip_processor: CLIPProcessor | None = None


def _load_clip() -> None:
    """Load the CLIP model if it hasn't been loaded yet."""
    global _clip_model, _clip_processor
    if _clip_model is None or _clip_processor is None:
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def is_nsfw(image: Image.Image) -> bool:
    """Return ``True`` if the given image is likely NSFW."""
    _load_clip()
    assert _clip_model and _clip_processor  # for mypy
    inputs = _clip_processor(text=["nsfw", "safe"], images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = _clip_model(**inputs)
    probs: torch.Tensor = outputs.logits_per_image.softmax(dim=1)[0]
    value = int(probs.argmax().item())
    return value == 0
