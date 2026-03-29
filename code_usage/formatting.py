"""Formatting helpers for terminal, JSON, and Waybar output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from code_usage.providers.base import ProviderUsage, UsageWindow


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


PROGRESS_BAR_WIDTH = 32


def status_from_utilization(utilization: float) -> str:
    """Map utilization to a severity status."""
    if utilization >= 90:
        return "critical"
    if utilization >= 70:
        return "warning"
    return "ok"


def usage_tier_class(utilization: float) -> str:
    """Map utilization to a granular Waybar CSS class."""
    if utilization >= 95:
        return "usage-95"
    if utilization >= 85:
        return "usage-85"
    if utilization >= 70:
        return "usage-70"
    if utilization >= 50:
        return "usage-50"
    return "usage-0"


def color_for_utilization(utilization: float) -> str:
    """Get ANSI color code for utilization."""
    if utilization >= 90:
        return Colors.RED
    if utilization >= 70:
        return Colors.YELLOW
    return Colors.GREEN


def icon_for_utilization(utilization: float) -> str:
    """Get a textual status icon."""
    if utilization >= 90:
        return "RED"
    if utilization >= 70:
        return "YEL"
    return "GRN"


def format_progress_bar(utilization: float) -> str:
    """Create a progress bar visualization."""
    filled = int(utilization / 100 * PROGRESS_BAR_WIDTH)
    empty = PROGRESS_BAR_WIDTH - filled
    return f"[{'█' * filled}{'░' * empty}]"


def format_time_remaining(reset_time_str: Optional[str]) -> str:
    """Format time remaining until reset."""
    if not reset_time_str:
        return "unknown"

    try:
        reset_time = datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = reset_time - now

        if delta.total_seconds() <= 0:
            return "soon"

        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h {minutes}m"
    except (AttributeError, ValueError):
        return "unknown"


def format_usage_window(window: UsageWindow) -> str:
    """Format a single usage window for terminal output."""
    color = color_for_utilization(window.utilization)
    icon = icon_for_utilization(window.utilization)
    percentage = int(window.utilization)
    progress_bar = format_progress_bar(window.utilization)
    time_remaining = format_time_remaining(window.resets_at)

    return (
        f"{window.title} ({window.subtitle})\n"
        f"  {icon} {color}{percentage}%{Colors.RESET}  {progress_bar}\n"
        f"  {Colors.DIM}Resets in {time_remaining}{Colors.RESET}"
    )


def format_terminal_output(
    primary: ProviderUsage,
    providers: List[ProviderUsage],
    selection_mode: str,
    program_counts: Optional[Dict[str, int]] = None,
) -> str:
    """Format full terminal output."""
    lines: List[str] = [
        f"{Colors.BOLD}Code Usage Status{Colors.RESET}",
        "=" * 17,
        "",
    ]

    if len(providers) > 1 or selection_mode == "auto":
        lines.append(
            f"Primary Provider: {primary.display_name} "
            f"({int(primary.max_utilization)}%, selected via {selection_mode})"
        )
        lines.append("")

    for provider in providers:
        header = provider.display_name
        if provider.plan_type:
            header = f"{header} [{provider.plan_type}]"
        if provider.experimental:
            header = f"{header} (experimental)"

        lines.append(f"{Colors.BOLD}{header}{Colors.RESET}")
        lines.append("-" * len(header))
        for window in provider.windows:
            lines.append(format_usage_window(window))
            lines.append("")

        if provider.warning:
            lines.append(f"{Colors.DIM}{provider.warning}{Colors.RESET}")
            lines.append("")

    if program_counts is not None:
        lines.extend(format_process_info(program_counts).splitlines())
        lines.append("")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"{Colors.DIM}Last updated: {timestamp}{Colors.RESET}")
    return "\n".join(lines).rstrip()


def format_process_info(program_counts: Dict[str, int]) -> str:
    """Format verbose process information."""
    lines = [
        f"{Colors.BOLD}Active Programs{Colors.RESET}",
        "-" * 15,
        "",
    ]
    total = sum(program_counts.values())
    if total == 0:
        lines.append(f"{Colors.DIM}No tracked programs running (idle mode){Colors.RESET}")
        return "\n".join(lines)

    for name, count in program_counts.items():
        if count <= 0:
            continue
        instance_word = "instance" if count == 1 else "instances"
        lines.append(f"  {Colors.GREEN}•{Colors.RESET} {name}: {count} {instance_word}")
    lines.append("")
    lines.append(
        f"{Colors.DIM}Total: {total} instance{'s' if total != 1 else ''} running{Colors.RESET}"
    )
    return "\n".join(lines)


def format_json_output(
    primary: ProviderUsage,
    providers: List[ProviderUsage],
    selection_mode: str,
    program_counts: Optional[Dict[str, int]] = None,
) -> str:
    """Format structured JSON output."""
    output = {
        "provider": primary.key,
        "provider_display_name": primary.display_name,
        "selection_mode": selection_mode,
        "status": primary.status,
        "max_utilization": int(primary.max_utilization),
        "providers": {provider.key: provider.to_dict() for provider in providers},
    }
    if program_counts is not None:
        output["process_counts"] = program_counts
    return json.dumps(output, indent=2)


def build_waybar_payload(
    primary: ProviderUsage,
    providers: List[ProviderUsage],
    program_counts: Dict[str, int],
) -> Dict[str, object]:
    """Build Waybar JSON output."""
    active = any(count > 0 for count in program_counts.values())
    percentage = int(primary.max_utilization)
    status = status_from_utilization(primary.max_utilization)
    tier_class = usage_tier_class(primary.max_utilization)

    text = f"\uf121 {percentage}%"

    tooltip_lines = [
        "Code Usage",
        "",
        f"Primary: {primary.display_name} ({percentage}%)",
    ]
    if primary.plan_type:
        tooltip_lines.append(f"Plan: {primary.plan_type}")

    for provider in providers:
        tooltip_lines.extend(["", provider.display_name])
        if provider.plan_type:
            tooltip_lines.append(f"Plan: {provider.plan_type}")
        for window in provider.windows:
            tooltip_lines.append(
                f"{window.title}: {int(window.utilization)}% "
                f"(resets in {format_time_remaining(window.resets_at)})"
            )
        if provider.warning:
            tooltip_lines.append(provider.warning)

    active_programs = [
        f"{name} ({count})" for name, count in program_counts.items() if count > 0
    ]
    mode_line = "Mode: Active coding" if active else "Mode: Idle"
    if active_programs:
        mode_line = f"{mode_line} | Tracked: {', '.join(active_programs)}"
    tooltip_lines.extend(["", mode_line])

    return {
        "text": text,
        "tooltip": "\n".join(tooltip_lines),
        "class": [status, tier_class, "active" if active else "idle"],
        "percentage": percentage,
        "alt": primary.key if active else "idle",
    }
