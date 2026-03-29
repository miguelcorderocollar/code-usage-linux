"""Helpers for process detection."""

from __future__ import annotations

import subprocess
from typing import Dict, List


DEFAULT_PROGRAMS = ["claude", "codex", "opencode"]


def parse_programs(programs_arg: str) -> List[str]:
    """Parse a comma-separated program list."""
    programs = [program.strip() for program in programs_arg.split(",") if program.strip()]
    return programs or DEFAULT_PROGRAMS[:]


def count_program_instances(programs: List[str]) -> Dict[str, int]:
    """Count running instances of tracked programs."""
    counts: Dict[str, int] = {}

    for program in programs:
        try:
            result = subprocess.run(
                ["pgrep", "-x", program, "-a"],
                capture_output=True,
                timeout=2,
                check=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            counts[program] = 0
            continue

        if result.returncode != 0:
            counts[program] = 0
            continue

        output = result.stdout.decode().strip()
        if not output:
            counts[program] = 0
            continue

        process_lines = [line for line in output.split("\n") if line]
        if program == "opencode":
            process_lines = [line for line in process_lines if "--port" in line]

        counts[program] = len(process_lines)

    return counts


def is_any_program_running(program_counts: Dict[str, int]) -> bool:
    """Return True when any tracked program is active."""
    return any(count > 0 for count in program_counts.values())

