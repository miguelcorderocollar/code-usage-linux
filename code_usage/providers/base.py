"""Shared provider models and interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UsageWindow:
    """Normalized usage window for a provider."""

    key: str
    label: str
    subtitle: str
    utilization: float
    resets_at: Optional[str]


@dataclass
class ProviderSnapshot:
    """Normalized provider usage snapshot."""

    provider: str
    display_name: str
    windows: Dict[str, UsageWindow] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def max_utilization(self) -> float:
        """Return the highest utilization across all windows."""
        if not self.windows:
            return 0.0
        return max(window.utilization for window in self.windows.values())

    @property
    def status(self) -> str:
        """Return normalized severity status."""
        if self.max_utilization >= 90:
            return "critical"
        if self.max_utilization >= 70:
            return "warning"
        return "ok"


class ProviderError(RuntimeError):
    """Raised when a provider cannot fetch usage."""


class ProviderClient:
    """Base class for usage providers."""

    provider_name = "unknown"
    display_name = "Unknown"

    def is_configured(self) -> bool:
        """Return True when provider credentials appear available."""
        raise NotImplementedError

    def fetch_usage(self) -> ProviderSnapshot:
        """Fetch normalized usage data for the provider."""
        raise NotImplementedError
