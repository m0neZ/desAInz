"""Utilities for analyzing resource metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import pandas as pd


@dataclass
class ResourceMetric:
    """Represents a single resource usage metric."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float


class MetricsAnalyzer:
    """Analyze resource metrics for optimization recommendations."""

    def __init__(self, metrics: Iterable[ResourceMetric]) -> None:
        """Initialize the analyzer with historical metrics."""
        self._df = pd.DataFrame(
            [
                {
                    "timestamp": m.timestamp,
                    "cpu_percent": m.cpu_percent,
                    "memory_mb": m.memory_mb,
                }
                for m in metrics
            ]
        )
        if self._df.empty:
            self._df = pd.DataFrame(columns=["timestamp", "cpu_percent", "memory_mb"])
        self._df.sort_values("timestamp", inplace=True)
        self._df.reset_index(drop=True, inplace=True)

    def average_cpu(self, last_n: int | None = None) -> float:
        """Return the average CPU usage."""
        data = self._df.tail(last_n) if last_n else self._df
        return float(data["cpu_percent"].mean()) if not data.empty else 0.0

    def average_memory(self, last_n: int | None = None) -> float:
        """Return the average memory usage in MB."""
        data = self._df.tail(last_n) if last_n else self._df
        return float(data["memory_mb"].mean()) if not data.empty else 0.0

    def recommend_optimizations(self) -> List[str]:
        """Provide optimization recommendations based on trends."""
        recommendations: List[str] = []
        if self.average_cpu(10) > 80:
            recommendations.append(
                "Consider scaling CPU resources or optimizing workloads"
            )
        if self.average_memory(10) > 1024:
            recommendations.append(
                "Investigate memory leaks or reduce memory footprint"
            )
        return recommendations

    def top_recommendations(self, limit: int = 3) -> List[str]:
        """
        Return the top optimization recommendations.

        This simply limits the list returned by :meth:`recommend_optimizations`.
        """

        return self.recommend_optimizations()[:limit]
