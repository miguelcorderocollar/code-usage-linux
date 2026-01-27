# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Usage for Linux is a Python-based terminal application for monitoring Claude Code API usage limits. It displays usage statistics in the terminal with color-coded status, progress bars, and time-until-reset information. The project also includes Waybar integration for real-time status bar monitoring on Wayland desktops.

## Core Commands

### Installation
```bash
./install.sh                    # Quick install (copies script, installs dependencies)
pip3 install --user requests>=2.25.0  # Manual dependency install
```

### Running the Application
```bash
claude-usage                    # Show current usage
claude-usage --watch           # Auto-refresh every 2 minutes
claude-usage --json            # Output as JSON for scripting
claude-usage --verbose         # Show detailed process information
claude-usage --programs claude,opencode,cursor --verbose  # Custom program tracking
~/.local/bin/claude-usage-waybar  # Waybar integration script
```

### Development
```bash
# Syntax and import checks
python3 -m py_compile claude-usage.py waybar/claude-usage-waybar.py
python3 -m py_compile *.py waybar/*.py

# Run with verbose error output
python3 claude-usage.py --help 2>&1
```

## Architecture and Code Structure

### Main Components

**claude-usage.py** (Terminal Application)
- **CredentialReader**: Reads Claude Code OAuth credentials from `~/.claude/.credentials.json`. Handles file not found, corruption, and missing fields with user-friendly error messages.
- **UsageAPIClient**: Queries `https://api.anthropic.com/api/oauth/usage` using OAuth Bearer token. Implements exponential backoff retry logic (up to 3 attempts) for network errors.
- **UsageFormatter**: Formats API response data for terminal output. Handles color coding (🟢🟡🔴), progress bars, and human-readable time formatting (e.g., "2h 37m", "4d 12h").
- **count_program_instances()**: Uses `pgrep -x` to detect running instances of specified programs. For opencode, filters by `--port` flag to count only main processes, not helpers.

**waybar/claude-usage-waybar.py** (Waybar Integration)
- Returns JSON output with text, tooltip, and CSS class for styling
- Tracks process status to determine "active" vs "idle" mode
- Responds to Waybar signals for manual refresh

### Key Design Patterns

**Error Handling**: Specific exceptions (FileNotFoundError, ValueError, requests.HTTPError, requests.RequestException) are caught and converted to user-friendly messages. Network errors use exponential backoff (2^attempt seconds).

**Time Formatting**: ISO8601 timestamps (e.g., "2026-01-12T21:22:15Z") are parsed and formatted as human-readable deltas (days/hours/minutes until reset).

**Progress Bars**: Fixed 32-character width using Unicode blocks (█ filled, ░ empty). Calculation: `int(utilization / 100 * 32)`.

**Color Status Mapping**: Green (<70%), Yellow (70-89%), Red (≥90%).

**Process Tracking**: Different filtering logic per program (opencode counts only main instances with `--port`, others count all matches).

## Important Implementation Details

### Credentials and Authentication
- Credentials stored at `~/.claude/.credentials.json`
- Read path: `data['claudeAiOauth']['accessToken']`
- Authentication errors (401) trigger re-authentication prompt
- Token is passed as Bearer token in Authorization header

### API Response Structure
Expected fields from `/api/oauth/usage`:
- `five_hour`: {utilization: float, resets_at: ISO8601}
- `seven_day`: {utilization: float, resets_at: ISO8601}
- `sonnet_only`: {utilization: float, resets_at: ISO8601} (optional)

### Process Tracking
- Uses `pgrep -x` for exact executable name matching (case-sensitive)
- Default programs: claude, opencode
- Opencode filtering: `if '--port' in line` to exclude helper processes
- Timeout: 2 seconds per pgrep call
- No processes found = count 0 for that program

### Waybar Integration
- Module path: `~/.local/bin/claude-usage-waybar`
- Configuration location: `~/.config/waybar/config.jsonc`
- Default signal: 8 (manual refresh via `pkill -SIGRTMIN+8 waybar`)
- Refresh interval: 120 seconds (configurable)
- JSON return format: `{"text": "...", "tooltip": "...", "class": "..."}` where class is "ok", "warning", "critical", or "error"

### Waybar Local Configuration Updates
When modifying the user's local Waybar config:
1. **Always use the Omarchy skill** if available - Load it before making Waybar changes
2. **Edit user config directly** at `~/.config/waybar/config.jsonc`
3. **Restart Waybar** - Run `omarchy-restart-waybar` or `pkill waybar && waybar &`
4. **Never edit** `~/.local/share/omarchy/` - system-managed files

## Code Style Guidelines

### Python Requirements
- Python 3.8+ minimum
- Only external dependency: `requests>=2.25.0`
- Use `typing` module for type hints (Optional, Dict, Any, List, etc.)

### Naming Conventions
- **Classes**: PascalCase (CredentialReader, UsageAPIClient, UsageFormatter)
- **Methods/Functions**: snake_case (read_access_token, format_progress_bar)
- **Constants**: UPPER_CASE (CREDENTIALS_PATH, API_ENDPOINT)
- **CLI Scripts**: snake_case with hyphens (claude-usage, claude-usage-waybar)

### Docstring Format
Use Google-style docstrings with Args, Returns, Raises sections:
```python
def method_name(self, param: Type) -> ReturnType:
    """Short description.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this error occurs
    """
```

### Import Organization
```python
# Standard library
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Third-party
import requests

# Local (if any)
```

### Terminal Output
- Use Colors class constants (Colors.GREEN, Colors.RED, Colors.RESET) instead of hardcoded ANSI codes
- Always reset colors with `Colors.RESET`
- Errors go to stderr: `print(..., file=sys.stderr)`
- Normal output goes to stdout: `print(...)`

## Testing Components

### Test Credential Reader
```bash
python3 -c "
from claude_usage import CredentialReader
reader = CredentialReader()
print('Accessible:', bool(reader.read_access_token()))
"
```

### Test API Client
```bash
python3 -c "
from claude_usage import UsageAPIClient, CredentialReader
client = UsageAPIClient()
token = CredentialReader().read_access_token()
data = client.fetch_usage(token)
print('Keys:', list(data.keys()))
"
```

### Test Process Tracking
```bash
# Check actual running processes
pgrep -l 'claude|opencode'

# Test exact matching
pgrep -x claude
pgrep -x opencode

# Run verbose mode to see detected processes
claude-usage --verbose
claude-usage --programs claude,opencode,cursor --verbose
```

## Deploying Updates to User's System

Once features are implemented and tested, deploy the updates to the user's local system when they request it.

### Updating Terminal Application
```bash
# Copy the updated main script to user's local bin
cp claude-usage.py ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage

# Test the update
claude-usage
claude-usage --help
```

### Updating Waybar Integration (if modified)
```bash
# Copy the updated Waybar script
cp waybar/claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/claude-usage-waybar

# Test the script directly
~/.local/bin/claude-usage-waybar

# Restart Waybar to pick up changes
pkill waybar && waybar &
# OR if using systemd:
systemctl --user restart waybar
# OR if using Omarchy:
omarchy-restart-waybar
```

### Post-Deployment Verification
After deployment, verify the updates are working:

**For terminal application:**
```bash
# Check version is updated (if applicable)
claude-usage --help

# Test basic functionality
claude-usage

# If features added, test new flags
claude-usage --new-flag  # (if applicable)
```

**For Waybar integration:**
```bash
# Check module output
~/.local/bin/claude-usage-waybar

# Verify it appears in status bar and responds to signals
pkill -SIGRTMIN+8 waybar
```

## Key Files and Their Purposes

- `claude-usage.py` - Main terminal application (570 lines)
- `waybar/claude-usage-waybar.py` - Waybar module script (~400 lines)
- `waybar/config.jsonc` - Example Waybar configuration
- `waybar/style.css` - Waybar styling with multiple theme options
- `waybar/OMARCHY.md` - Omarchy-specific integration notes
- `install.sh` - Installation and PATH setup
- `requirements.txt` - Dependency specification
- `README.md` - User-facing documentation
- `AGENTS.md` - Detailed agent guidelines and testing procedures

## Related Documentation

For additional context, see:
- `AGENTS.md` - Comprehensive testing procedures and code style examples
- `waybar/README.md` - Waybar configuration and troubleshooting details
- `waybar/OMARCHY.md` - Omarchy-specific setup for Hyprland users
- `README.md` - Complete usage documentation and feature overview
