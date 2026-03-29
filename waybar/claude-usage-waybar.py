#!/usr/bin/env python3
"""Compatibility shim for the renamed code-usage-waybar helper."""

import sys
from pathlib import Path
from typing import List


SCRIPT_PATH = Path(__file__).resolve()
for candidate in (SCRIPT_PATH.parent, SCRIPT_PATH.parent.parent):
    if (candidate / "code_usage").exists():
        sys.path.insert(0, str(candidate))
        break

from code_usage.waybar_app import main


def _legacy_argv() -> List[str]:
    """Preserve Claude-only defaults for the compatibility alias."""
    argv = sys.argv[1:]
    if "--provider" not in argv:
        return ["--provider", "claude", *argv]
    return argv


if __name__ == "__main__":
    raise SystemExit(main(_legacy_argv()))
