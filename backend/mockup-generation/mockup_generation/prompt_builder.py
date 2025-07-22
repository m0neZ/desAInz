"""Prompt building utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Any, Dict, List

from jinja2 import Template


@dataclass
class PromptContext:
    """Context data for prompt generation."""

    keywords: list[str]
    style: str = "vector art"
    extra: Dict[str, Any] = field(default_factory=dict)


TEMPLATES: List[Template] = [
    Template(
        "A {{ style }} design featuring {{ keywords | join(', ') }}. {{ extra.get('note', '') }}"
    ),
    Template(
        "Create a {{ style }} composition with {{ keywords | join(' and ') }}. {{ extra.get('note', '') }}"
    ),
]


def _mix_keywords(keywords: list[str], rng: Random) -> list[str]:
    """Return ``keywords`` shuffled and occasionally combined."""
    mixed = keywords.copy()
    rng.shuffle(mixed)
    if len(mixed) > 1 and rng.random() > 0.5:
        idx = rng.randrange(len(mixed) - 1)
        mixed[idx] = f"{mixed[idx]} and {mixed[idx + 1]}"
        del mixed[idx + 1]
    return mixed


def build_prompt(context: PromptContext, rng: Random | None = None) -> str:
    """Return a formatted prompt string using mixed keywords."""
    rng = rng or Random()
    keywords = _mix_keywords(context.keywords, rng)
    template = rng.choice(TEMPLATES)
    data = {**context.__dict__, "keywords": keywords}
    return template.render(**data)
