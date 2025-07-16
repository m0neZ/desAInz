"""Post-processing pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, cast

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


def validate_color_space(image: Image.Image, expected_mode: str = "CMYK") -> bool:
    """Return ``True`` if the image uses the expected color space."""
    return image.mode == expected_mode


def validate_dpi_image(
    image: Image.Image, expected_dpi: Tuple[int, int] = (300, 300)
) -> bool:
    """Return ``True`` if ``image`` has the given DPI metadata."""
    dpi = cast(Tuple[int, int], image.info.get("dpi", expected_dpi))
    return dpi == expected_dpi


def compress_image(image: Image.Image, output_path: Path) -> None:
    """Save ``image`` using lossless compression."""
    image.save(output_path, format="PNG", optimize=True, compress_level=9)
