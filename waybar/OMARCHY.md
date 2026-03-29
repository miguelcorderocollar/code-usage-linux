# Omarchy Integration Guide

Omarchy-specific setup for the combined `custom/code-usage` Waybar module.

## Signal choice

Your current Omarchy Waybar config already uses:
- `8` for `custom/screenrecording-indicator`
- `9` for `custom/idle-indicator`
- `10` for `custom/notification-silencing-indicator`

Use `11` for `custom/code-usage`.

## Omarchy module config

Insert the module after `"group/tray-expander"` in `modules-right` and add:

```jsonc
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
```

## Install commands

```bash
cp -r code_usage ~/.local/bin/code_usage
cp code-usage.py ~/.local/bin/code-usage
cp waybar/code-usage-waybar.py ~/.local/bin/code-usage-waybar
cp claude-usage.py ~/.local/bin/claude-usage
cp waybar/claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/code-usage ~/.local/bin/code-usage-waybar
chmod +x ~/.local/bin/claude-usage ~/.local/bin/claude-usage-waybar
```

## Suggested CSS

```css
#custom-code-usage {
  min-width: 12px;
  margin: 0 8px;
}

#custom-code-usage.ok {
  color: #a6e3a1;
}

#custom-code-usage.warning {
  color: #f9e2af;
}

#custom-code-usage.critical,
#custom-code-usage.error {
  color: #f38ba8;
}
```

## Restart

```bash
omarchy-restart-waybar
```

## Manual refresh

```bash
pkill -SIGRTMIN+11 waybar
```
