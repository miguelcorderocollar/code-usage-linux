"""Experimental Codex usage provider."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests

from code_usage.providers.base import ProviderClient, ProviderError, ProviderSnapshot, UsageWindow


class CodexCredentialStore:
    """Read and refresh Codex ChatGPT auth credentials."""

    AUTH_PATH = os.path.expanduser("~/.codex/auth.json")
    REFRESH_ENDPOINT = "https://auth.openai.com/oauth/token"
    CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

    def is_configured(self) -> bool:
        """Return True when the Codex auth file exists."""
        return os.path.exists(self.AUTH_PATH)

    def load_auth_data(self) -> Dict[str, Any]:
        """Load auth data from disk."""
        if not self.is_configured():
            raise ProviderError("Not logged in to Codex. Run 'codex login'.")

        try:
            with open(self.AUTH_PATH, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as error:
            raise ProviderError(
                "Codex auth file is corrupted. Run 'codex login' again."
            ) from error

    def save_auth_data(self, auth_data: Dict[str, Any]) -> None:
        """Persist refreshed auth data."""
        with open(self.AUTH_PATH, "w", encoding="utf-8") as handle:
            json.dump(auth_data, handle, indent=2)

    def get_chatgpt_tokens(self) -> Dict[str, Any]:
        """Return tokens for ChatGPT-authenticated Codex."""
        auth_data = self.load_auth_data()
        if auth_data.get("auth_mode") != "chatgpt":
            if auth_data.get("OPENAI_API_KEY"):
                raise ProviderError(
                    "Codex is configured with an API key. This app only supports the experimental ChatGPT quota flow for Codex."
                )
            raise ProviderError("Codex is not configured in ChatGPT auth mode.")

        tokens = auth_data.get("tokens", {})
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        if not access_token:
            raise ProviderError("Codex auth is missing an access token. Run 'codex login' again.")
        if not refresh_token:
            raise ProviderError("Codex auth is missing a refresh token. Run 'codex login' again.")
        return auth_data

    def needs_refresh(self, auth_data: Dict[str, Any]) -> bool:
        """Return True when the access token should be refreshed."""
        last_refresh = auth_data.get("last_refresh")
        if not last_refresh:
            return True

        try:
            parsed = datetime.fromisoformat(last_refresh.replace("Z", "+00:00"))
        except ValueError:
            return True

        return parsed < datetime.now(timezone.utc) - timedelta(days=8)

    def refresh_tokens(self, auth_data: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        """Refresh the ChatGPT OAuth tokens."""
        refresh_token = auth_data["tokens"]["refresh_token"]
        response = requests.post(
            self.REFRESH_ENDPOINT,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "client_id": self.CLIENT_ID,
                "refresh_token": refresh_token,
            },
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise ProviderError(
                f"Codex token refresh failed with status {response.status_code}. Run 'codex login' again."
            )

        payload = response.json()
        auth_data["tokens"]["access_token"] = payload.get("access_token", auth_data["tokens"]["access_token"])
        auth_data["tokens"]["refresh_token"] = payload.get("refresh_token", auth_data["tokens"]["refresh_token"])
        if payload.get("id_token"):
            auth_data["tokens"]["id_token"] = payload["id_token"]
        auth_data["last_refresh"] = datetime.now(timezone.utc).isoformat()
        return auth_data


class CodexProviderClient(ProviderClient):
    """Fetch Codex usage from the experimental ChatGPT backend."""

    provider_name = "codex"
    display_name = "Codex Usage"
    API_ENDPOINT = "https://chatgpt.com/backend-api/wham/usage"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.credentials = CodexCredentialStore()

    def is_configured(self) -> bool:
        """Return True when Codex auth appears present."""
        return self.credentials.is_configured()

    def fetch_usage(self) -> ProviderSnapshot:
        """Fetch and normalize Codex usage."""
        auth_data = self.credentials.get_chatgpt_tokens()
        if self.credentials.needs_refresh(auth_data):
            auth_data = self.credentials.refresh_tokens(auth_data, timeout=self.timeout)

        payload = self._fetch_usage_data(auth_data)
        windows = self._build_windows(payload)
        if not windows:
            raise ProviderError("Codex usage response did not include any windows.")

        snapshot = ProviderSnapshot(
            provider=self.provider_name,
            display_name=self.display_name,
            windows=windows,
            extra={"plan_type": payload.get("plan_type")},
            warnings=[
                "Experimental backend; this undocumented Codex endpoint may break without notice."
            ],
        )
        self.credentials.save_auth_data(auth_data)
        return snapshot

    def _fetch_usage_data(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch raw usage and refresh once on auth failure."""
        response = self.session.get(
            self.API_ENDPOINT,
            headers=self._build_headers(auth_data),
            timeout=self.timeout,
        )

        if response.status_code in (401, 403):
            auth_data = self.credentials.refresh_tokens(auth_data, timeout=self.timeout)
            retry_response = self.session.get(
                self.API_ENDPOINT,
                headers=self._build_headers(auth_data),
                timeout=self.timeout,
            )
            if retry_response.status_code in (401, 403):
                raise ProviderError("Codex authentication expired. Run 'codex login' again.")
            if retry_response.status_code >= 400:
                raise ProviderError(
                    f"Codex experimental endpoint error: {retry_response.status_code}"
                )
            return retry_response.json()

        if response.status_code >= 400:
            raise ProviderError(f"Codex experimental endpoint error: {response.status_code}")

        return response.json()

    def _build_headers(self, auth_data: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers for the experimental endpoint."""
        headers = {
            "Authorization": f"Bearer {auth_data['tokens']['access_token']}",
            "Accept": "application/json",
        }
        account_id = auth_data["tokens"].get("account_id")
        if account_id:
            headers["ChatGPT-Account-Id"] = account_id
        return headers

    def _normalize_reset(self, reset_at: Optional[Any]) -> Optional[str]:
        """Normalize reset timestamp to ISO8601 string."""
        if reset_at is None:
            return None
        try:
            return datetime.fromtimestamp(int(reset_at), tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return None

    def _build_windows(self, payload: Dict[str, Any]) -> Dict[str, UsageWindow]:
        """Normalize Codex response windows."""
        windows: Dict[str, UsageWindow] = {}
        rate_limit = payload.get("rate_limit", {})
        primary = rate_limit.get("primary_window", {})
        secondary = rate_limit.get("secondary_window", {})
        code_review = payload.get("code_review_rate_limit", {}).get("primary_window", {})

        if primary:
            windows["session"] = UsageWindow(
                key="session",
                label="Session Usage",
                subtitle="5-hour window",
                utilization=float(primary.get("used_percent", 0)),
                resets_at=self._normalize_reset(primary.get("reset_at")),
            )

        if secondary:
            windows["weekly"] = UsageWindow(
                key="weekly",
                label="Weekly Usage",
                subtitle="7-day window",
                utilization=float(secondary.get("used_percent", 0)),
                resets_at=self._normalize_reset(secondary.get("reset_at")),
            )

        if code_review:
            windows["code_review"] = UsageWindow(
                key="code_review",
                label="Code Review",
                subtitle="7-day window",
                utilization=float(code_review.get("used_percent", 0)),
                resets_at=self._normalize_reset(code_review.get("reset_at")),
            )

        return windows

