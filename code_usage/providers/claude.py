"""Anthropic Claude usage provider."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import requests

from code_usage.providers.base import ProviderClient, ProviderError, ProviderSnapshot, UsageWindow


class ClaudeCredentialReader:
    """Read Claude Code OAuth credentials."""

    CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")

    def is_configured(self) -> bool:
        """Return True when Claude credentials are present."""
        return os.path.exists(self.CREDENTIALS_PATH)

    def read_access_token(self) -> str:
        """Read the Claude access token from disk."""
        if not self.is_configured():
            raise ProviderError(
                "Not logged in to Claude Code. Run 'claude' and complete the login flow."
            )

        try:
            with open(self.CREDENTIALS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as error:
            raise ProviderError(
                "Claude credentials file is corrupted. Run 'claude' to re-authenticate."
            ) from error

        try:
            access_token = data["claudeAiOauth"]["accessToken"]
        except KeyError as error:
            raise ProviderError(
                "Invalid Claude credential format. Run 'claude' to re-authenticate."
            ) from error

        if not access_token:
            raise ProviderError(
                "Claude access token missing. Run 'claude' to re-authenticate."
            )

        return access_token


class ClaudeProviderClient(ProviderClient):
    """Fetch Claude usage from Anthropic's OAuth endpoint."""

    provider_name = "claude"
    display_name = "Claude Code Usage"
    API_ENDPOINT = "https://api.anthropic.com/api/oauth/usage"
    VERSION = "2.0.0"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.credential_reader = ClaudeCredentialReader()

    def is_configured(self) -> bool:
        """Return True when Claude credentials are available."""
        return self.credential_reader.is_configured()

    def fetch_usage(self) -> ProviderSnapshot:
        """Fetch and normalize Claude usage."""
        access_token = self.credential_reader.read_access_token()
        usage_data = self._fetch_usage_data(access_token)
        windows = {}

        five_hour = usage_data.get("five_hour", {})
        if five_hour:
            windows["session"] = UsageWindow(
                key="session",
                label="Session Usage",
                subtitle="5-hour window",
                utilization=float(five_hour.get("utilization", 0)),
                resets_at=five_hour.get("resets_at"),
            )

        seven_day = usage_data.get("seven_day", {})
        if seven_day:
            windows["weekly"] = UsageWindow(
                key="weekly",
                label="Weekly Usage",
                subtitle="7-day window",
                utilization=float(seven_day.get("utilization", 0)),
                resets_at=seven_day.get("resets_at"),
            )

        sonnet_only = usage_data.get("sonnet_only", {})
        if sonnet_only and sonnet_only.get("utilization") is not None:
            windows["sonnet"] = UsageWindow(
                key="sonnet",
                label="Sonnet Only",
                subtitle="7-day window",
                utilization=float(sonnet_only.get("utilization", 0)),
                resets_at=sonnet_only.get("resets_at"),
            )

        if not windows:
            raise ProviderError("Claude usage response did not include any windows.")

        return ProviderSnapshot(
            provider=self.provider_name,
            display_name=self.display_name,
            windows=windows,
        )

    def _fetch_usage_data(self, access_token: str, retry_count: int = 3) -> Dict[str, Any]:
        """Fetch raw Claude usage data with retry handling."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"CodeUsageLinux/{self.VERSION}",
            "anthropic-beta": "oauth-2025-04-20",
        }
        last_error: Exception | None = None

        for attempt in range(retry_count):
            try:
                response = self.session.get(
                    self.API_ENDPOINT,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code == 401:
                    raise ProviderError(
                        "Claude authentication expired. Run 'claude' to re-authenticate."
                    )
                response.raise_for_status()
                return response.json()
            except ProviderError:
                raise
            except requests.Timeout as error:
                last_error = error
            except requests.ConnectionError as error:
                last_error = error
            except requests.HTTPError as error:
                raise ProviderError(f"Claude API error: {error.response.status_code}") from error

            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)

        if last_error:
            raise ProviderError(f"Claude network error: {last_error}") from last_error
        raise ProviderError("Unknown Claude usage fetch failure.")

