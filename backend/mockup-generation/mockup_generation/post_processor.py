"""Post-processing pipeline."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

import open_clip
import torch
from torch.nn import Module
from typing import Callable, Tuple, cast

import cv2
import numpy
from PIL import Image

_clip_model: Module | None = None
_clip_preprocess: Callable[[Image.Image], torch.Tensor] | None = None
_clip_lock = Lock()
_nsfw_tokens = open_clip.tokenize(["nsfw", "nudity", "pornography"]).to("cpu")


def _load_clip() -> None:
    """Load CLIP model on first use."""
    global _clip_model, _clip_preprocess
    with _clip_lock:
        if _clip_model is None:
            _clip_model, _, _clip_preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="openai"
            )
            _clip_model.eval()


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


def ensure_not_nsfw(image: Image.Image, threshold: float = 0.3) -> None:
    """Raise ``ValueError`` if ``image`` is likely NSFW."""
    _load_clip()
    assert _clip_model is not None and _clip_preprocess is not None
    image_input = _clip_preprocess(image).unsqueeze(0)
    with torch.no_grad():
        image_features = _clip_model.encode_image(image_input)
        text_features = _clip_model.encode_text(_nsfw_tokens)
        scores = (image_features @ text_features.T).softmax(dim=-1)
    if float(scores[:, 0]) > threshold:
        raise ValueError("NSFW content detected")


def validate_dpi(image_path: Path, expected_dpi: Tuple[int, int] = (300, 300)) -> bool:
    """Validate that image has the required DPI."""
    image = Image.open(image_path)
    dpi = cast(Tuple[int, int], image.info.get("dpi", expected_dpi))
    return dpi == expected_dpi


def validate_color_space(image: Image.Image, expected_mode: str = "CMYK") -> bool:
    """Return ``True`` if ``image`` uses ``expected_mode`` color space."""
    return image.mode == expected_mode


def validate_dpi_image(
    image: Image.Image, expected_dpi: Tuple[int, int] = (300, 300)
) -> bool:
    """Return ``True`` if ``image`` has the expected DPI."""
    dpi = cast(Tuple[int, int], image.info.get("dpi", expected_dpi))
    return dpi == expected_dpi


def compress_lossless(image: Image.Image, output_path: Path) -> None:
    """Save ``image`` at ``output_path`` using lossless compression."""
    image.save(output_path, format="PNG", optimize=True)
