# Claude Usage for Linux

A terminal-based Claude Code usage monitor for Linux. Displays your Claude Code usage limits with color-coded status, progress bars, and time-until-reset information directly in your terminal.

Inspired by the [macOS Claude Usage menubar app](https://github.com/richhickson/claudecodeusage#) by [@richhickson](https://x.com/richhickson).

## Features

- **Color-coded status** - Green (OK), Yellow (>70%), Red (>90%)
- **Session & Weekly limits** - Shows both 5-hour and 7-day usage windows
- **Progress bars** - Visual representation of usage levels
- **Time until reset** - Human-readable countdown (e.g., "2h 37m" or "4d 12h")
- **Watch mode** - Auto-refresh every 2 minutes (matching macOS app)
- **JSON output** - For scripting and automation
- **Waybar integration** - Status bar module for Wayland desktops
- **Lightweight** - Single Python script, minimal dependencies

## Requirements

- **Linux** - Any modern distribution
- **Python 3.8+** - Usually pre-installed
- **Claude Code CLI** - Must be installed and logged in
- **requests library** - Installed automatically by install script

## Installation

### Quick Install

```bash
chmod +x install.sh
./install.sh
```

The install script will:
1. Check Python version (requires 3.8+)
2. Install the `requests` library
3. Copy `claude-usage` to `~/.local/bin`
4. Update your PATH if needed

### Manual Install

```bash
# Install dependencies
pip3 install --user requests

# Copy script to local bin
cp claude-usage.py ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Waybar Integration

For Wayland users with Waybar status bar, there's a dedicated module for real-time monitoring in your status bar. See [waybar/README.md](waybar/README.md) for installation and configuration instructions.

## Usage

### Basic Usage

Show current usage:
```bash
claude-usage
```

Example output:
```
Claude Code Usage Status
========================

Session Usage (5-hour window)
  🟢 23%  [████████░░░░░░░░░░░░░░░░░░░░░░░░]
  Resets in 2h 37m

Weekly Usage (7-day window)
  🟢 15%  [█████░░░░░░░░░░░░░░░░░░░░░░░░░░░]
  Resets in 4d 12h

Last updated: 2026-01-11 18:45:32
```

### Watch Mode

Auto-refresh every 2 minutes (press Ctrl+C to exit):
```bash
claude-usage --watch
```

### JSON Output

For scripting and automation:
```bash
claude-usage --json
```

Example JSON output:
```json
{
  "session": {
    "utilization": 23,
    "resets_at": "2026-01-11T21:22:15Z"
  },
  "weekly": {
    "utilization": 15,
    "resets_at": "2026-01-16T06:45:00Z"
  },
  "status": "ok"
}
```

### Help

Show all options:
```bash
claude-usage --help
```

## Prerequisites

Before using Claude Usage, you must be logged in to Claude Code:

```bash
# Install Claude Code if you haven't already
npm install -g @anthropic-ai/claude-code

# Log in
claude
```

## How It Works

Claude Usage reads your Claude Code OAuth credentials from `~/.claude/.credentials.json` and queries the Anthropic usage API at `https://api.anthropic.com/api/oauth/usage`.

**Note:** This uses an undocumented API that could change at any time. The script will gracefully handle API changes but may stop working if Anthropic modifies the endpoint.

## Color Coding

| Status | Color | Percentage |
|--------|-------|------------|
| 🟢 Normal | Green | < 70% |
| 🟡 Warning | Yellow | 70-89% |
| 🔴 Critical | Red | ≥ 90% |

## Troubleshooting

### "Not logged in to Claude Code"

You need to authenticate with Claude Code first:
```bash
claude
```

Complete the login flow in your browser, then try running `claude-usage` again.

### "Credentials file is corrupted"

Your credentials file may be damaged. Re-authenticate:
```bash
claude
```

### "Authentication expired"

Your session has expired. Log in again:
```bash
claude
```

### "Network Error"

Check your internet connection. The script automatically retries up to 3 times with exponential backoff.

### Command not found

Make sure `~/.local/bin` is in your PATH:
```bash
echo $PATH | grep "$HOME/.local/bin"
```

If not, add it:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Differences from macOS App

| Feature | macOS App | Linux Script |
|---------|-----------|--------------|
| UI | Menubar dropdown | Terminal output |
| Launch | Menubar icon | Manual/alias |
| Auto-start | Launch at login | Cron/systemd (manual) |
| Refresh | Auto (2 min) | Watch mode (--watch) |
| Notifications | System | Terminal only |

## Privacy

- Your credentials never leave your machine
- No analytics or telemetry
- No data sent anywhere except Anthropic's API
- Open source - verify the code yourself

## Advanced Usage

### Shell Alias

Add to your `.bashrc` or `.zshrc`:
```bash
alias cu='claude-usage'
alias cuw='claude-usage --watch'
```

### Cron Job

Check usage every hour (saves to log):
```bash
# Add to crontab (crontab -e)
0 * * * * /home/yourusername/.local/bin/claude-usage >> ~/.claude-usage.log 2>&1
```

### systemd User Service

Create `~/.config/systemd/user/claude-usage.service`:
```ini
[Unit]
Description=Claude Usage Monitor
After=network.target

[Service]
Type=simple
ExecStart=/home/yourusername/.local/bin/claude-usage --watch
Restart=on-failure
RestartSec=60

[Install]
WantedBy=default.target
```

Enable and start:
```bash
systemd --user enable claude-usage
systemd --user start claude-usage
```

## License

MIT License.

## Credits

This project was inspired by [@richhickson](https://x.com/richhickson)'s [macOS Claude Usage menubar app](https://github.com/richhickson/claudecodeusage#).

Special thanks to [DHH](https://world.hey.com/dhh) (David Heinemeier Hansson) for creating [Omarchy](https://github.com/basecamp/omarchy).

## Disclaimer

This is an unofficial tool not affiliated with Anthropic. It uses an undocumented API that may change without notice.
