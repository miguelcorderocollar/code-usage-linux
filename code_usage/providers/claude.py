"""Claude provider implementation."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

import requests

from code_usage.providers.base import ProviderError, ProviderUsage, UsageProvider, UsageWindow


class ClaudeProvider(UsageProvider):
    """Anthropic OAuth usage provider."""

    key = "claude"
    display_name = "Claude Code"
    credentials_path = os.path.expanduser("~/.claude/.credentials.json")
    api_endpoint = "https://api.anthropic.com/api/oauth/usage"
    version = "2.0.0"

    def __init__(self, timeout: int = 10) -> None:
        """Initialize the provider."""
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_usage(self) -> ProviderUsage:
        """Fetch Claude usage data."""
        access_token = self._read_access_token()
        payload = self._fetch_payload(access_token)
        windows: List[UsageWindow] = []

        five_hour = payload.get("five_hour", {})
        if five_hour:
            windows.append(
                UsageWindow(
                    key="session",
                    title="Session Usage",
                    subtitle="5-hour window",
                    utilization=float(five_hour.get("utilization", 0)),
                    resets_at=five_hour.get("resets_at"),
                    limit_window_seconds=5 * 60 * 60,
                )
            )

        seven_day = payload.get("seven_day", {})
        if seven_day:
            windows.append(
                UsageWindow(
                    key="weekly",
                    title="Weekly Usage",
                    subtitle="7-day window",
                    utilization=float(seven_day.get("utilization", 0)),
                    resets_at=seven_day.get("resets_at"),
                    limit_window_seconds=7 * 24 * 60 * 60,
                )
            )

        sonnet_only = payload.get("sonnet_only", {})
        if sonnet_only and sonnet_only.get("utilization") is not None:
            windows.append(
                UsageWindow(
                    key="sonnet",
                    title="Sonnet Only",
                    subtitle="7-day window",
                    utilization=float(sonnet_only.get("utilization", 0)),
                    resets_at=sonnet_only.get("resets_at"),
                    limit_window_seconds=7 * 24 * 60 * 60,
                )
            )

        return ProviderUsage(
            key=self.key,
            display_name=self.display_name,
            windows=windows,
            plan_type=None,
            metadata={"source": "anthropic-oauth"},
        )

    def _read_access_token(self) -> str:
        """Read Claude OAuth access token from disk."""
        if not os.path.exists(self.credentials_path):
            raise ProviderError(
                "Not logged in to Claude Code.\n"
                "Please run 'claude' in your terminal and complete the login flow."
            )

        try:
            with open(self.credentials_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "Claude credentials file is corrupted.\n"
                "Please run 'claude' to re-authenticate."
            ) from exc

        access_token = (
            data.get("claudeAiOauth", {})
            .get("accessToken")
        )
        if not access_token:
            raise ProviderError(
                "Invalid Claude credential format.\n"
                "Please run 'claude' to re-authenticate."
            )
        return access_token

    def _fetch_payload(self, access_token: str, retry_count: int = 3) -> Dict[str, Any]:
        """Fetch usage JSON with retries."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"CodeUsageLinux/{self.version}",
            "anthropic-beta": "oauth-2025-04-20",
        }

        last_error: Exception | None = None
        for attempt in range(retry_count):
            try:
                response = self.session.get(
                    self.api_endpoint,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code == 401:
                    raise ProviderError(
                        "Claude authentication expired.\n"
                        "Please run 'claude' to re-authenticate."
                    )
                if response.status_code == 429:
                    raise ProviderError(
                        "Claude usage API rate limit reached (HTTP 429).\n"
                        "Please wait and try again."
                    )
                response.raise_for_status()
                return response.json()
            except ProviderError:
                raise
            except requests.HTTPError as exc:
                raise ProviderError(
                    f"Claude usage API error: {exc.response.status_code}"
                ) from exc
            except requests.Timeout as exc:
                last_error = exc
            except requests.ConnectionError as exc:
                last_error = exc

            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)

        if last_error is not None:
            raise ProviderError(f"Claude network error: {last_error}") from last_error

        raise ProviderError("Claude usage request failed for an unknown reason.")
