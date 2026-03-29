"""Shared application helpers for Code Usage."""

from __future__ import annotations

from typing import List, Tuple

from code_usage.providers.base import ProviderError, ProviderUsage, UsageProvider
from code_usage.providers.claude import ClaudeProvider
from code_usage.providers.codex import CodexProvider


def get_provider(provider_name: str) -> UsageProvider:
    """Return a provider instance by name."""
    providers = {
        "claude": ClaudeProvider(),
        "codex": CodexProvider(),
    }
    try:
        return providers[provider_name]
    except KeyError as exc:
        raise ProviderError(f"Unsupported provider: {provider_name}") from exc


def resolve_provider_usage(provider_name: str) -> Tuple[ProviderUsage, List[ProviderUsage]]:
    """Fetch usage data for one provider or auto-select across providers."""
    if provider_name != "auto":
        provider_usage = get_provider(provider_name).fetch_usage()
        return provider_usage, [provider_usage]

    successes: List[ProviderUsage] = []
    failures: List[str] = []
    for candidate in ("claude", "codex"):
        try:
            successes.append(get_provider(candidate).fetch_usage())
        except ProviderError as exc:
            failures.append(f"{candidate}: {exc}")

    if not successes:
        failure_text = "\n".join(failures)
        raise ProviderError(
            "No providers could be queried successfully.\n"
            f"{failure_text}"
        )

    successes.sort(key=lambda provider: provider.max_utilization, reverse=True)
    return successes[0], successes
