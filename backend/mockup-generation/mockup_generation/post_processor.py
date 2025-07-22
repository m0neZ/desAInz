"""Post-processing pipeline."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Callable, Mapping, Tuple, cast, TYPE_CHECKING, TypedDict

from PIL import Image

if TYPE_CHECKING:  # pragma: no cover - type imports
    from torch import Tensor
    from torch.nn import Module

from backend.shared.clip import load_clip, open_clip, torch

_clip_model: Module | None = None
_clip_preprocess: Callable[[Image.Image], Tensor] | None = None
_clip_lock = Lock()
_nsfw_tokens: Tensor | None = None


class MarketplaceRule(TypedDict, total=False):
    """Validation limits for a marketplace."""

    max_file_size_mb: int
    max_width: int
    max_height: int
    upload_limit: int
    selectors: Mapping[str, str]


_LIMITS: Mapping[str, MarketplaceRule] = {}


def _load_limits() -> Mapping[str, MarketplaceRule]:
    """Load marketplace limits from the YAML configuration file."""
    import yaml  # type: ignore

    path = Path(__file__).resolve().parents[3] / "config" / "marketplace_rules.yaml"
    if not path.exists():
        return {}
    return cast(Mapping[str, MarketplaceRule], yaml.safe_load(path.read_text()))


_LIMITS = _load_limits()


def _strictest(field: str, default: int) -> int:
    """Return the smallest configured value for ``field`` or ``default``."""
    values: list[int] = []
    for v in _LIMITS.values():
        val = v.get(field)
        if isinstance(val, int):
            values.append(val)
    return min(values) if values else default


MAX_FILE_SIZE_MB = _strictest("max_file_size_mb", 25)
MAX_WIDTH = _strictest("max_width", 15000)
MAX_HEIGHT = _strictest("max_height", 15000)


def remove_background(image: Image.Image) -> Image.Image:
    """Remove white background using OpenCV."""
    import cv2
    import numpy

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
    global _clip_model, _clip_preprocess, _nsfw_tokens
    loaded = load_clip("ViT-B-32")
    if loaded and open_clip is not None and torch is not None:
        _clip_model, _clip_preprocess, _tokenizer = loaded
        if _nsfw_tokens is None:
            _nsfw_tokens = open_clip.tokenize(["nsfw", "nudity", "pornography"]).to(
                "cpu"
            )
    if (
        _clip_model is None
        or _clip_preprocess is None
        or _nsfw_tokens is None
        or torch is None
    ):
        return
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
    return bool(image.mode == expected_mode)


def validate_dpi_image(
    image: Image.Image, expected_dpi: Tuple[int, int] = (300, 300)
) -> bool:
    """Return ``True`` if ``image`` has the expected DPI."""
    dpi = cast(Tuple[int, int], image.info.get("dpi", expected_dpi))
    return dpi == expected_dpi


def compress_lossless(image: Image.Image, output_path: Path) -> None:
    """Save ``image`` at ``output_path`` using lossless compression."""
    image.save(output_path, format="PNG", optimize=True)


def validate_dimensions(
    image: Image.Image,
    max_width: int = MAX_WIDTH,
    max_height: int = MAX_HEIGHT,
) -> bool:
    """Return ``True`` if ``image`` fits within ``max_width`` and ``max_height``."""
    width, height = image.size
    return width <= max_width and height <= max_height  # type: ignore[no-any-return]


def validate_file_size(path: Path, max_file_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    """Return ``True`` if ``path`` does not exceed ``max_file_size_mb``."""
    size_mb = path.stat().st_size / (1024 * 1024)
    return size_mb <= max_file_size_mb


def post_process_image(path: Path) -> Path:
    """Run the full post-processing pipeline on ``path``."""
    image: Image.Image = Image.open(path)
    image = remove_background(image)
    image = convert_to_cmyk(image)
    ensure_not_nsfw(image)
    if not validate_dpi_image(image):
        raise ValueError("Invalid DPI")
    if not validate_color_space(image):
        raise ValueError("Invalid color space")
    if not validate_dimensions(image):
        raise ValueError("Invalid dimensions")
    compress_lossless(image, path)
    if not validate_file_size(path):
        raise ValueError("File size too large")
    return path
