"""Minimal diffusers stub with StableDiffusionXLPipeline."""

from types import SimpleNamespace


class StableDiffusionXLPipeline:
    """Simplified pipeline implementation for tests."""

    @classmethod
    def from_pretrained(
        cls, *_args: object, **_kwargs: object
    ) -> "StableDiffusionXLPipeline":  # noqa: D401,E501
        """Return a new pipeline instance."""
        return cls()

    def to(self, _device: str) -> "StableDiffusionXLPipeline":  # pragma: no cover
        """Return ``self`` to allow method chaining."""
        return self

    def enable_attention_slicing(self) -> None:  # pragma: no cover
        """No-op for attention slicing."""
        return None

    def __call__(self, *args: object, **kwargs: object) -> SimpleNamespace:
        """Return an object with an ``images`` attribute."""
        return SimpleNamespace(images=[SimpleNamespace(save=lambda _p: None)])


__all__ = ["StableDiffusionXLPipeline"]
