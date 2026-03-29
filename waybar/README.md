# Waybar Integration for Code Usage

This directory contains the Waybar integration for `code-usage`.

## Default module

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

The module shows the provider currently in the highest-risk state, using compact labels such as `Cl 23%` or `Cx 61%`.

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

## Compatibility alias

If you want a Claude-only Waybar module during migration:

```jsonc
"exec": "~/.local/bin/claude-usage-waybar"
```

## Omarchy

See [OMARCHY.md](OMARCHY.md).
