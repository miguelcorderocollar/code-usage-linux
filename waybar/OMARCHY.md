# Omarchy Integration Guide

This project does not ship an Omarchy-managed config. Update your user Waybar files only:

- `~/.config/waybar/config.jsonc`
- `~/.config/waybar/style.css`

Do not edit files under `~/.local/share/omarchy/`.

## Recommended Omarchy module

Use signal `11`. Your current config already uses `7`, `8`, `9`, and `10`.

```jsonc
"custom/code-usage": {
  "exec": "~/.local/bin/code-usage-waybar --provider auto --programs claude,codex,opencode",
  "return-type": "json",
  "interval": 120,
  "signal": 11,
  "format": "{text}",
  "on-click": "xdg-terminal-exec --app-id=org.omarchy.code-usage -e bash -c 'code-usage --provider auto; echo; echo Press Enter to close; read'",
  "on-click-right": "pkill -SIGRTMIN+11 waybar",
  "tooltip": true,
  "max-length": 25
}
```

## Suggested placement

Insert `"custom/code-usage"` in `modules-right` immediately after `"group/tray-expander"`.

## CSS

```css
#custom-code-usage {
  min-width: 12px;
  margin: 0 7.5px;
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

## Apply changes

```bash
omarchy-restart-waybar
```
