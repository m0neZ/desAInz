"""Utilities for analyzing resource metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import pandas as pd


@dataclass
class ResourceMetric:
    """Represents a single resource usage metric."""

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_usage_mb: Optional[float] = None


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
                    "disk_usage_mb": m.disk_usage_mb,
                }
                for m in metrics
            ]
        )
        if self._df.empty:
            self._df = pd.DataFrame(
                columns=["timestamp", "cpu_percent", "memory_mb", "disk_usage_mb"]
            )
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

    def average_disk_usage(self, last_n: int | None = None) -> float:
        """Return the average disk usage in MB if available."""
        if "disk_usage_mb" not in self._df.columns:
            return 0.0
        data = self._df.tail(last_n) if last_n else self._df
        return float(data["disk_usage_mb"].mean()) if not data.empty else 0.0

    def _trend(self, column: str, last_n: int | None = None) -> float:
        """Return slope per minute for ``column`` over the selected window."""
        data = self._df.tail(last_n) if last_n else self._df
        if data.empty or len(data) < 2:
            return 0.0
        delta_v = data[column].iloc[-1] - data[column].iloc[0]
        delta_t = (
            data["timestamp"].iloc[-1] - data["timestamp"].iloc[0]
        ).total_seconds() / 60
        return float(delta_v / delta_t) if delta_t else 0.0

    def cpu_trend(self, last_n: int | None = None) -> float:
        """Return CPU usage trend slope per minute."""
        return self._trend("cpu_percent", last_n)

    def memory_trend(self, last_n: int | None = None) -> float:
        """Return memory usage trend slope per minute."""
        return self._trend("memory_mb", last_n)

    def disk_usage_trend(self, last_n: int | None = None) -> float:
        """Return disk usage trend slope per minute."""
        if "disk_usage_mb" not in self._df.columns:
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
