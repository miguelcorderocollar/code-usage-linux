#!/usr/bin/env python3
"""
Waybar Module for Claude Code Usage
Outputs JSON formatted data for Waybar custom module integration.

Displays code icon + current usage percentage at all times

Tooltip shows usage stats and "Last checked: X time ago"

Inspired by the macOS Claude Usage menubar app by @richhickson.
https://github.com/richhickson/claudecodeusage#
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import requests


class CredentialReader:
    """Reads Claude Code OAuth credentials"""
    CREDENTIALS_PATH = os.path.expanduser('~/.claude/.credentials.json')

    def read_access_token(self) -> str:
        if not os.path.exists(self.CREDENTIALS_PATH):
            raise FileNotFoundError("Not logged in")

        with open(self.CREDENTIALS_PATH, 'r') as f:
            data = json.load(f)

        return data['claudeAiOauth']['accessToken']


class UsageAPIClient:
    """Client for Anthropic OAuth usage API"""
    API_ENDPOINT = 'https://api.anthropic.com/api/oauth/usage'

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_usage(self, access_token: str) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'anthropic-beta': 'oauth-2025-04-20'
        }

        response = requests.get(
            self.API_ENDPOINT,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


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


def is_any_program_running(program_counts: Dict[str, int]) -> bool:
    """Check if any tracked program is running
    
    Args:
        program_counts: Dict of program names to instance counts
    
    Returns:
        True if at least one program has instances running
    """
    return any(count > 0 for count in program_counts.values())


class UsageStateTracker:
    """Tracks usage state to determine display mode"""
    STATE_FILE = os.path.expanduser('~/.cache/claude-usage-state.json')
    ACTIVE_THRESHOLD = 600  # 10 minutes in seconds

    def __init__(self):
        os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """Load previous state from cache"""
        if not os.path.exists(self.STATE_FILE):
            return {}

        try:
            with open(self.STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_state(self, utilization: int):
        """Save current state to cache"""
        state = {
            'utilization': utilization,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'last_check': datetime.now(timezone.utc).isoformat()
        }
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(state, f)
        except:
            pass  # Fail silently if can't write cache

    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check timestamp"""
        state = self.load_state()
        if not state:
            return None

        last_check_str = state.get('last_check')
        if not last_check_str:
            return None

        try:
            return datetime.fromisoformat(last_check_str)
        except:
            return None

    def is_active_mode(self, programs: List[str]) -> bool:
        """
        Determine if we should show active mode (with percentage).
        Returns True if any tracked program instance is running, False otherwise.
        
        Args:
            programs: List of program names to check
        
        Returns:
            True if any program is running
        """
        program_counts = count_program_instances(programs)
        return is_any_program_running(program_counts)


def format_time_remaining(reset_time_str: Optional[str]) -> str:
    """Format time remaining until reset"""
    if not reset_time_str:
        return "unknown"

    try:
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


def format_time_ago(check_time: Optional[datetime]) -> str:
    """Format how long ago the check was performed"""
    if not check_time:
        return "unknown"

    try:
        now = datetime.now(timezone.utc)
        delta = now - check_time
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours}h ago"
        else:
            days = total_seconds // 86400
            return f"{days}d ago"
    except:
        return "unknown"


def format_timestamp(check_time: Optional[datetime]) -> str:
    """Format timestamp in human-readable format"""
    if not check_time:
        return "unknown"

    try:
        # Format as "2025-01-11 14:30:45"
        return check_time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "unknown"


def get_emoji(utilization: float) -> str:
    """Get status icon based on utilization"""
    return '\uf121'


def get_css_class(utilization: float) -> str:
    """Get CSS class based on utilization"""
    if utilization >= 90:
        return 'critical'
    elif utilization >= 70:
        return 'warning'
    else:
        return 'ok'


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Waybar module for Claude Code usage monitoring'
    )
    parser.add_argument(
        '--programs',
        type=str,
        default='claude,opencode',
        help='Comma-separated list of programs to track (default: claude,opencode)'
    )
    return parser.parse_args()


def main():
    """Main entry point for Waybar module"""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Parse programs list
        programs = [p.strip() for p in args.programs.split(',') if p.strip()]
        if not programs:
            programs = ['claude', 'opencode']  # Fallback to defaults
        
        # Read credentials and fetch usage
        credential_reader = CredentialReader()
        api_client = UsageAPIClient()
        state_tracker = UsageStateTracker()

        access_token = credential_reader.read_access_token()
        usage_data = api_client.fetch_usage(access_token)

        # Extract data
        five_hour = usage_data.get('five_hour', {})
        seven_day = usage_data.get('seven_day', {})
        sonnet_only = usage_data.get('sonnet_only', {})

        session_util = five_hour.get('utilization', 0)
        weekly_util = seven_day.get('utilization', 0)
        sonnet_util = sonnet_only.get('utilization', 0) if sonnet_only else 0

        session_reset = format_time_remaining(five_hour.get('resets_at'))
        weekly_reset = format_time_remaining(seven_day.get('resets_at'))

        # Determine status based on max utilization
        max_util = max(session_util, weekly_util, sonnet_util)
        emoji = get_emoji(max_util)
        css_class = get_css_class(max_util)

        # Determine display mode and count instances
        program_counts = count_program_instances(programs)
        is_active = is_any_program_running(program_counts)
        total_instances = sum(program_counts.values())

        # Save current state
        state_tracker.save_state(int(session_util))

        # Format text: icon + percentage only when active, just icon when idle
        if is_active:
            text = f"{emoji} ({int(session_util)}%)"
        else:
            text = f"{emoji} "

        # Format tooltip (always detailed)
        tooltip_lines = [
            f"Claude Code Usage",
            f"",
            f"Session (5h): {int(session_util)}%",
            f"  Resets in {session_reset}",
            f"",
            f"Weekly (7d): {int(weekly_util)}%",
            f"  Resets in {weekly_reset}"
        ]

        if sonnet_only and sonnet_util > 0:
            sonnet_reset = format_time_remaining(sonnet_only.get('resets_at'))
            tooltip_lines.extend([
                f"",
                f"Sonnet Only: {int(sonnet_util)}%",
                f"  Resets in {sonnet_reset}"
            ])

        # Add mode indicator and program details to tooltip
        mode_text = "Active coding" if is_active else "Idle"
        
        if is_active:
            # Build detailed instance text showing which programs are running
            active_programs = [f"{name} ({count})" for name, count in program_counts.items() if count > 0]
            instance_text = f"Tracked: {', '.join(active_programs)}"
        else:
            instance_text = "(no instances)"
        
        tooltip_lines.append(f"\nMode: {mode_text} {instance_text}")

        tooltip = "\n".join(tooltip_lines)

        # Output JSON for Waybar
        output = {
            "text": text,
            "tooltip": tooltip,
            "class": css_class,
            "percentage": int(max_util),
            "alt": "active" if is_active else "idle"  # Can be used for CSS styling
        }

        print(json.dumps(output))
        sys.exit(0)

    except FileNotFoundError:
        # Not logged in - show key icon
        output = {
            "text": "\uf084",
            "tooltip": "Not logged in to Claude Code\nRun: claude",
            "class": "no-credentials"
        }
        print(json.dumps(output))
        sys.exit(0)

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            output = {
                "text": "\uf071",
                "tooltip": "Authentication expired\nRun: claude",
                "class": "error"
            }
        else:
            output = {
                "text": "\uf071",
                "tooltip": f"API Error: {e.response.status_code}",
                "class": "error"
            }
        print(json.dumps(output))
        sys.exit(0)

    except requests.RequestException:
        # Network error
        output = {
            "text": "\uf071",
            "tooltip": "Network error\nCheck connection",
            "class": "error"
        }
        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # Unknown error
        output = {
            "text": "\uf071",
            "tooltip": f"Error: {str(e)}",
            "class": "error"
        }
        print(json.dumps(output))
        sys.exit(0)


if __name__ == '__main__':
    main()
