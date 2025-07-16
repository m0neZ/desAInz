"""Prompt building utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from jinja2 import Template


@dataclass
class PromptContext:
    """Context data for prompt generation."""

    keywords: list[str]
    style: str = "vector art"
    extra: Dict[str, Any] = field(default_factory=dict)


TEMPLATE = Template(
    (
        "A {{ style }} design featuring {{ keywords | join(', ') }}. "
        "{{ extra.get('note', '') }}"
    )
)


def build_prompt(context: PromptContext) -> str:
    """Return a formatted prompt string."""
    return str(TEMPLATE.render(**context.__dict__))
