"""Waybar helper entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from code_usage import resolve_provider_usage
from code_usage.formatting import build_waybar_payload
from code_usage.processes import DEFAULT_PROGRAMS, count_program_instances, parse_programs
from code_usage.providers.base import ProviderError

LOADING_MARKER_PATH = "/tmp/code-usage-waybar.loading"


def build_parser() -> argparse.ArgumentParser:
    """Build the Waybar parser."""
    parser = argparse.ArgumentParser(
        description="Waybar module for Code Usage monitoring",
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "codex"],
        default="auto",
        help="Provider to query (default: auto)",
    )
    parser.add_argument(
        "--programs",
        type=str,
        default=",".join(DEFAULT_PROGRAMS),
        help="Comma-separated list of programs to track",
    )
    return parser


def _error_payload(message: str) -> dict:
    """Render a Waybar-friendly error payload."""
    return {
        "text": "\uf071",
        "tooltip": message,
        "class": "error",
    }


def _loading_payload() -> dict:
    """Render a transient loading payload for click-triggered refreshes."""
    return {
        "text": "\uf121 ...",
        "tooltip": "Manual refresh in progress...",
        "class": ["loading", "manual-refresh"],
        "percentage": 0,
        "alt": "loading",
    }


def _consume_loading_marker() -> bool:
    """Return True when a click-triggered refresh marker is present."""
    try:
        os.remove(LOADING_MARKER_PATH)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        # Marker handling should never break the module output.
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Run the Waybar helper."""
    parser = build_parser()
    args = parser.parse_args(argv)
    programs = parse_programs(args.programs)

    if _consume_loading_marker():
        print(json.dumps(_loading_payload()))
        return 0

    try:
        primary, providers = resolve_provider_usage(args.provider)
        payload = build_waybar_payload(primary, providers, count_program_instances(programs))
        print(json.dumps(payload))
        return 0
    except ProviderError as exc:
        print(json.dumps(_error_payload(str(exc))))
        return 0
    except Exception as exc:
        print(json.dumps(_error_payload(f"Unexpected error: {exc}")))
        return 0
