# Omarchy Integration Guide

Configuration guide for integrating Code Usage with Omarchy's Waybar setup.

## Important: signal choice

Your current config already uses:

- `custom/screenrecording-indicator` with `signal: 8`
- `custom/idle-indicator` with `signal: 9`
- `custom/notification-silencing-indicator` with `signal: 10`

Use `signal: 11` for `custom/code-usage`.

## Omarchy-optimized configuration

Add this module:

```jsonc
"custom/code-usage": {
  "exec": "~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode",
  "return-type": "json",
  "interval": 120,
  "signal": 11,
  "format": "{text}",
  "on-click": "sh -c 'touch /tmp/code-usage-waybar.loading; pkill -SIGRTMIN+11 waybar; sleep 0.35; pkill -SIGRTMIN+11 waybar; sleep 0.8; pkill -SIGRTMIN+11 waybar'",
  "on-click-right": "pkill -SIGRTMIN+11 waybar",
  "tooltip": true,
  "max-length": 25
}
```

If you only care about Codex right now, use this instead:

```jsonc
"custom/code-usage": {
  "exec": "~/.local/bin/code-usage-waybar --provider codex --programs codex",
  "return-type": "json",
  "interval": 120,
  "signal": 11,
  "format": "{text}",
  "on-click": "sh -c 'touch /tmp/code-usage-waybar.loading; pkill -SIGRTMIN+11 waybar; sleep 0.35; pkill -SIGRTMIN+11 waybar; sleep 0.8; pkill -SIGRTMIN+11 waybar'",
  "on-click-right": "pkill -SIGRTMIN+11 waybar",
  "tooltip": true,
  "max-length": 25
}
```

### Why these settings

1. `signal: 11` avoids conflicts with your existing Omarchy indicators
2. Left click does an in-place refresh with a temporary loading indicator
3. You can lock the module to one provider if you only care about one service

## Suggested module position

Place it in `modules-right` after `"group/tray-expander"`:

```jsonc
"modules-right": [
  "group/tray-expander",
  "custom/code-usage",
  "bluetooth",
  "network",
  "custom/pia-vpn",
  "pulseaudio",
  "cpu",
  "battery"
]
```

## Installation for Omarchy

### 1. Install the app

From the project directory:

```bash
./install.sh
```

This is the preferred install path because the command wrappers depend on the shared `code_usage` package installed under `~/.local/bin/code_usage`.

### 2. Update Waybar config

Edit:

- `~/.config/waybar/config.jsonc`
- `~/.config/waybar/style.css`

Do not edit files under `~/.local/share/omarchy/`.

### 3. Add CSS styling

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

#custom-code-usage.loading {
  color: #89b4fa;
}

#custom-code-usage.idle {
  opacity: 0.65;
}
```

### 4. Restart Waybar

```bash
omarchy-restart-waybar
```

## Manual refresh

```bash
pkill -SIGRTMIN+11 waybar
```

## Manual test

```bash
~/.local/bin/code-usage-waybar --provider auto
~/.local/bin/code-usage --provider auto
```

Codex-only:

```bash
~/.local/bin/code-usage-waybar --provider codex --programs codex
~/.local/bin/code-usage --provider codex
```

## Troubleshooting

### Module not showing

1. Check the wrappers exist:

```bash
ls -l ~/.local/bin/code-usage ~/.local/bin/code-usage-waybar
```

2. Test the Waybar script manually:

```bash
~/.local/bin/code-usage-waybar --provider auto
```

3. Check Waybar logs:

```bash
journalctl --user -u waybar -f
```

### Signal not working

Check signal usage in your config:

```bash
grep -o 'signal[^,]*' ~/.config/waybar/config.jsonc
```

Then trigger the configured signal:

```bash
pkill -SIGRTMIN+11 waybar
```
