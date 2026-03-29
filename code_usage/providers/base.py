"""Base provider contracts and shared data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UsageWindow:
    """Normalized usage window for a provider."""

    key: str
    title: str
    subtitle: str
    utilization: float
    resets_at: Optional[str]
    limit_window_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "key": self.key,
            "title": self.title,
            "subtitle": self.subtitle,
            "utilization": int(self.utilization),
            "resets_at": self.resets_at,
            "limit_window_seconds": self.limit_window_seconds,
        }


@dataclass
class ProviderUsage:
    """Normalized provider usage payload."""

    key: str
    display_name: str
    windows: List[UsageWindow]
    plan_type: Optional[str] = None
    experimental: bool = False
    warning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def max_utilization(self) -> float:
        """Return the highest current utilization."""
        if not self.windows:
            return 0.0
        return max(window.utilization for window in self.windows)

    @property
    def status(self) -> str:
        """Return severity status for the provider."""
        if self.max_utilization >= 90:
            return "critical"
        if self.max_utilization >= 70:
            return "warning"
        return "ok"

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "key": self.key,
            "display_name": self.display_name,
            "plan_type": self.plan_type,
            "experimental": self.experimental,
            "warning": self.warning,
            "status": self.status,
            "max_utilization": int(self.max_utilization),
            "windows": [window.to_dict() for window in self.windows],
            "metadata": self.metadata,
        }


class ProviderError(RuntimeError):
    """User-facing provider failure."""


class UsageProvider(ABC):
    """Abstract provider interface."""

    key: str
    display_name: str
    experimental: bool = False

    @abstractmethod
    def fetch_usage(self) -> ProviderUsage:
        """Fetch usage data and normalize it."""
