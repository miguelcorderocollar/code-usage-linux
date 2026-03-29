# Waybar Integration for Code Usage

This directory contains everything needed to integrate provider-neutral usage monitoring into Waybar.

Primary helper:

- `code-usage-waybar`

Compatibility alias:

- `claude-usage-waybar`

> Using Omarchy? See [OMARCHY.md](OMARCHY.md) for Omarchy-specific configuration and the signal choice already validated against your current config.

## Features

- Real-time monitoring in Waybar
- Combined provider view with worst-case provider selection
- Rich tooltip with provider windows, plan type, and active processes
- Auto-refresh every 2 minutes by default
- Manual refresh via signal
- Click action to open the terminal view

## Installation

### 1. Install the app

Recommended:

```bash
./install.sh
```

This installs the required shared package plus the `code-usage-waybar` and `claude-usage-waybar` wrappers.

### 2. Configure Waybar

Add the module to your `~/.config/waybar/config.jsonc`:

```jsonc
{
  "modules-right": [
    "group/tray-expander",
    "custom/code-usage",
    "bluetooth",
    "network",
    "custom/pia-vpn",
    "pulseaudio",
    "cpu",
    "battery"
  ],

  "custom/code-usage": {
    "exec": "~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode",
    "return-type": "json",
    "interval": 120,
    "signal": 11,
    "format": "{text}",
    "on-click": "xdg-terminal-exec --app-id=org.omarchy.code-usage -e bash -lc 'code-usage --provider auto; echo; echo Press Enter to close; read'",
    "on-click-right": "pkill -SIGRTMIN+11 waybar",
    "tooltip": true,
    "max-length": 25
  }
}
```

### 3. Add CSS styling

Add this to `~/.config/waybar/style.css`:

```css
#custom-code-usage {
  min-width: 12px;
  margin: 0 8px;
}

#custom-code-usage.usage-0 {
  color: #a6e3a1;
}

#custom-code-usage.usage-50 {
  color: #94e2d5;
}

#custom-code-usage.usage-70 {
  color: #f9e2af;
}

#custom-code-usage.usage-85 {
  color: #fab387;
}

#custom-code-usage.usage-95,
#custom-code-usage.error {
  color: #f38ba8;
}

#custom-code-usage.idle {
  opacity: 0.65;
}
```

### 4. Restart Waybar

```bash
pkill waybar && waybar &
```

Or if you use Omarchy:

```bash
omarchy-restart-waybar
```

## Configuration options

### Provider selection

Default combined mode:

```jsonc
"exec": "~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode"
```

Force Claude only:

```jsonc
"exec": "~/.local/bin/code-usage-waybar --provider claude"
```

Force Codex only:

```jsonc
"exec": "~/.local/bin/code-usage-waybar --provider codex"
```

Codex-only setup with Codex-only process tracking:

```jsonc
"exec": "~/.local/bin/code-usage-waybar --provider codex --programs codex"
```

Compatibility alias:

```jsonc
"exec": "~/.local/bin/claude-usage-waybar"
```

### Tracking multiple programs

Customize tracked programs:

```jsonc
"exec": "~/.local/bin/code-usage-waybar --programs codex",
"exec": "~/.local/bin/code-usage-waybar --programs claude,codex,opencode",
"exec": "~/.local/bin/code-usage-waybar --programs claude,cursor"
```

The tooltip shows active tracked programs and instance counts.

Recommended combinations:

- `--provider auto --programs claude,codex,opencode` for mixed setups
- `--provider codex --programs codex` if you only care about Codex
- `--provider claude --programs claude` if you only care about Claude

### Refresh interval

```jsonc
"interval": 60,
"interval": 120,
"interval": 300
```

### Manual refresh

```bash
pkill -SIGRTMIN+11 waybar
```

## Troubleshooting

### Module not appearing

1. Check the installed wrapper:

```bash
ls -l ~/.local/bin/code-usage-waybar
```

2. Test it manually:

```bash
~/.local/bin/code-usage-waybar --provider auto
```

3. Check Waybar logs:

```bash
journalctl --user -u waybar -f
```

### Module not updating

1. Verify `interval` is numeric
2. Verify the signal number matches your config
3. Trigger a refresh manually:

```bash
pkill -SIGRTMIN+11 waybar
```
