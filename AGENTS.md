# Claude Usage for Linux - Agent Guidelines

This document provides guidelines for agentic coding agents working on the Claude Usage for Linux project.

## Project Overview

Claude Usage for Linux is a Python-based terminal application for monitoring Claude Code API usage limits. It displays usage statistics in the terminal and integrates with Waybar status bars for real-time monitoring.

## Build, Lint, and Test Commands

### Installation and Setup
```bash
# Quick install (copies script and installs dependencies)
./install.sh

# Manual setup
pip3 install --user requests>=2.25.0
cp claude-usage.py ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage
```

### Running the Application
```bash
# Basic usage (show current usage)
claude-usage

# Watch mode (auto-refresh every 2 minutes)
claude-usage --watch

# JSON output for scripting
claude-usage --json

# Waybar integration
~/.local/bin/claude-usage-waybar
```

### Development Commands
```bash
# No formal linting setup - use these manually:
python3 -m py_compile claude-usage.py waybar/claude-usage-waybar.py

# Check imports
python3 -c "import claude-usage; print('Main script imports OK')"
python3 -c "import waybar.claude-usage-waybar; print('Waybar script imports OK')"

# Basic syntax check
python3 -m py_compile *.py waybar/*.py

# Run with verbose error output
python3 claude-usage.py --help 2>&1
```

### Testing Individual Components
```bash
# Test credential reading (requires valid ~/.claude/.credentials.json)
python3 -c "
from claude_usage import CredentialReader
reader = CredentialReader()
print('Credentials accessible:', bool(reader.read_access_token()))
"

# Test API client (requires valid credentials)
python3 -c "
from claude_usage import UsageAPIClient, CredentialReader
client = UsageAPIClient()
reader = CredentialReader()
token = reader.read_access_token()
data = client.fetch_usage(token)
print('API response keys:', list(data.keys()))
"

# Test formatter
python3 -c "
from claude_usage import UsageFormatter
formatter = UsageFormatter()
sample_data = {
    'five_hour': {'utilization': 25.0, 'resets_at': '2026-01-12T00:00:00Z'},
    'seven_day': {'utilization': 10.0, 'resets_at': '2026-01-16T00:00:00Z'}
}
print('Terminal output:')
print(formatter.format_output(sample_data))
print('JSON output:')
print(formatter.format_json_output(sample_data))
"
```

## Code Style Guidelines

### Python Version and Dependencies
- **Python Version**: 3.8+ minimum
- **Dependencies**: 
  - `requests>=2.25.0` (core HTTP library)
- Use `typing` module for type hints
- Avoid external dependencies beyond requests

### File Structure and Organization
```
/
├── claude-usage.py           # Main terminal application
├── waybar/
│   ├── claude-usage-waybar.py # Waybar integration script
│   ├── config.jsonc          # Waybar configuration example
│   └── style.css             # Waybar styling
├── install.sh                # Installation script
├── requirements.txt          # Python dependencies
└── README.md                 # User documentation
```

### Naming Conventions
- **Classes**: PascalCase (`CredentialReader`, `UsageAPIClient`, `UsageFormatter`)
- **Methods**: snake_case (`read_access_token`, `format_progress_bar`)
- **Constants**: UPPER_CASE (`CREDENTIALS_PATH`, `API_ENDPOINT`)
- **Variables**: snake_case (`access_token`, `usage_data`)
- **Modules**: snake_case with hyphens for CLI tools (`claude-usage`, `claude-usage-waybar`)

### Code Structure Patterns

#### Class Organization
```python
class ComponentName:
    """Single-line description of component purpose."""

    # Class constants first
    CONSTANT_NAME = "value"

    def __init__(self, param: Type) -> None:
        """Initialize component.

        Args:
            param: Description of parameter
        """
        self.param = param

    def method_name(self, param: Type) -> ReturnType:
        """Method description.

        Args:
            param: Parameter description

        Returns:
            Description of return value

        Raises:
            ExceptionType: When this error occurs
        """
        pass
```

#### Error Handling
```python
try:
    # Risky operation
    result = risky_function()
except SpecificException as e:
    # Handle specific error with user-friendly message
    print(f"Error: {e}", file=sys.stderr)
    return False
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected Error: {e}", file=sys.stderr)
    return False
```

#### Type Hints
```python
from typing import Optional, Dict, Any, List

def function_name(
    required_param: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """Function with proper type hints."""
    pass
```

### Documentation Standards
- All classes and public methods must have docstrings
- Use Google-style docstrings (Args, Returns, Raises sections)
- Include type hints in function signatures
- Add inline comments for complex logic
- Keep docstrings concise but descriptive

### Terminal Output and Colors
```python
class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
```

- Use color constants instead of hardcoded ANSI codes
- Always reset colors with `Colors.RESET`
- Use `file=sys.stderr` for error messages
- Use `file=sys.stdout` for normal output

### API Integration Guidelines
- Use requests.Session() for connection reuse
- Set appropriate User-Agent and headers
- Implement exponential backoff for retries
- Handle HTTP errors gracefully
- Respect API rate limits

### Configuration and Credentials
- Store credentials in `~/.claude/.credentials.json` (user-specific)
- Never log or expose credentials in output
- Use `os.path.expanduser()` for user directory paths
- Check file existence before reading

### Progress Bars and Formatting
- Use Unicode block characters for progress bars: `█` (filled), `░` (empty)
- Fixed width progress bars (32 characters)
- Include percentage and time remaining in displays
- Format time as "Xh Ym" or "Xd Yh"

### Error Messages
- Provide clear, actionable error messages
- Suggest solutions when possible
- Use consistent error prefixes ("Error:", "Network Error:")
- Exit with appropriate status codes (0 for success, 1 for errors)

### Security Considerations
- Never log authentication tokens
- Use HTTPS for all API calls
- Validate JSON responses before processing
- Handle malformed data gracefully
- Don't store sensitive data in code or version control

### Testing Philosophy
- Test API responses with mock data
- Verify error handling with invalid inputs
- Test color output formatting
- Check JSON serialization/deserialization
- Validate progress bar calculations

### Commit Message Style
```
feat: add support for sonnet usage tracking
fix: handle network timeouts with exponential backoff
docs: update installation instructions for Ubuntu
style: format code with consistent spacing
refactor: extract common formatting logic to base class
```

### File Permissions
- Python scripts should be executable (`chmod +x`)
- Use `#!/usr/bin/env python3` shebang
- Installation scripts should be executable

### Import Organization
```python
# Standard library imports
import json
import os
import sys
from datetime import datetime, timezone

# Third-party imports
import requests

# Local imports (if any)
from . import local_module
```

### Constants and Magic Numbers
- Extract magic numbers to named constants
- Use descriptive constant names
- Group related constants in classes

### Logging and Debug Output
- Use print() for user-facing output
- Use stderr for errors and warnings
- Include timestamps in debug output
- Avoid verbose logging in production code

## Cursor Rules

None found in the repository.

## Copilot Instructions

None found in the repository.