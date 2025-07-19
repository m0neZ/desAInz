"""Utilities for generating mockups with Stable Diffusion XL."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from PIL import Image

import requests
from diffusers import StableDiffusionXLPipeline
import torch
from .settings import settings

from .model_repository import get_default_model_id


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result from a generation request."""

    image_path: str
    duration: float


class MockupGenerator:
    """Generate mockups using Stable Diffusion XL with fallback."""

    def __init__(self) -> None:
        """Prepare the generator without loading the model."""
        self.model_id = get_default_model_id()
        self.pipeline: Optional[StableDiffusionXLPipeline] = None
        self._lock = Lock()

    def load(self) -> None:
        """Load or reload the diffusion pipeline on the available device."""
        current = get_default_model_id()
        with self._lock:
            if self.pipeline is None or self.model_id != current:
                self.model_id = current
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id
                ).to(device)
                self.pipeline.enable_attention_slicing()

    def generate(
        self, prompt: str, output_path: str, *, num_inference_steps: int = 30
    ) -> GenerationResult:
        """
        Generate an image.

        If local generation fails, an external provider is used as a
        fallback.

        Args:
            prompt: Text prompt describing the desired image.
            output_path: Filesystem path to save the resulting image.
            num_inference_steps: Number of inference steps for the model.

        Returns:
            GenerationResult containing the image path and duration.
        """
        from time import perf_counter

        self.load()
        assert self.pipeline is not None
        start = perf_counter()
        try:
            image = self.pipeline(
                prompt=prompt, num_inference_steps=num_inference_steps
            ).images[0]
        except (RuntimeError, ValueError, OSError) as exc:
            logger.warning("Local generation failed: %s. Falling back to API", exc)
            image = self._fallback_api(prompt)
        duration = perf_counter() - start
        image.save(output_path)
        return GenerationResult(image_path=output_path, duration=duration)

    def _fallback_api(self, prompt: str) -> Image.Image:
        """
        Fetch an image from a third-party provider.

        Args:
            prompt: Text prompt to send to the provider.

        Returns:
            PIL image from the external API.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        from io import BytesIO
        import base64
        import time

        session = requests.Session()
        provider = settings.fallback_provider.lower()

        for attempt in range(3):
            try:
                if provider == "dall-e":
                    response = session.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                        json={"prompt": prompt, "n": 1, "size": "1024x1024"},
                        timeout=30,
                    )
                    response.raise_for_status()
                    image_url = response.json()["data"][0]["url"]
                    image_resp = session.get(image_url, timeout=30)
                    image_resp.raise_for_status()
                    data = image_resp.content
                else:
                    response = session.post(
                        (
                            "https://api.stability.ai/v1/generation/"
                            "stable-diffusion-v1-6/text-to-image"
                        ),
                        headers={
                            "Authorization": f"Bearer {settings.stability_ai_api_key}",
                            "Accept": "application/json",
                        },
                        json={"text_prompts": [{"text": prompt}]},
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = base64.b64decode(response.json()["artifacts"][0]["base64"])
                return Image.open(BytesIO(data))
            except (requests.RequestException, OSError, ValueError) as exc:
                logger.warning("Fallback provider error: %s", exc)
                if attempt == 2:
                    raise
                time.sleep(2**attempt)

        raise RuntimeError("Failed to generate image via fallback provider")
