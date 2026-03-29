"""CLI application entrypoint."""

from __future__ import annotations

import argparse
import sys
import time
from typing import Dict, Tuple

from code_usage.formatting import (
    build_json_output,
    format_process_info,
    format_terminal_output,
    select_primary_provider,
)
from code_usage.processes import DEFAULT_PROGRAMS, count_program_instances, parse_programs
from code_usage.providers.base import ProviderError, ProviderSnapshot
from code_usage.providers.claude import ClaudeProviderClient
from code_usage.providers.codex import CodexProviderClient


def get_provider_clients() -> Dict[str, object]:
    """Return the supported provider clients."""
    return {
        "claude": ClaudeProviderClient(),
        "codex": CodexProviderClient(),
    }


def collect_provider_results(provider_mode: str) -> Tuple[Dict[str, ProviderSnapshot], Dict[str, str]]:
    """Collect successful provider snapshots and provider errors."""
    clients = get_provider_clients()
    requested = clients.keys() if provider_mode == "auto" else [provider_mode]
    snapshots: Dict[str, ProviderSnapshot] = {}
    errors: Dict[str, str] = {}

    for provider_name in requested:
        client = clients[provider_name]
        if not client.is_configured():
            errors[provider_name] = "not configured"
            continue
        try:
            snapshots[provider_name] = client.fetch_usage()
        except ProviderError as error:
            errors[provider_name] = str(error)

    return snapshots, errors


def build_argument_parser(default_provider: str = "auto") -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Monitor code usage limits across Claude and Codex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                  Auto-select the highest-risk provider
  %(prog)s --provider claude                Show Claude usage only
  %(prog)s --provider codex                 Show Codex usage only
  %(prog)s --watch                          Auto-refresh every 2 minutes
  %(prog)s --json                           Output as JSON for scripting
  %(prog)s --verbose                        Show process tracking details
        """,
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "codex"],
        default=default_provider,
        help="Usage provider to display (default: %(default)s)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-refresh every 2 minutes (Ctrl+C to exit)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
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


def clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def run_cli(default_provider: str = "auto") -> int:
    """Run the CLI application."""
    parser = build_argument_parser(default_provider=default_provider)
    args = parser.parse_args()
    programs = parse_programs(args.programs)

    def fetch_and_display() -> None:
        snapshots, errors = collect_provider_results(args.provider)
        if not snapshots:
            error_messages = [f"{name}: {message}" for name, message in errors.items()]
            raise ProviderError("No provider data available.\n" + "\n".join(error_messages))

        selected_provider = select_primary_provider(snapshots)
        if args.json:
            print(build_json_output(snapshots, selected_provider, errors))
            return

        print(format_terminal_output(snapshots, selected_provider, errors))
        if args.verbose:
            print()
            print(format_process_info(count_program_instances(programs)))

    try:
        if args.watch:
            while True:
                clear_screen()
                fetch_and_display()
                time.sleep(120)
        else:
            fetch_and_display()
        return 0
    except KeyboardInterrupt:
        print("\nExiting...", file=sys.stderr)
        return 0
    except ProviderError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected Error: {error}", file=sys.stderr)
        return 1
