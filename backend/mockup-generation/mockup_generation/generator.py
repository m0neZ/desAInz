"""Image generation module using Stable Diffusion XL."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests  # type: ignore[import-untyped]
from diffusers import StableDiffusionXLPipeline
from PIL import Image
import torch


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Container for generation result."""

    image_path: str
    duration: float


class MockupGenerator:
    """Generate mockups using Stable Diffusion XL with fallback."""

    def __init__(
        self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    ) -> None:
        """Initialize the generator with the given model ID."""
        self.model_id = model_id
        self.pipeline: Optional[StableDiffusionXLPipeline] = None

    def load(self) -> None:
        """Load the diffusion pipeline on GPU if available."""
        if self.pipeline is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(self.model_id).to(
                device
            )
            self.pipeline.enable_attention_slicing()

    def generate(
        self, prompt: str, output_path: str, *, num_inference_steps: int = 30
    ) -> GenerationResult:
        """Generate an image or fall back to external API on failure."""
        from time import perf_counter

        self.load()
        assert self.pipeline is not None
        start = perf_counter()
        try:
            image = self.pipeline(
                prompt=prompt, num_inference_steps=num_inference_steps
            ).images[0]
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Local generation failed: %s. Falling back to API", exc)
            image = self._fallback_api(prompt)
        duration = perf_counter() - start
        image.save(output_path)
        return GenerationResult(image_path=output_path, duration=duration)

    def _fallback_api(self, prompt: str) -> Image.Image:
        """Call external API as a fallback mechanism."""
        response = requests.post(
            "https://api.example.com/generate",
            json={"prompt": prompt},
            timeout=60,
        )
        response.raise_for_status()
        from io import BytesIO

        return Image.open(BytesIO(response.content))
