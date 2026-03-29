# Code Usage for Linux

A terminal-based usage monitor for Linux that can read quota windows from multiple coding assistants. It currently supports:

- Claude Code via Anthropic OAuth usage
- Codex via an experimental ChatGPT-auth usage endpoint

The app includes a terminal view and a Waybar module for Omarchy and other Wayland desktops.

## Features

- Provider-neutral CLI: `code-usage`
- Claude-only compatibility alias: `claude-usage`
- Auto provider selection based on highest current utilization
- Color-coded usage windows with progress bars and reset countdowns
- JSON output for scripting
- Waybar integration with combined worst-case status
- Process tracking for `claude`, `codex`, and `opencode`

## Requirements

- Linux
- Python 3.8+
- `requests>=2.25.0`
- For Claude support: Claude Code CLI login
- For Codex support: Codex CLI login

## Installation

### Quick install

```bash
chmod +x install.sh
./install.sh
```

This installs the app bundle to `~/.local/share/code-usage` and installs command wrappers to `~/.local/bin`.

### Manual install

```bash
pip3 install --user requests
mkdir -p ~/.local/share/code-usage ~/.local/bin
cp -R code_usage ~/.local/share/code-usage/code_usage
cp code-usage.py ~/.local/share/code-usage/code-usage.py
cp claude-usage.py ~/.local/share/code-usage/claude-usage.py
cp waybar/code-usage-waybar.py ~/.local/share/code-usage/waybar/code-usage-waybar.py
cp waybar/claude-usage-waybar.py ~/.local/share/code-usage/waybar/claude-usage-waybar.py
chmod +x ~/.local/share/code-usage/code-usage.py ~/.local/share/code-usage/claude-usage.py
chmod +x ~/.local/share/code-usage/waybar/code-usage-waybar.py ~/.local/share/code-usage/waybar/claude-usage-waybar.py
```

## Usage

### Auto-select provider

```bash
code-usage
```

### Force one provider

```bash
code-usage --provider claude
code-usage --provider codex
```

### JSON output

```bash
code-usage --json
```

### Verbose mode

```bash
code-usage --verbose
```

### Compatibility alias

```bash
claude-usage
```

## How it works

### Claude

Reads `~/.claude/.credentials.json` and queries `https://api.anthropic.com/api/oauth/usage`.

### Codex

Reads `~/.codex/auth.json` and queries `https://chatgpt.com/backend-api/wham/usage`.

Important: Codex support is experimental and depends on an undocumented endpoint. It may break without notice.

## Waybar

See [waybar/README.md](waybar/README.md) for setup instructions, including Omarchy-specific configuration.

## Troubleshooting

### Claude not configured

```bash
claude
```

### Codex not configured

```bash
codex login
```

### Network or auth failure

Retry the provider login flow. For Codex, the app will attempt token refresh automatically once before failing.
