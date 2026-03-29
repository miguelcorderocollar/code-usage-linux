# Waybar Integration for Code Usage

This directory contains the combined Waybar helper for provider-neutral usage monitoring.

Primary helper:
- `code-usage-waybar`

Compatibility alias:
- `claude-usage-waybar`

## Module summary

- module id: `custom/code-usage`
- primary command: `~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode`
- refresh signal: `11`
- left click opens the terminal CLI
- right click refreshes via `SIGRTMIN+11`

## Install

```bash
cp code-usage-waybar.py ~/.local/bin/code-usage-waybar
cp claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/code-usage-waybar ~/.local/bin/claude-usage-waybar
```

Make sure `~/.local/bin/code_usage/` is installed alongside the binaries.

## Config snippet

Add the module after `"group/tray-expander"` in `modules-right`:

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

## CSS snippet

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

## Manual test

```bash
~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode
pkill -SIGRTMIN+11 waybar
```

## Notes

- `auto` queries all working providers and renders the highest-utilization one as primary
- idle mode shows only the code icon
- active mode shows the icon and the selected provider percentage
