# Waybar Integration for Claude Usage

This directory contains everything needed to integrate Claude Code usage monitoring into your Waybar status bar.

> **🎯 Using Omarchy?** See [OMARCHY.md](OMARCHY.md) for Omarchy-specific configuration that avoids signal conflicts and uses Omarchy's launcher patterns.

## Features

- **Real-time monitoring** - Shows current usage in your status bar
- **Color-coded status** - Visual indicators (🟢 green, 🟡 yellow, 🔴 red)
- **Rich tooltips** - Hover to see detailed usage breakdown
- **Auto-refresh** - Updates every 2 minutes (configurable)
- **Click actions** - Left-click for terminal details, right-click to refresh
- **Error handling** - Clear indicators for login/network issues

## Preview

**Status bar display:**
```
🟢 30%    (Normal usage)
🟡 75%    (Warning - high usage)
🔴 92%    (Critical - very high usage)
❌ Claude (Not logged in)
```

**Tooltip on hover:**
```
Claude Code Usage

Session (5h): 30%
  Resets in 3h 57m

Weekly (7d): 4%
  Resets in 6d 22h
```

## Installation

### 1. Install the Waybar Module Script

```bash
# From the project directory
cd waybar
chmod +x claude-usage-waybar.py

# Copy to your local bin (recommended)
cp claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/claude-usage-waybar

# OR for system-wide install:
sudo cp claude-usage-waybar.py /usr/local/bin/claude-usage-waybar
```

### 2. Configure Waybar

Add the module to your Waybar config at `~/.config/waybar/config.jsonc`:

```jsonc
{
    // Add "custom/claude-usage" to your modules list
    "modules-right": [
        "custom/claude-usage",  // Add this line
        "pulseaudio",
        "network",
        "battery",
        "clock"
    ],

    // Add the module definition
    "custom/claude-usage": {
        "exec": "~/.local/bin/claude-usage-waybar",
        "return-type": "json",
        "interval": 120,  // Refresh every 2 minutes
        "signal": 8,      // Manual refresh: pkill -SIGRTMIN+8 waybar
        "format": "{text}",
        "on-click": "notify-send 'Claude Usage' \"$(~/.local/bin/claude-usage)\"",  // Show notification
        "on-click-right": "pkill -SIGRTMIN+8 waybar",  // Force refresh
        "tooltip": true,
        "max-length": 25
    }
}
```

**Note:** Left-click shows a desktop notification with current usage. Right-click refreshes the module.

### 3. Add CSS Styling

Add the styles to your Waybar CSS at `~/.config/waybar/style.css`:

```css
/* Claude Usage Module */
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

#custom-claude-usage.warning {
    color: #f9e2af;
    background-color: rgba(249, 226, 175, 0.1);
    border: 1px solid rgba(249, 226, 175, 0.3);
}

#custom-claude-usage.critical {
    color: #f38ba8;
    background-color: rgba(243, 139, 168, 0.1);
    border: 1px solid rgba(243, 139, 168, 0.3);
    animation: pulse 2s infinite;
}

#custom-claude-usage.error {
    color: #cba6f7;
    background-color: rgba(203, 166, 247, 0.1);
    border: 1px solid rgba(203, 166, 247, 0.3);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

See `style.css` for alternative styling options (minimalist, bold, light theme, etc.)

### 4. Restart Waybar

```bash
pkill waybar && waybar &
# OR if using systemd:
systemctl --user restart waybar
```

## Update

To update to a newer version of the integration:

### 1. Update the Project Files

Pull the latest changes or download the updated files to your local copy.

### 2. Reinstall the Script

```bash
# From the project directory
cd waybar

# Update your local bin copy
cp claude-usage-waybar.py ~/.local/bin/claude-usage-waybar
chmod +x ~/.local/bin/claude-usage-waybar

# OR for system-wide install:
sudo cp claude-usage-waybar.py /usr/local/bin/claude-usage-waybar
```

### 3. Check for Config Changes

Review the latest `README.md` and example config in this directory. If there are changes to the Waybar module configuration, update your `~/.config/waybar/config.jsonc` accordingly.

### 4. Restart Waybar

```bash
pkill waybar && waybar &
# OR if using systemd:
systemctl --user restart waybar
```

**Note:** If you're using Omarchy, check [OMARCHY.md](OMARCHY.md) for any additional update steps specific to your setup.

## Configuration Options

### Refresh Interval

Change the `interval` value in the config (in seconds):

```jsonc
"interval": 60,   // Refresh every 1 minute
"interval": 300,  // Refresh every 5 minutes
"interval": 120,  // Default: every 2 minutes
```

### Manual Refresh

Trigger a manual update with a signal:

```bash
pkill -SIGRTMIN+8 waybar
```

**Note:** The signal number (8) matches the `"signal": 8` in the config. Change both if needed.

### Click Actions

By default, left-click shows a desktop notification with usage details. Customize the actions:

```jsonc
"on-click": "kitty -e claude-usage",              // Open in kitty terminal
"on-click": "gnome-terminal -- claude-usage",     // Open in GNOME Terminal
"on-click": "notify-send 'Usage' '$(claude-usage)'",  // Show notification
"on-click-middle": "claude-usage --json",         // Show JSON on middle-click
```

### Format Options

Customize the display format:

```jsonc
// Show just the emoji and percentage
"format": "{text}",

// Show with a custom prefix
"format": "Claude: {text}",

// Show percentage as progress bar
"format": "{text} {percentage}%",

// Icon-based format (uses format-icons)
"format": "{icon} {percentage}%",
```

## Troubleshooting

### Module not appearing

1. Check the script is executable:
   ```bash
   ls -l ~/.local/bin/claude-usage-waybar
   # Should show: -rwxr-xr-x
   ```

2. Test the script manually:
   ```bash
   ~/.local/bin/claude-usage-waybar
   # Should output: {"text": "🟢 30%", ...}
   ```

3. Check Waybar logs:
   ```bash
   journalctl --user -u waybar -f
   ```

### Shows "Not logged in"

Make sure you're authenticated with Claude Code:
```bash
claude
```

### Module shows but no styling

1. Verify CSS file path in your Waybar config:
   ```jsonc
   "style": "~/.config/waybar/style.css"
   ```

2. Check CSS syntax is valid (no missing braces, semicolons)

3. Restart Waybar completely:
   ```bash
   pkill waybar && waybar &
   ```

### Module not updating

1. Check the interval is set correctly:
   ```jsonc
   "interval": 120,  // Should be a number, not a string
   ```

2. Manually trigger an update:
   ```bash
   pkill -SIGRTMIN+8 waybar
   ```

3. Check for Python errors:
   ```bash
   ~/.local/bin/claude-usage-waybar 2>&1
   ```

## Advanced Configuration

### Different Update Frequencies

Update session usage more frequently than weekly:

```jsonc
"custom/claude-session": {
    "exec": "~/.local/bin/claude-usage-waybar",
    "interval": 60,  // Every minute
    // ... rest of config
},
"custom/claude-weekly": {
    "exec": "~/.local/bin/claude-usage-waybar",
    "interval": 300,  // Every 5 minutes
    // ... rest of config
}
```

### Notification on Critical Usage

Create a wrapper script that sends notifications:

```bash
#!/bin/bash
output=$(~/.local/bin/claude-usage-waybar)
usage=$(echo "$output" | jq -r .percentage)

if [ "$usage" -ge 90 ]; then
    notify-send -u critical "Claude Usage Critical" "Usage at ${usage}%!"
fi

echo "$output"
```

## Color Themes

The included CSS uses Catppuccin Mocha colors. See `style.css` for alternatives:

- **Catppuccin Mocha** (dark theme) - Default
- **Catppuccin Latte** (light theme) - Commented out
- **Minimalist** (no background) - Commented out
- **Bold** (solid backgrounds) - Commented out

Uncomment your preferred style or create your own!

## Files in This Directory

- `claude-usage-waybar.py` - Main Waybar module script
- `config.jsonc` - Waybar configuration snippet (example)
- `style.css` - CSS styling with multiple theme options
- `README.md` - This file

## Documentation References

Based on the latest Waybar documentation (January 2026):
- [Waybar Custom Modules](https://man.archlinux.org/man/extra/waybar/waybar-custom.5.en)
- [Waybar GitHub Wiki](https://github.com/Alexays/Waybar/wiki/Configuration)
- [Arch Linux Waybar Guide](https://wiki.archlinux.org/title/Waybar)

## Support

If you encounter issues:

1. Test the base script first: `claude-usage`
2. Test the Waybar script: `~/.local/bin/claude-usage-waybar`
3. Check Waybar logs: `journalctl --user -u waybar -f`
4. Verify you're logged in: `claude`

For more help, see the main [README.md](../README.md) in the parent directory.
