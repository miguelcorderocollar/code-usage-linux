# Code Usage for Linux

A terminal-based usage monitor for Linux that displays quota windows, reset timers, and process activity for supported coding assistants.

It currently supports:

- Claude Code via Anthropic OAuth usage
- Codex via an experimental ChatGPT-auth usage endpoint

The project now exposes provider-neutral commands:

- `code-usage`
- `code-usage-waybar`

Backward-compatible aliases remain available:

- `claude-usage`
- `claude-usage-waybar`

The GitHub repository is still named `claude-usage-linux`, but the product and command surface have been generalized to **Code Usage for Linux**.

Inspired by the [macOS Claude Usage menubar app](https://github.com/richhickson/claudecodeusage#) by [@richhickson](https://x.com/richhickson).

## Features

- Color-coded status: green (OK), yellow (>70%), red (>90%)
- Session and weekly limits
- Progress bars in terminal output
- Human-readable reset countdowns like `2h 37m` and `4d 12h`
- Watch mode with 2-minute refreshes
- JSON output for scripting and automation
- Waybar integration for Wayland desktops
- Provider selection with `--provider auto|claude|codex`
- Auto-selection of the highest-utilization working provider
- Process tracking for `claude`, `codex`, and `opencode`
- Compatibility aliases for previous Claude-specific installs

## Requirements

- Linux
- Python 3.8+
- `requests>=2.25.0`
- Claude Code login for Claude support
- Codex login for experimental Codex support

## Installation

### Quick install

```bash
chmod +x install.sh
./install.sh
```

The install script will:

1. Check your Python version
2. Install the `requests` dependency
3. Install the shared `code_usage/` package to `~/.local/bin/code_usage`
4. Install the command wrappers to `~/.local/bin`
5. Add `~/.local/bin` to your shell PATH if needed

Installed commands:

- `code-usage`
- `code-usage-waybar`
- `claude-usage`
- `claude-usage-waybar`

### Manual install

```bash
pip3 install --user 'requests>=2.25.0'
mkdir -p ~/.local/bin
cp -r code_usage ~/.local/bin/code_usage
cp code-usage.py ~/.local/bin/code-usage
cp waybar/code-usage-waybar.py ~/.local/bin/code-usage-waybar
cp claude-usage.py ~/.local/bin/claude-usage
cp waybar/claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/code-usage ~/.local/bin/code-usage-waybar
chmod +x ~/.local/bin/claude-usage ~/.local/bin/claude-usage-waybar
```

## Waybar integration

For Wayland users with Waybar, there is a dedicated module for real-time monitoring in the status bar. See [waybar/README.md](waybar/README.md) for general setup and [waybar/OMARCHY.md](waybar/OMARCHY.md) for Omarchy-specific configuration.

## Usage

### Basic usage

Auto-select the highest-utilization working provider:

```bash
code-usage
```

Force a specific provider:

```bash
code-usage --provider claude
code-usage --provider codex
```

Compatibility alias:

```bash
claude-usage
```

### Watch mode

Auto-refresh every 2 minutes:

```bash
code-usage --watch
```

### JSON output

```bash
code-usage --json
```

Example JSON output:

```json
{
  "provider": "codex",
  "provider_display_name": "Codex",
  "selection_mode": "auto",
  "status": "ok",
  "max_utilization": 27,
  "providers": {
    "codex": {
      "plan_type": "plus",
      "experimental": true,
      "windows": []
    }
  }
}
```

### Verbose mode

Show detailed information including detected processes:

```bash
code-usage --verbose
code-usage --programs claude,codex,opencode --verbose
```

### Help

```bash
code-usage --help
```

## Prerequisites

### Claude

If you want Claude support, install and log in to Claude Code:

```bash
claude
```

### Codex

If you want Codex support, log in to Codex:

```bash
codex login
```

## How it works

### Claude provider

The Claude provider reads `~/.claude/.credentials.json` and queries:

```text
https://api.anthropic.com/api/oauth/usage
```

Normalized windows:

- session (`five_hour`)
- weekly (`seven_day`)
- optional sonnet-only weekly window

### Codex provider

The Codex provider reads `~/.codex/auth.json` and queries:

```text
https://chatgpt.com/backend-api/wham/usage
```

If needed, it attempts token refresh through:

```text
https://auth.openai.com/oauth/token
```

Normalized windows:

- session
- weekly
- optional code review weekly window
- plan type

Important: Codex support is experimental because it depends on an undocumented endpoint and auth flow that may change without notice.

## Color coding

| Status | Color | Percentage |
|--------|-------|------------|
| 🟢 Normal | Green | < 70% |
| 🟡 Warning | Yellow | 70-89% |
| 🔴 Critical | Red | ≥ 90% |

## Process tracking

By default, the app tracks:

```text
claude,codex,opencode
```

Customize tracked programs:

```bash
code-usage --programs codex --verbose
code-usage --programs claude,codex,opencode --verbose
code-usage --programs claude,cursor --verbose
code-usage --programs my-ai-tool,another-tool --verbose
```

## Troubleshooting

### "Not logged in" or auth errors

Claude:

```bash
claude
```

Codex:

```bash
codex login
```

### Claude authentication expired

Re-run:

```bash
claude
```

### Codex authentication expired

Re-run:

```bash
codex login
```

### Network or rate-limit errors

- Check your internet connection
- Retry after provider-side rate limiting clears
- For Codex, remember the endpoint is experimental and may temporarily break

### Command not found

Make sure `~/.local/bin` is in your PATH:

```bash
echo "$PATH" | grep "$HOME/.local/bin"
```

If not:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Privacy

- Credentials stay on your machine
- No analytics or telemetry are added here
- Requests go directly to provider backends
- The code is open source and inspectable

## Compatibility

The old command names still work as wrappers:

```bash
claude-usage
claude-usage-waybar
```
