#!/usr/bin/env python3
"""Compatibility shim for the renamed code-usage-waybar helper."""

import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from code_usage.waybar_app import main


def _legacy_argv() -> List[str]:
    """Preserve Claude-only defaults for the compatibility alias."""
    argv = sys.argv[1:]
    if "--provider" not in argv:
        return ["--provider", "claude", *argv]
    return argv


if __name__ == "__main__":
    raise SystemExit(main(_legacy_argv()))
