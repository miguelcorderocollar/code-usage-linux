# Omarchy-Focused Plan: Conditional Reset Notification for ccusage-linux

## Overview
Adapt the ccusage-linux tool to add automatic desktop notifications when usage limits reset (session or weekly), but only if the previous usage was at 100% or higher. This leverages Omarchy's notification stack (Mako) and integrates with Waybar for a seamless Hyprland experience.

## Why Omarchy-Focused?
Omarchy provides a curated Arch Linux/Hyprland setup with:
- Mako as the notification daemon (configured in `~/.config/mako/`)
- Waybar for status bars (requires `omarchy-restart-waybar` after changes)
- Hooks for automation (`~/.config/omarchy/hooks/`)
- Commands like `omarchy-refresh-waybar` for safe config resets

This ensures the feature fits Omarchy's aesthetic and productivity philosophy without manual config hassles.

## Adapted Feature Details
- **Notification System**: Use Mako (via `makoctl` or direct integration) instead of `notify-send` for Hyprland-native notifications. Customize style to match current Omarchy theme.
- **Trigger**: Automatic on reset detection during normal 2-minute API polls.
- **Condition**: Only notify if previous usage ≥100% (avoids spam for normal resets).
- **Content**: "Session/Weekly limit reset! Previous usage was at [X]% - time to resume coding." Include theme-matched styling and optional sound.
- **Integration**: Enhance Waybar module as an "Omarchy special patch" – modify `~/.config/waybar/config.jsonc` to use a patched version of `claude-usage-waybar.py`.

## Implementation Steps
### 1. Core Logic Changes
   - Modify `claude-usage.py` to track last usage state in `~/.cache/ccusage-last-usage.json`.
   - Add reset detection: Check for `resets_at` changes and previous ≥100% usage.
   - On qualifying reset, trigger Mako notification using Python subprocess.

### 2. Waybar and Omarchy Integration
   - Update `waybar/claude-usage-waybar.py` with notification logic.
   - Patch Waybar config (`~/.config/waybar/config.jsonc`) to enable the feature (e.g., add `--notify-on-reset` flag).
   - Use Omarchy commands: After changes, run `omarchy-refresh-waybar` to apply safely.
   - Optional: Create hook `~/.config/omarchy/hooks/theme-set` to adjust notification style on theme changes.

### 3. User Experience
   - **Automatic**: No user action – notifications appear passively.
   - **Control**: Enable via script flag (default on for Omarchy). Manual test: `python3 claude-usage.py --test-reset-notification`.
   - **Keybinding**: Add to `~/.config/hypr/bindings.conf` for testing: `bind = SUPER, U, exec, python3 claude-usage.py --test-reset-notification`.

### 4. Testing and Validation
   - Test with mocked API responses for ≥100% usage.
   - Ensure Mako notifications display correctly in Hyprland.
   - Run Omarchy debug: `omarchy-debug --no-sudo --print` if issues arise.

## Tradeoffs and Notes
- **Performance**: Minimal impact (file I/O on polls).
- **Customization**: Notification style ties to Omarchy theme for consistency.
- **Fallback**: If Mako unavailable, fall back to `notify-send`.
- **Edge Cases**: Handle API downtime gracefully; add cooldown for rapid resets.

## Next Steps
- Implement core logic in `claude-usage.py`.
- Test Waybar integration and Omarchy commands.
- Document in README or create Omarchy-specific docs.