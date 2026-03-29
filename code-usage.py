#!/usr/bin/env python3
"""Primary CLI entrypoint for Code Usage."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from code_usage.app import main


if __name__ == "__main__":
    raise SystemExit(main())
