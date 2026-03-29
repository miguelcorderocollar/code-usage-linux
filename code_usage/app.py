"""CLI application entrypoint helpers."""

from __future__ import annotations

import argparse
import sys
import time
from typing import List, Optional

from code_usage import resolve_provider_usage
from code_usage.formatting import format_json_output, format_terminal_output
from code_usage.processes import DEFAULT_PROGRAMS, count_program_instances, parse_programs
from code_usage.providers.base import ProviderError


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Monitor coding assistant usage limits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                       Show current usage
  %(prog)s --provider auto                       Show the most utilized working provider
  %(prog)s --provider codex --json               Output experimental Codex usage as JSON
  %(prog)s --watch                               Auto-refresh every 2 minutes
  %(prog)s --verbose                             Show detected process information
  %(prog)s --programs claude,codex,opencode      Track specific programs
        """,
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "codex"],
        default="auto",
        help="Provider to query (default: auto)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh every 2 minutes (Ctrl+C to exit)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text",
    )
    parser.add_argument(
        "--programs",
        type=str,
        default=",".join(DEFAULT_PROGRAMS),
        help="Comma-separated list of programs to track",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information including detected processes",
    )
    return parser


def run_once(provider_name: str, json_output: bool, verbose: bool, programs: List[str]) -> int:
    """Fetch and display usage one time."""
    primary, providers = resolve_provider_usage(provider_name)
    program_counts = count_program_instances(programs) if verbose else None

    if json_output:
        print(format_json_output(primary, providers, provider_name, program_counts))
    else:
        print(format_terminal_output(primary, providers, provider_name, program_counts))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Run the terminal CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    programs = parse_programs(args.programs)

    try:
        if args.watch:
            while True:
                clear_screen()
                run_once(args.provider, args.json, args.verbose, programs)
                time.sleep(120)
        return run_once(args.provider, args.json, args.verbose, programs)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 0
    except ProviderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected Error: {exc}", file=sys.stderr)
        return 1
