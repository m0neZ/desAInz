"""Factories for tests."""

from __future__ import annotations

import factory
from signal_ingestion.models import Signal


class SignalFactory(factory.Factory):
    """Factory for ``Signal``."""

    class Meta:
        """Factory configuration."""

        model = Signal

    id = factory.Sequence(lambda n: n)
    source = "test"
    content = "{}"
