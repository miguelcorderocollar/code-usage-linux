#!/usr/bin/env python3
"""Waybar module for provider-neutral code usage monitoring."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_usage.waybar_support import run_waybar


if __name__ == "__main__":
    raise SystemExit(run_waybar())
