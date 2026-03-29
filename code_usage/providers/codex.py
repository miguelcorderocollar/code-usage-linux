"""Experimental Codex provider implementation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from code_usage.providers.base import ProviderError, ProviderUsage, UsageProvider, UsageWindow


class CodexProvider(UsageProvider):
    """ChatGPT-auth usage provider for Codex."""

    key = "codex"
    display_name = "Codex"
    experimental = True
    auth_path = os.path.expanduser("~/.codex/auth.json")
    usage_endpoint = "https://chatgpt.com/backend-api/wham/usage"
    refresh_endpoint = "https://auth.openai.com/oauth/token"
    client_id = "app_EMoamEEZ73f0CkXaXp7hrann"
    version = "2.0.0"

    def __init__(self, timeout: int = 15) -> None:
        """Initialize the provider."""
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_usage(self) -> ProviderUsage:
        """Fetch and normalize Codex usage data."""
        auth_data = self._read_auth()
        tokens = auth_data.get("tokens", {})
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise ProviderError(
                "Experimental Codex support could not find an access token in ~/.codex/auth.json.\n"
                "Please run 'codex' and complete the login flow."
            )

        response = self._request_usage(access_token)
        if response.status_code == 401:
            if not refresh_token:
                raise ProviderError(
                    "Experimental Codex support found expired authentication with no refresh token.\n"
                    "Please run 'codex' and sign in again."
                )
            refreshed = self._refresh_tokens(refresh_token)
            auth_data = self._persist_refresh(auth_data, refreshed)
            access_token = auth_data["tokens"].get("access_token")
            response = self._request_usage(access_token)

        if response.status_code == 401:
            raise ProviderError(
                "Experimental Codex support could not refresh ChatGPT authentication.\n"
                "Please run 'codex' and sign in again."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ProviderError(
                f"Experimental Codex usage API error: {response.status_code}"
            ) from exc

        payload = response.json()
        windows = self._normalize_windows(payload)
        return ProviderUsage(
            key=self.key,
            display_name=self.display_name,
            windows=windows,
            plan_type=payload.get("plan_type"),
            experimental=True,
            warning="Experimental backend based on ChatGPT web quota data.",
            metadata={"source": "chatgpt-wham-usage"},
        )

    def _read_auth(self) -> Dict[str, Any]:
        """Load Codex auth state from disk."""
        if not os.path.exists(self.auth_path):
            raise ProviderError(
                "Experimental Codex support could not find ~/.codex/auth.json.\n"
                "Please run 'codex' and complete the login flow."
            )

        try:
            with open(self.auth_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                "Experimental Codex auth file is corrupted.\n"
                "Please run 'codex' to re-authenticate."
            ) from exc

    def _request_usage(self, access_token: str) -> requests.Response:
        """Request Codex usage data."""
        return self.session.get(
            self.usage_endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": f"CodeUsageLinux/{self.version}",
            },
            timeout=self.timeout,
        )

    def _refresh_tokens(self, refresh_token: str) -> Dict[str, Optional[str]]:
        """Refresh Codex ChatGPT tokens using the upstream OAuth client id."""
        response = self.session.post(
            self.refresh_endpoint,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"CodeUsageLinux/{self.version}",
            },
            json={
                "client_id": self.client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=self.timeout,
        )

        if response.status_code == 401:
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            code = None
            if isinstance(payload.get("error"), dict):
                code = payload["error"].get("code")
            elif isinstance(payload.get("error"), str):
                code = payload.get("error")

            suffix = f" ({code})" if code else ""
            raise ProviderError(
                "Experimental Codex support could not refresh the ChatGPT token"
                f"{suffix}.\nPlease run 'codex' and sign in again."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ProviderError(
                f"Experimental Codex token refresh failed with status {response.status_code}."
            ) from exc

        payload = response.json()
        return {
            "id_token": payload.get("id_token"),
            "access_token": payload.get("access_token"),
            "refresh_token": payload.get("refresh_token"),
        }

    def _persist_refresh(
        self,
        auth_data: Dict[str, Any],
        refreshed: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """Persist refreshed tokens back to ~/.codex/auth.json."""
        auth_data.setdefault("tokens", {})
        for key, value in refreshed.items():
            if value:
                auth_data["tokens"][key] = value
        auth_data["last_refresh"] = datetime.now(timezone.utc).isoformat()

        with open(self.auth_path, "w", encoding="utf-8") as handle:
            json.dump(auth_data, handle, indent=2)
            handle.write("\n")

        return auth_data

    def _normalize_windows(self, payload: Dict[str, Any]) -> List[UsageWindow]:
        """Normalize ChatGPT quota windows."""
        windows: List[UsageWindow] = []
        rate_limit = payload.get("rate_limit", {})
        code_review = payload.get("code_review_rate_limit", {})

        primary = self._window_from_snapshot(
            rate_limit.get("primary_window"),
            key="session",
            title="Session Usage",
            default_subtitle="5-hour window",
        )
        if primary:
            windows.append(primary)

        secondary = self._window_from_snapshot(
            rate_limit.get("secondary_window"),
            key="weekly",
            title="Weekly Usage",
            default_subtitle="7-day window",
        )
        if secondary:
            windows.append(secondary)

        review = self._window_from_snapshot(
            code_review.get("primary_window"),
            key="code_review",
            title="Code Review Usage",
            default_subtitle="weekly window",
        )
        if review:
            windows.append(review)

        return windows

    def _window_from_snapshot(
        self,
        snapshot: Optional[Dict[str, Any]],
        *,
        key: str,
        title: str,
        default_subtitle: str,
    ) -> Optional[UsageWindow]:
        """Convert a WHAM window snapshot to a normalized window."""
        if not isinstance(snapshot, dict):
            return None

        limit_window_seconds = snapshot.get("limit_window_seconds")
        subtitle = self._subtitle_for_seconds(limit_window_seconds) or default_subtitle
        reset_at = snapshot.get("reset_at")
        resets_at = None
        if isinstance(reset_at, int):
            resets_at = datetime.fromtimestamp(reset_at, tz=timezone.utc).isoformat()

        return UsageWindow(
            key=key,
            title=title,
            subtitle=subtitle,
            utilization=float(snapshot.get("used_percent", 0)),
            resets_at=resets_at,
            limit_window_seconds=limit_window_seconds,
        )

    def _subtitle_for_seconds(self, seconds: Any) -> Optional[str]:
        """Render a human-friendly window label from seconds."""
        if not isinstance(seconds, int) or seconds <= 0:
            return None
        if seconds % 604800 == 0:
            weeks = seconds // 604800
            return "7-day window" if weeks == 1 else f"{weeks}-week window"
        if seconds % 86400 == 0:
            days = seconds // 86400
            return "1-day window" if days == 1 else f"{days}-day window"
        if seconds % 3600 == 0:
            hours = seconds // 3600
            return "1-hour window" if hours == 1 else f"{hours}-hour window"
        minutes = seconds // 60
        return "1-minute window" if minutes == 1 else f"{minutes}-minute window"
