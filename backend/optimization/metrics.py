"""Utilities for analyzing resource metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - imports for type checking
    from .storage import MetricsStore


@dataclass(slots=True)
class ResourceMetric:
    """Represents a single resource usage metric."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_usage_mb: Optional[float] = None


class MetricsAnalyzer:
    """Analyze resource metrics for optimization recommendations."""

    @classmethod
    def from_store(
        cls, store: "MetricsStore", limit: int | None = None
    ) -> "MetricsAnalyzer":
        """Create analyzer from a :class:`MetricsStore` instance."""
        if limit is None:
            metrics = store.get_metrics()
        else:
            metrics = store.get_recent_metrics(limit)
        return cls(metrics)

    def __init__(self, metrics: Iterable[ResourceMetric]) -> None:
        """Initialize the analyzer with historical metrics."""
        data = sorted(metrics, key=lambda m: m.timestamp)
        self._timestamps = np.array(
            [m.timestamp.timestamp() for m in data], dtype=float
        )
        self._cpu = np.array([m.cpu_percent for m in data], dtype=float)
        self._memory = np.array([m.memory_mb for m in data], dtype=float)
        self._disk = np.array(
            [m.disk_usage_mb if m.disk_usage_mb is not None else np.nan for m in data],
            dtype=float,
        )

    def average_cpu(self, last_n: int | None = None) -> float:
        """Return the average CPU usage."""
        data = self._cpu[-last_n:] if last_n else self._cpu
        return float(np.nanmean(data)) if data.size else 0.0

    def average_memory(self, last_n: int | None = None) -> float:
        """Return the average memory usage in MB."""
        data = self._memory[-last_n:] if last_n else self._memory
        return float(np.nanmean(data)) if data.size else 0.0

    def average_disk_usage(self, last_n: int | None = None) -> float:
        """Return the average disk usage in MB if available."""
        if np.isnan(self._disk).all():
            return 0.0
        data = self._disk[-last_n:] if last_n else self._disk
        return float(np.nanmean(data)) if data.size else 0.0

    def _trend(self, column: str, last_n: int | None = None) -> float:
        """Return slope per minute for ``column`` over the selected window."""
        if column == "cpu_percent":
            arr = self._cpu
        elif column == "memory_mb":
            arr = self._memory
        else:
            arr = self._disk
        idx = slice(-last_n, None) if last_n else slice(None)
        arr = arr[idx]
        ts = self._timestamps[idx]
        if arr.size < 2:
            return 0.0
        delta_v = arr[-1] - arr[0]
        delta_t = (ts[-1] - ts[0]) / 60
        return float(delta_v / delta_t) if delta_t else 0.0

    def cpu_trend(self, last_n: int | None = None) -> float:
        """Return CPU usage trend slope per minute."""
        return self._trend("cpu_percent", last_n)

    def memory_trend(self, last_n: int | None = None) -> float:
        """Return memory usage trend slope per minute."""
        return self._trend("memory_mb", last_n)

    def disk_usage_trend(self, last_n: int | None = None) -> float:
        """Return disk usage trend slope per minute."""
        if np.isnan(self._disk).all():
            return 0.0
        return self._trend("disk_usage_mb", last_n)

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
        if self.average_disk_usage(10) > 10 * 1024:
            recommendations.append(
                "Disk usage exceeds 10GB; clean up or increase storage"
            )
        if self.cpu_trend(20) > 0.5:
            recommendations.append(
                "CPU usage is trending upward; evaluate auto-scaling to control costs"
            )
        if self.memory_trend(20) > 50:
            recommendations.append(
                "Memory consumption is increasing; investigate to avoid over-provisioning"
            )
        if self.disk_usage_trend(20) > 100:
            recommendations.append(
                "Disk usage is growing quickly; remove unused data or expand storage"
            )
        return recommendations

    def top_recommendations(self, limit: int = 3) -> List[str]:
        """Return prioritized optimization recommendations."""
        recommendations: List[str] = []

        if self.average_cpu() > 70:
            recommendations.append(
                "Average CPU usage is consistently high; evaluate long-term scaling"
            )
        if self.average_memory() > 1024:
            recommendations.append(
                "Average memory usage exceeds 1GB; consider memory optimization"
            )
        if self.average_disk_usage() > 10 * 1024:
            recommendations.append(
                "Disk usage is high on average; plan for storage expansion"
            )
        if self.cpu_trend() > 0.5:
            recommendations.append(
                "CPU usage trend indicates growth; optimize workload distribution"
            )
        if self.memory_trend() > 50:
            recommendations.append(
                "Increasing memory trend detected; review application memory usage"
            )
        if self.disk_usage_trend() > 100:
            recommendations.append(
                "Disk consumption trend rising; regularly clean up stale files"
            )

        recommendations.extend(self.recommend_optimizations())

        unique: list[str] = []
        seen: set[str] = set()
        for rec in recommendations:
            if rec not in seen:
                unique.append(rec)
                seen.add(rec)

        return unique[:limit]
