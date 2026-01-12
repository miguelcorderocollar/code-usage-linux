#!/usr/bin/env python3
"""
Claude Code Usage Monitor for Linux
Displays Claude Code usage limits in the terminal with color-coded status.
Inspired by the macOS Claude Usage menubar app by @richhickson.
https://github.com/richhickson/claudecodeusage#
"""

import json
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import requests


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class CredentialReader:
    """Reads Claude Code OAuth credentials from Linux config directory"""

    CREDENTIALS_PATH = os.path.expanduser('~/.claude/.credentials.json')

    def read_access_token(self) -> str:
        """
        Read access token from Claude Code credentials file.

        Returns:
            Access token string

        Raises:
            FileNotFoundError: If credentials file doesn't exist
            ValueError: If credentials format is invalid
        """
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise FileNotFoundError(
                "Not logged in to Claude Code.\n"
                "Please run 'claude' in your terminal and complete the login flow."
            )

        try:
            with open(self.CREDENTIALS_PATH, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(
                "Credentials file is corrupted.\n"
                "Please run 'claude' to re-authenticate."
            )

        try:
            access_token = data['claudeAiOauth']['accessToken']
            if not access_token:
                raise KeyError
            return access_token
        except KeyError:
            raise ValueError(
                "Invalid credential format.\n"
                "Please run 'claude' to re-authenticate."
            )


class UsageAPIClient:
    """Client for Anthropic OAuth usage API"""

    API_ENDPOINT = 'https://api.anthropic.com/api/oauth/usage'
    VERSION = '1.0.0'

    def __init__(self, timeout: int = 10):
        """
        Initialize API client.

        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_usage(self, access_token: str, retry_count: int = 3) -> Dict[str, Any]:
        """
        Fetch usage data from Anthropic API.

        Args:
            access_token: OAuth access token
            retry_count: Number of retries for network errors (default: 3)

        Returns:
            Usage data dictionary with five_hour, seven_day, sonnet_only

        Raises:
            requests.HTTPError: If API returns error status
            requests.RequestException: If network request fails
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': f'ClaudeUsageLinux/{self.VERSION}',
            'anthropic-beta': 'oauth-2025-04-20'
        }

        last_error = None
        for attempt in range(retry_count):
            try:
                response = self.session.get(
                    self.API_ENDPOINT,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 401:
                    raise requests.HTTPError(
                        "Authentication expired.\n"
                        "Please run 'claude' to re-authenticate."
                    )

                response.raise_for_status()
                return response.json()

            except requests.Timeout:
                last_error = requests.RequestException(
                    f"Request timed out after {self.timeout} seconds"
                )
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            except requests.ConnectionError as e:
                last_error = e
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

        # If we get here, all retries failed
        if last_error:
            raise last_error

        return {}


def count_program_instances(programs: List[str]) -> Dict[str, int]:
    """Count running instances of multiple programs
    
    Args:
        programs: List of program names to track (e.g., ['claude', 'opencode'])
    
    Returns:
        Dict mapping program name to count (e.g., {'claude': 2, 'opencode': 1})
    """
    counts = {}
    
    for program in programs:
        program = program.strip()
        if not program:
            continue
            
        try:
            # Match the executable name exactly with full command line
            result = subprocess.run(
                ['pgrep', '-x', program, '-a'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                # Get process lines with full command
                output = result.stdout.decode().strip()
                if not output:
                    counts[program] = 0
                    continue
                    
                process_lines = output.split('\n')
                
                # Filter out helper processes for opencode
                # Only count main instances (those with --port flag)
                if program == 'opencode':
                    main_processes = [line for line in process_lines if '--port' in line]
                    counts[program] = len(main_processes)
                else:
                    # For other programs, count all matches
                    counts[program] = len([p for p in process_lines if p])
            else:
                counts[program] = 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            counts[program] = 0
    
    return counts


class UsageFormatter:
    """Formats usage data for terminal output"""

    PROGRESS_BAR_WIDTH = 32

    def get_color(self, utilization: float) -> str:
        """
        Get color code based on utilization percentage.

        Args:
            utilization: Usage percentage (0-100)

        Returns:
            ANSI color code
        """
        if utilization >= 90:
            return Colors.RED
        elif utilization >= 70:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def get_emoji(self, utilization: float) -> str:
        """
        Get status emoji based on utilization percentage.

        Args:
            utilization: Usage percentage (0-100)

        Returns:
            Status emoji
        """
        if utilization >= 90:
            return '🔴'
        elif utilization >= 70:
            return '🟡'
        else:
            return '🟢'

    def format_progress_bar(self, utilization: float) -> str:
        """
        Create progress bar visualization.

        Args:
            utilization: Usage percentage (0-100)

        Returns:
            Progress bar string with filled and empty blocks
        """
        filled = int(utilization / 100 * self.PROGRESS_BAR_WIDTH)
        empty = self.PROGRESS_BAR_WIDTH - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def format_time_remaining(self, reset_time_str: Optional[str]) -> str:
        """
        Format time remaining until reset.

        Args:
            reset_time_str: ISO8601 timestamp string

        Returns:
            Human-readable time string (e.g., "2h 37m" or "4d 12h")
        """
        if not reset_time_str:
            return "unknown"

        try:
            # Parse ISO8601 timestamp
            reset_time = datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = reset_time - now

            if delta.total_seconds() <= 0:
                return "soon"

            total_seconds = int(delta.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            if days > 0:
                return f"{days}d {hours}h"
            else:
                return f"{hours}h {minutes}m"

        except (ValueError, AttributeError):
            return "unknown"

    def format_usage_section(self, title: str, subtitle: str,
                           utilization: float, resets_at: Optional[str]) -> str:
        """
        Format a single usage section with progress bar and time.

        Args:
            title: Section title (e.g., "Session Usage")
            subtitle: Section subtitle (e.g., "5-hour window")
            utilization: Usage percentage (0-100)
            resets_at: ISO8601 reset timestamp

        Returns:
            Formatted section string
        """
        color = self.get_color(utilization)
        emoji = self.get_emoji(utilization)
        percentage = int(utilization)
        progress_bar = self.format_progress_bar(utilization)
        time_remaining = self.format_time_remaining(resets_at)

        return (
            f"{title} ({subtitle})\n"
            f"  {emoji} {color}{percentage}%{Colors.RESET}  {progress_bar}\n"
            f"  {Colors.DIM}Resets in {time_remaining}{Colors.RESET}"
        )

    def format_output(self, usage_data: Dict[str, Any]) -> str:
        """
        Format complete usage output.

        Args:
            usage_data: API response with five_hour, seven_day, sonnet_only

        Returns:
            Complete formatted output string
        """
        sections = []

        # Header
        sections.append(f"{Colors.BOLD}Claude Code Usage Status{Colors.RESET}")
        sections.append("=" * 24)
        sections.append("")

        # Session usage (5-hour window)
        five_hour = usage_data.get('five_hour', {})
        if five_hour:
            sections.append(self.format_usage_section(
                "Session Usage",
                "5-hour window",
                five_hour.get('utilization', 0),
                five_hour.get('resets_at')
            ))
            sections.append("")

        # Weekly usage (7-day window)
        seven_day = usage_data.get('seven_day', {})
        if seven_day:
            sections.append(self.format_usage_section(
                "Weekly Usage",
                "7-day window",
                seven_day.get('utilization', 0),
                seven_day.get('resets_at')
            ))
            sections.append("")

        # Sonnet only (optional)
        sonnet_only = usage_data.get('sonnet_only', {})
        if sonnet_only and sonnet_only.get('utilization') is not None:
            sections.append(self.format_usage_section(
                "Sonnet Only",
                "7-day window",
                sonnet_only.get('utilization', 0),
                sonnet_only.get('resets_at')
            ))
            sections.append("")

        # Footer
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"{Colors.DIM}Last updated: {timestamp}{Colors.RESET}")

        return "\n".join(sections)

    def format_process_info(self, program_counts: Dict[str, int]) -> str:
        """
        Format process detection information (for --verbose mode).
        
        Args:
            program_counts: Dict of program names to instance counts
        
        Returns:
            Formatted string showing detected processes
        """
        sections = []
        sections.append(f"{Colors.BOLD}Active Programs{Colors.RESET}")
        sections.append("-" * 24)
        sections.append("")
        
        total_instances = sum(program_counts.values())
        
        if total_instances == 0:
            sections.append(f"{Colors.DIM}No tracked programs running (idle mode){Colors.RESET}")
        else:
            active_programs = [(name, count) for name, count in program_counts.items() if count > 0]
            for name, count in active_programs:
                instance_word = "instance" if count == 1 else "instances"
                sections.append(f"  {Colors.GREEN}•{Colors.RESET} {name}: {count} {instance_word}")
            
            sections.append("")
            sections.append(f"{Colors.DIM}Total: {total_instances} instance{'s' if total_instances != 1 else ''} running{Colors.RESET}")
        
        return "\n".join(sections)

    def format_json_output(self, usage_data: Dict[str, Any]) -> str:
        """
        Format usage data as JSON.

        Args:
            usage_data: API response

        Returns:
            JSON string
        """
        output = {}

        five_hour = usage_data.get('five_hour', {})
        if five_hour:
            output['session'] = {
                'utilization': int(five_hour.get('utilization', 0)),
                'resets_at': five_hour.get('resets_at')
            }

        seven_day = usage_data.get('seven_day', {})
        if seven_day:
            output['weekly'] = {
                'utilization': int(seven_day.get('utilization', 0)),
                'resets_at': seven_day.get('resets_at')
            }

        sonnet_only = usage_data.get('sonnet_only', {})
        if sonnet_only and sonnet_only.get('utilization') is not None:
            output['sonnet'] = {
                'utilization': int(sonnet_only.get('utilization', 0)),
                'resets_at': sonnet_only.get('resets_at')
            }

        # Determine status based on max utilization
        max_util = max(
            five_hour.get('utilization', 0),
            seven_day.get('utilization', 0),
            sonnet_only.get('utilization', 0) if sonnet_only else 0
        )

        if max_util >= 90:
            output['status'] = 'critical'
        elif max_util >= 70:
            output['status'] = 'warning'
        else:
            output['status'] = 'ok'

        return json.dumps(output, indent=2)


def clear_screen():
    """Clear terminal screen"""
    print('\033[2J\033[H', end='')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Monitor Claude Code usage limits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                Show current usage
  %(prog)s --watch                        Auto-refresh every 2 minutes
  %(prog)s --json                         Output as JSON for scripting
  %(prog)s --verbose                      Show detailed process information
  %(prog)s --programs claude,opencode     Track specific programs
        """
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Auto-refresh every 2 minutes (Ctrl+C to exit)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of formatted text'
    )
    parser.add_argument(
        '--programs',
        type=str,
        default='claude,opencode',
        help='Comma-separated list of programs to track (default: claude,opencode)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information including detected processes'
    )

    args = parser.parse_args()
    
    # Parse programs list
    programs = [p.strip() for p in args.programs.split(',') if p.strip()]
    if not programs:
        programs = ['claude', 'opencode']  # Fallback to defaults

    credential_reader = CredentialReader()
    api_client = UsageAPIClient()
    formatter = UsageFormatter()

    def fetch_and_display():
        """Fetch usage data and display it"""
        try:
            # Read credentials
            access_token = credential_reader.read_access_token()

            # Fetch usage data
            usage_data = api_client.fetch_usage(access_token)

            # Display output
            if args.json:
                print(formatter.format_json_output(usage_data))
            else:
                print(formatter.format_output(usage_data))
                
                # Show process information in verbose mode
                if args.verbose:
                    print()
                    program_counts = count_program_instances(programs)
                    print(formatter.format_process_info(program_counts))

            return True

        except FileNotFoundError as e:
            print(f"{Colors.RED}Error:{Colors.RESET} {e}", file=sys.stderr)
            return False
        except ValueError as e:
            print(f"{Colors.RED}Error:{Colors.RESET} {e}", file=sys.stderr)
            return False
        except requests.HTTPError as e:
            print(f"{Colors.RED}Error:{Colors.RESET} {e}", file=sys.stderr)
            return False
        except requests.RequestException as e:
            print(f"{Colors.RED}Network Error:{Colors.RESET} {e}", file=sys.stderr)
            print("Please check your internet connection and try again.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"{Colors.RED}Unexpected Error:{Colors.RESET} {e}", file=sys.stderr)
            return False

    # Watch mode
    if args.watch:
        if args.json:
            print(f"{Colors.RED}Error:{Colors.RESET} --watch and --json cannot be used together",
                  file=sys.stderr)
            sys.exit(1)

        try:
            while True:
                clear_screen()
                success = fetch_and_display()

                if success:
                    print(f"\n{Colors.DIM}Press Ctrl+C to exit{Colors.RESET}")

                # Sleep for 2 minutes (120 seconds)
                time.sleep(120)

        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}Exiting...{Colors.RESET}")
            sys.exit(0)
    else:
        # One-shot mode
        success = fetch_and_display()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
