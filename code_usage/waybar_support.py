"""Waybar application helpers."""

from __future__ import annotations

import argparse
import json

from code_usage.cli import collect_provider_results
from code_usage.formatting import build_waybar_output, select_primary_provider
from code_usage.processes import DEFAULT_PROGRAMS, count_program_instances, parse_programs


def build_argument_parser(default_provider: str = "auto") -> argparse.ArgumentParser:
    """Build the Waybar argument parser."""
    parser = argparse.ArgumentParser(
        description="Waybar module for code usage monitoring"
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "codex"],
        default=default_provider,
        help="Usage provider to display (default: %(default)s)",
    )
    parser.add_argument(
        "--programs",
        type=str,
        default=",".join(DEFAULT_PROGRAMS),
        help="Comma-separated list of programs to track",
    )
    return parser


def run_waybar(default_provider: str = "auto") -> int:
    """Run the Waybar module."""
    args = build_argument_parser(default_provider=default_provider).parse_args()
    programs = parse_programs(args.programs)
    program_counts = count_program_instances(programs)

    snapshots, errors = collect_provider_results(args.provider)
    selected_provider = select_primary_provider(snapshots) if snapshots else args.provider
    output = build_waybar_output(
        snapshots,
        selected_provider,
        errors,
        program_counts,
    )
    print(json.dumps(output))
    return 0

