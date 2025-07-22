"""Utilities for generating mockups with Stable Diffusion XL."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Optional, TYPE_CHECKING

from .settings import settings
from .model_repository import get_default_model_id

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from PIL import Image
    from diffusers import StableDiffusionXLPipeline


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result from a generation request."""

    image_path: str
    duration: float


class GenerationError(RuntimeError):
    """Raised when mockup generation fails after all retries."""


class MockupGenerator:
    """Generate mockups using Stable Diffusion XL with fallback."""

    def __init__(self) -> None:
        """Prepare the generator without loading the model."""
        self.model_id = get_default_model_id()
        self.pipeline: Optional["StableDiffusionXLPipeline"] = None
        self._lock = Lock()

    def load(self, model_identifier: str | None = None) -> None:
        """Load or reload the diffusion pipeline on the available device."""
        current = model_identifier or get_default_model_id()
        with self._lock:
            if self.pipeline is None or self.model_id != current:
                from diffusers import StableDiffusionXLPipeline
                import torch

                self.model_id = current
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id
                ).to(device)
                self.pipeline.enable_attention_slicing()

    def generate(
        self,
        prompt: str,
        output_path: str,
        *,
        num_inference_steps: int = 30,
        model_identifier: str | None = None,
    ) -> GenerationResult:
        """
        Generate an image.

        If local generation fails, an external provider is used as a fallback.

        Parameters
        ----------
        prompt : str
            Text prompt describing the desired image.
        output_path : str
            Filesystem path to save the resulting image.
        num_inference_steps : int, optional
            Number of inference steps for the model.
        model_identifier : str | None, optional
            Model identifier to load instead of the default.

        Returns
        -------
        GenerationResult
            Result containing the image path and duration.
        """
        from time import perf_counter

        if settings.use_comfyui:
            from .comfy_workflow import ComfyUIWorkflow

            workflow = {"prompt": prompt, "output": output_path}
            runner = ComfyUIWorkflow(settings.comfyui_url)
            res = runner.execute(workflow, output_path)
            return GenerationResult(image_path=res.image_path, duration=res.duration)

        self.load(model_identifier)
        assert self.pipeline is not None
        start = perf_counter()
        try:
            image = self.pipeline(
                prompt=prompt, num_inference_steps=num_inference_steps
            ).images[0]
        except (RuntimeError, ValueError, OSError) as exc:
            logger.warning("Local generation failed: %s. Falling back to API", exc)
            import asyncio

            image = asyncio.run(self._fallback_api(prompt))
        duration = perf_counter() - start
        image.save(output_path)
        return GenerationResult(image_path=output_path, duration=duration)

    async def _fallback_api(self, prompt: str) -> Image.Image:
        """
        Fetch an image from a third-party provider.

        Parameters
        ----------
        prompt : str
            Text prompt to send to the provider.

        Returns
        -------
        Image.Image
            Image from the external API.

        Raises
        ------
        GenerationError
            If all retry attempts fail.
        """
        from io import BytesIO
        import base64
        import httpx
        import asyncio
        from PIL import Image

        provider = settings.fallback_provider.lower()

        async with httpx.AsyncClient(timeout=30) as session:
            for attempt in range(1, 4):
                try:
                    if provider in {"openai", "dall-e", "dalle"}:
                        response = await session.post(
                            "https://api.openai.com/v1/images/generations",
                            headers={
                                "Authorization": f"Bearer {settings.openai_api_key}"
                            },
                            json={"prompt": prompt, "n": 1, "size": "1024x1024"},
                        )
                        response.raise_for_status()
                        image_url = response.json()["data"][0]["url"]
                        image_resp = await session.get(image_url)
                        image_resp.raise_for_status()
                        data = image_resp.content
                    else:
                        response = await session.post(
                            (
                                "https://api.stability.ai/v1/generation/"
                                "stable-diffusion-v1-6/text-to-image"
                            ),
                            headers={
                                "Authorization": f"Bearer {settings.stability_ai_api_key}",
                                "Accept": "application/json",
                            },
                            json={"text_prompts": [{"text": prompt}]},
                        )
                        response.raise_for_status()
                        data = base64.b64decode(
                            response.json()["artifacts"][0]["base64"]
                        )
                    return Image.open(BytesIO(data))
                except (httpx.HTTPError, OSError, ValueError, KeyError) as exc:
                    logger.warning("Fallback provider error: %s", exc)
                    if attempt == 3:
                        raise GenerationError(
                            "Failed to generate image via fallback provider"
                        ) from exc
                    await asyncio.sleep(2**attempt)

        raise GenerationError("Failed to generate image via fallback provider")

    def cleanup(self) -> None:
        """Release the diffusion pipeline and free CUDA memory."""
        with self._lock:
            if self.pipeline is not None:
                try:
                    self.pipeline.to("cpu")
                except Exception:  # pragma: no cover - device transfer optional
                    pass
                self.pipeline = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            if hasattr(torch.cuda, "ipc_collect"):
                torch.cuda.ipc_collect()
