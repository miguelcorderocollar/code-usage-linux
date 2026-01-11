# Omarchy Integration Guide

Configuration guide for integrating Claude Usage with Omarchy's Waybar setup.

## Important: Signal Conflict

Your current config has a **signal conflict**:
- `custom/screenrecording-indicator` uses `signal: 8`
- `custom/claude-usage` also uses `signal: 8`

This means both modules will refresh when you send `SIGRTMIN+8`, which is incorrect.

**Fix:** Change Claude Usage to use `signal: 9` (or any unused signal number).

## Omarchy-Optimized Configuration

Replace your current `custom/claude-usage` section with this:

```jsonc
"custom/claude-usage": {
  "exec": "~/.local/bin/claude-usage-waybar",
  "return-type": "json",
  "interval": 120,
  "signal": 9,  // Changed from 8 to avoid conflict with screenrecording-indicator
  "format": "{text}",
    "on-click": "xdg-terminal-exec --app-id=org.omarchy.claude-usage -e bash -c 'claude-usage; echo; echo Press Enter to close; read'",
  "on-click-right": "pkill -SIGRTMIN+9 waybar",
  "tooltip": true,
  "max-length": 25
}
```

### Changes Made

1. **Signal changed to 9** - Avoids conflict with screen recording indicator
2. **Uses xdg-terminal-exec** - Launches ghostty (Omarchy's default terminal) with proper app-id without presentation mode
3. **Updated refresh command** - Now uses `SIGRTMIN+9` to match the new signal

## Complete Module Position

Your modules-right already includes claude-usage in a good position:

```jsonc
"modules-right": [
  "group/tray-expander",
  "custom/claude-usage",    // ← Already here, good position!
  "bluetooth",
  "network",
  "custom/pia-vpn",
  "pulseaudio",
  "cpu",
  "battery"
]
```

## Installation for Omarchy

### 1. Install the Script

```bash
# Copy to local bin (from the project directory)
cd waybar
chmod +x claude-usage-waybar.py
cp claude-usage-waybar.py ~/.local/bin/claude-usage-waybar

# Also install the main CLI tool
cd ..
chmod +x claude-usage.py
cp claude-usage.py ~/.local/bin/claude-usage
```

### 2. Update Waybar Config

Edit `~/.config/waybar/config.jsonc` and update the `custom/claude-usage` section with the configuration above.

### 3. Add CSS Styling

Add to `~/.config/waybar/style.css`:

```css
/* Claude Usage Module - Omarchy Style */
#custom-claude-usage {
    padding: 0 10px;
    margin: 0 5px;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease;
}

#custom-claude-usage.ok {
    color: #a6e3a1;
    background-color: rgba(166, 227, 161, 0.1);
    border: 1px solid rgba(166, 227, 161, 0.3);
}

#custom-claude-usage.ok:hover {
    background-color: rgba(166, 227, 161, 0.2);
    border-color: rgba(166, 227, 161, 0.5);
}

#custom-claude-usage.warning {
    color: #f9e2af;
    background-color: rgba(249, 226, 175, 0.1);
    border: 1px solid rgba(249, 226, 175, 0.3);
}

#custom-claude-usage.warning:hover {
    background-color: rgba(249, 226, 175, 0.2);
    border-color: rgba(249, 226, 175, 0.5);
}

#custom-claude-usage.critical {
    color: #f38ba8;
    background-color: rgba(243, 139, 168, 0.1);
    border: 1px solid rgba(243, 139, 168, 0.3);
    animation: pulse 2s infinite;
}

#custom-claude-usage.critical:hover {
    background-color: rgba(243, 139, 168, 0.2);
    border-color: rgba(243, 139, 168, 0.5);
}

#custom-claude-usage.error {
    color: #cba6f7;
    background-color: rgba(203, 166, 247, 0.1);
    border: 1px solid rgba(203, 166, 247, 0.3);
}

#custom-claude-usage.error:hover {
    background-color: rgba(203, 166, 247, 0.2);
    border-color: rgba(203, 166, 247, 0.5);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

### 4. Restart Waybar

```bash
pkill waybar && waybar &
```

Or if you have a reload command:
```bash
omarchy-reload-waybar  # If this exists
```

## Manual Refresh Command

To manually refresh the Claude Usage module:

```bash
pkill -SIGRTMIN+9 waybar
```

## Keybinding Suggestion

Add to your Hyprland config (`~/.config/hypr/hyprland.conf`):

```conf
# Refresh Claude usage in Waybar
bind = SUPER ALT, C, exec, pkill -SIGRTMIN+9 waybar
```

## Troubleshooting

### Module Not Showing

1. Check the script is installed:
   ```bash
   ls -l ~/.local/bin/claude-usage-waybar
   ```

2. Test it manually:
   ```bash
   ~/.local/bin/claude-usage-waybar
   ```
   Should output JSON like: `{"text": "🟢 30%", ...}`

3. Check Waybar logs:
   ```bash
   journalctl --user -u waybar -f
   ```

### Terminal Closes Instantly on Click

The terminal opens but closes immediately because `claude-usage` is a command that runs and exits quickly. To keep the terminal open after showing the usage, use:

```jsonc
"on-click": "omarchy-launch-floating-terminal-with-presentation bash -c 'claude-usage; echo; echo Press Enter to close; read'",
```

### Terminal Doesn't Open on Click

If `omarchy-launch-floating-terminal-with-presentation` doesn't work, you can use the standard Omarchy terminal command:

```jsonc
"on-click": "xdg-terminal-exec bash -c 'claude-usage; echo; echo Press Enter to close; read'",
```

This uses xdg-terminal-exec which launches ghostty (Omarchy's configured terminal) with the proper Omarchy app-id.

### Signal Not Working

Make sure you're using the correct signal number:
```bash
# This should refresh the module
pkill -SIGRTMIN+9 waybar

# If signal 9 doesn't work, try finding an unused signal
# Check what signals are in use in your config
grep -o 'signal.*[0-9]' ~/.config/waybar/config.jsonc
```

## Omarchy Menu Integration (Optional)

To add Claude Usage to the Omarchy menu, you could create a custom menu item.

Check if there's an omarchy menu config file like `~/.config/omarchy/menu.conf` or similar, and add:

```
Claude Usage
  claude-usage
  Show Claude Code usage limits
```

## Alternative: Create Custom Omarchy Command

Create `/usr/local/bin/omarchy-claude-usage`:

```bash
#!/bin/bash
omarchy-launch-floating-terminal-with-presentation claude-usage
```

Then use in config:
```jsonc
"on-click": "omarchy-claude-usage",
```

## Styling to Match Omarchy Theme

The CSS above uses Catppuccin Mocha colors which should match Omarchy's aesthetic. If your Omarchy setup uses different colors, adjust the CSS color values to match.

To extract your current color scheme:
```bash
grep -E '#[0-9a-fA-F]{6}|rgba?\(' ~/.config/waybar/style.css | head -20
```

## Module Positioning

The current position in `modules-right` between `tray-expander` and `bluetooth` is ideal:
- Close to system indicators
- Visible but not intrusive
- Good logical grouping with other status modules

## Summary of Changes from Default Config

| Setting | Default | Omarchy Version | Reason |
|---------|---------|-----------------|---------|
| signal | 8 | 9 | Avoid conflict with screenrecording |
| on-click | `alacritty -e` | `xdg-terminal-exec --app-id=org.omarchy.claude-usage -e bash -c 'claude-usage; echo; echo Press Enter to close; read'` | Use xdg-terminal-exec with proper app-id |
| on-click-right | `pkill -SIGRTMIN+8` | `pkill -SIGRTMIN+9` | Match new signal number |

## Additional Omarchy Integrations

### Add to Hyprland Workspace Rules

If you want the terminal to float when showing usage:

```conf
# ~/.config/hypr/hyprland.conf
windowrulev2 = float,class:(claude-usage)
windowrulev2 = size 800 600,class:(claude-usage)
windowrulev2 = center,class:(claude-usage)
```

### Notification Integration

Create a script to notify on high usage:

```bash
#!/bin/bash
# ~/bin/omarchy-claude-usage-check

output=$(~/.local/bin/claude-usage-waybar)
percentage=$(echo "$output" | jq -r .percentage)

if [ "$percentage" -ge 90 ]; then
    notify-send -u critical "Claude Usage Critical" \
                "Usage at ${percentage}%!" \
                -i dialog-warning
fi
```

Add to crontab:
```bash
*/15 * * * * ~/bin/omarchy-claude-usage-check
```

## Files Modified

- `~/.config/waybar/config.jsonc` - Add/update custom/claude-usage
- `~/.config/waybar/style.css` - Add CSS styling
- `~/.local/bin/claude-usage-waybar` - Install script
- `~/.local/bin/claude-usage` - Install CLI tool

After making these changes, your Claude Usage module will integrate seamlessly with Omarchy's design patterns and avoid any conflicts with existing modules.
