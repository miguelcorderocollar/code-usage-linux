#!/usr/bin/env python3
"""Primary Waybar entrypoint for Code Usage."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from code_usage.waybar_app import main


if __name__ == "__main__":
    raise SystemExit(main())
