# Code Usage for Linux

Terminal and Waybar usage monitor for Linux with provider-neutral commands and experimental multi-provider support.

The project now exposes:
- `code-usage`
- `code-usage-waybar`

Backward-compatible aliases remain available:
- `claude-usage`
- `claude-usage-waybar`

The current GitHub repository is still named `claude-usage-linux`, but the product and command surface have been generalized to **Code Usage for Linux**. The intended repo target name is `code-usage-linux`.

## Features

- Provider-neutral CLI and Waybar integration
- Claude usage support via Anthropic OAuth
- Experimental Codex usage support via ChatGPT-auth state
- `--provider auto|claude|codex`
- Auto-selection of the highest-utilization working provider
- Terminal progress bars and reset timers
- JSON output for scripting
- Process tracking for `claude`, `codex`, and `opencode`
- Compatibility aliases for existing Claude-specific installs

## Requirements

- Linux
- Python 3.8+
- `requests>=2.25.0`
- Claude Code login for Claude provider support
- Codex login for experimental Codex provider support

## Install

### Quick install

```bash
chmod +x install.sh
./install.sh
```

This installs:
- `~/.local/bin/code-usage`
- `~/.local/bin/code-usage-waybar`
- `~/.local/bin/claude-usage`
- `~/.local/bin/claude-usage-waybar`
- `~/.local/bin/code_usage/`

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

## Usage

### Auto-select the most constrained working provider

```bash
code-usage --provider auto
```

### Claude only

```bash
code-usage --provider claude
```

### Experimental Codex only

```bash
code-usage --provider codex
```

### JSON output

```bash
code-usage --provider auto --json
```

Example shape:

```json
{
  "provider": "codex",
  "provider_display_name": "Codex",
  "selection_mode": "auto",
  "status": "ok",
  "max_utilization": 25,
  "providers": {
    "codex": {
      "plan_type": "plus",
      "experimental": true,
      "windows": []
    }
  }
}
```

### Watch mode

```bash
code-usage --watch
```

### Verbose mode with process tracking

```bash
code-usage --verbose
code-usage --programs claude,codex,opencode --verbose
```

## Provider behavior

### Claude

Claude support reads `~/.claude/.credentials.json` and queries:

```text
https://api.anthropic.com/api/oauth/usage
```

### Codex

Experimental Codex support reads `~/.codex/auth.json` and queries:

```text
https://chatgpt.com/backend-api/wham/usage
```

If needed, it refreshes tokens through:

```text
https://auth.openai.com/oauth/token
```

Normalized Codex windows include:
- session window
- weekly window
- optional code review window
- plan type

Codex support is marked experimental because it depends on ChatGPT web quota data and an internal auth flow that may change.

## Default process tracking

The default tracked programs are:

```text
claude,codex,opencode
```

Override them with:

```bash
code-usage --programs claude,cursor
```

## Waybar

See [waybar/README.md](waybar/README.md) for the combined Waybar module and [waybar/OMARCHY.md](waybar/OMARCHY.md) for Omarchy-specific setup.

## Validation commands

```bash
python3 -m py_compile code-usage.py waybar/code-usage-waybar.py
python3 -m py_compile code_usage/*.py code_usage/providers/*.py
python3 code-usage.py --provider claude --json
python3 code-usage.py --provider codex --json
python3 waybar/code-usage-waybar.py --provider auto
```

## Compatibility

The old command names still work as wrappers:

```bash
claude-usage
claude-usage-waybar
```

## Troubleshooting

### Claude authentication

```bash
claude
```

### Codex authentication

```bash
codex
```

### PATH issues

```bash
echo "$PATH" | grep "$HOME/.local/bin"
```

## Privacy

- credentials stay on your machine
- no analytics or telemetry are added here
- network requests go directly to provider backends
