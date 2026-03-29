#!/usr/bin/env python3
"""Backward-compatible wrapper for Claude-specific CLI usage."""

from code_usage.cli import run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli(default_provider="claude"))
