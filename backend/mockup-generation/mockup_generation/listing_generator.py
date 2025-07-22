"""Generate marketplace listing metadata using OpenAI or Claude."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List

import requests

from .settings import settings


@dataclass(slots=True)
class ListingMetadata:
    """Metadata for a marketplace listing."""

    title: str
    description: str
    tags: List[str]


class ListingGenerator:
    """Generate listing metadata via an LLM provider."""

    def __init__(self) -> None:
        """Initialize with API credentials from the environment."""
        self._openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self._openai_model = settings.openai_model
        self._claude_key = os.getenv("CLAUDE_API_KEY")
        self._session = requests.Session()

    def generate(self, keywords: List[str]) -> ListingMetadata:
        """Return listing metadata for ``keywords``."""
        prompt = (
            "Generate a short title, description and up to 5 tags as JSON "
            "with keys 'title', 'description', 'tags' for a design about: "
            f"{', '.join(keywords)}."
        )
        if self._openai_key:
            response = self._session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._openai_key}"},
                json={
                    "model": self._openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        elif self._claude_key:
            response = self._session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._claude_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-instant-1.2",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()["content"][0]["text"]
        else:
            raise RuntimeError("No API key provided")

        data = json.loads(content)
        tags = [str(tag) for tag in data.get("tags", [])]
        return ListingMetadata(
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            tags=tags,
        )
