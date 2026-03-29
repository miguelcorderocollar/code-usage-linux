#!/usr/bin/env python3
"""Primary Waybar entrypoint for Code Usage."""

import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
for candidate in (SCRIPT_PATH.parent, SCRIPT_PATH.parent.parent):
    if (candidate / "code_usage").exists():
        sys.path.insert(0, str(candidate))
        break

from code_usage.waybar_app import main


if __name__ == "__main__":
    raise SystemExit(main())
