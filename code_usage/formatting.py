"""Formatting helpers for terminal and Waybar output."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from code_usage.providers.base import ProviderSnapshot, UsageWindow


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


PROGRESS_BAR_WIDTH = 32
PROVIDER_SHORT_NAMES = {"claude": "Cl", "codex": "Cx"}


def get_color(utilization: float) -> str:
    """Return ANSI color for utilization."""
    if utilization >= 90:
        return Colors.RED
    if utilization >= 70:
        return Colors.YELLOW
    return Colors.GREEN


def get_status_emoji(utilization: float) -> str:
    """Return status emoji for utilization."""
    if utilization >= 90:
        return "🔴"
    if utilization >= 70:
        return "🟡"
    return "🟢"


def parse_reset_timestamp(reset_time: Optional[str]) -> Optional[datetime]:
    """Parse reset timestamp from ISO8601 or unix seconds."""
    if reset_time in (None, ""):
        return None

    if reset_time.isdigit():
        try:
            return datetime.fromtimestamp(int(reset_time), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

    try:
        return datetime.fromisoformat(reset_time.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_time_remaining(reset_time: Optional[str]) -> str:
    """Format remaining time until reset."""
    parsed = parse_reset_timestamp(reset_time)
    if not parsed:
        return "unknown"

    now = datetime.now(timezone.utc)
    delta = parsed - now
    if delta.total_seconds() <= 0:
        return "soon"

    total_seconds = int(delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m"


def format_progress_bar(utilization: float) -> str:
    """Return a fixed-width unicode progress bar."""
    filled = int(utilization / 100 * PROGRESS_BAR_WIDTH)
    empty = PROGRESS_BAR_WIDTH - filled
    return f"[{'█' * filled}{'░' * empty}]"


def snapshot_to_json(snapshot: ProviderSnapshot) -> Dict[str, object]:
    """Serialize a provider snapshot to a JSON-safe dictionary."""
    data: Dict[str, object] = {
        "status": snapshot.status,
        "display_name": snapshot.display_name,
        "windows": {
            key: {
                "utilization": int(window.utilization),
                "resets_at": window.resets_at,
                "label": window.label,
                "subtitle": window.subtitle,
            }
            for key, window in snapshot.windows.items()
        },
    }
    data.update(snapshot.extra)
    if snapshot.warnings:
        data["warnings"] = snapshot.warnings
    return data


def build_json_output(
    snapshots: Dict[str, ProviderSnapshot],
    selected_provider: str,
    errors: Dict[str, str],
) -> str:
    """Return the unified JSON output payload."""
    selected_snapshot = snapshots[selected_provider]
    payload = {
        "selected_provider": selected_provider,
        "providers": {
            name: snapshot_to_json(snapshot)
            for name, snapshot in snapshots.items()
        },
        "status": selected_snapshot.status,
    }
    if errors:
        payload["errors"] = errors
    return json.dumps(payload, indent=2)


def format_usage_window(window: UsageWindow) -> str:
    """Format one usage window for terminal output."""
    color = get_color(window.utilization)
    emoji = get_status_emoji(window.utilization)
    return (
        f"{window.label} ({window.subtitle})\n"
        f"  {emoji} {color}{int(window.utilization)}%{Colors.RESET}  "
        f"{format_progress_bar(window.utilization)}\n"
        f"  {Colors.DIM}Resets in {format_time_remaining(window.resets_at)}{Colors.RESET}"
    )


def format_snapshot_sections(snapshot: ProviderSnapshot) -> List[str]:
    """Format one provider snapshot for terminal output."""
    sections = [
        f"{Colors.BOLD}{snapshot.display_name}{Colors.RESET}",
        "-" * len(snapshot.display_name),
        "",
    ]

    for window in snapshot.windows.values():
        sections.append(format_usage_window(window))
        sections.append("")

    if snapshot.extra.get("plan_type"):
        sections.append(f"{Colors.DIM}Plan: {snapshot.extra['plan_type']}{Colors.RESET}")

    for warning in snapshot.warnings:
        sections.append(f"{Colors.DIM}Note: {warning}{Colors.RESET}")

    return sections


def format_terminal_output(
    snapshots: Dict[str, ProviderSnapshot],
    selected_provider: str,
    errors: Dict[str, str],
) -> str:
    """Format the multi-provider terminal output."""
    sections = [f"{Colors.BOLD}Code Usage Status{Colors.RESET}", "=" * 17, ""]
    sections.extend(format_snapshot_sections(snapshots[selected_provider]))

    other_snapshots = [
        snapshot for name, snapshot in snapshots.items() if name != selected_provider
    ]
    if other_snapshots:
        sections.append("")
        sections.append(f"{Colors.BOLD}Other Providers{Colors.RESET}")
        sections.append("-" * 15)
        sections.append("")
        for snapshot in other_snapshots:
            short_name = PROVIDER_SHORT_NAMES.get(snapshot.provider, snapshot.provider[:2].title())
            sections.append(f"{short_name}: {int(snapshot.max_utilization)}% ({snapshot.status})")

    if errors:
        sections.append("")
        sections.append(f"{Colors.BOLD}Unavailable Providers{Colors.RESET}")
        sections.append("-" * 21)
        sections.append("")
        for provider, error in errors.items():
            sections.append(f"{provider}: {error}")

    sections.append("")
    sections.append(f"{Colors.DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    return "\n".join(sections)


def format_process_info(program_counts: Dict[str, int]) -> str:
    """Format process details for verbose CLI output."""
    sections = [f"{Colors.BOLD}Active Programs{Colors.RESET}", "-" * 24, ""]
    total_instances = sum(program_counts.values())
    if total_instances == 0:
        sections.append(f"{Colors.DIM}No tracked programs running (idle mode){Colors.RESET}")
        return "\n".join(sections)

    for name, count in program_counts.items():
        if count <= 0:
            continue
        instance_word = "instance" if count == 1 else "instances"
        sections.append(f"  {Colors.GREEN}•{Colors.RESET} {name}: {count} {instance_word}")

    sections.append("")
    sections.append(f"{Colors.DIM}Total: {total_instances} instance{'s' if total_instances != 1 else ''} running{Colors.RESET}")
    return "\n".join(sections)


def select_primary_provider(snapshots: Dict[str, ProviderSnapshot]) -> str:
    """Return the provider with the highest utilization."""
    return max(
        snapshots.items(),
        key=lambda item: (item[1].max_utilization, item[0] == "codex"),
    )[0]


def build_waybar_output(
    snapshots: Dict[str, ProviderSnapshot],
    selected_provider: str,
    errors: Dict[str, str],
    program_counts: Dict[str, int],
) -> Dict[str, object]:
    """Build the JSON payload for Waybar."""
    if not snapshots:
        tooltip_lines = ["Code Usage", ""]
        for provider, error in errors.items():
            tooltip_lines.append(f"{provider}: {error}")
        return {
            "text": "Err",
            "tooltip": "\n".join(tooltip_lines),
            "class": "error",
            "percentage": 0,
            "alt": "error",
        }

    selected = snapshots[selected_provider]
    short_name = PROVIDER_SHORT_NAMES.get(selected_provider, selected_provider[:2].title())

    tooltip_lines = ["Code Usage", ""]
    for snapshot in snapshots.values():
        tooltip_lines.append(snapshot.display_name)
        for window in snapshot.windows.values():
            tooltip_lines.append(
                f"{window.label}: {int(window.utilization)}% ({format_time_remaining(window.resets_at)})"
            )
        if snapshot.extra.get("plan_type"):
            tooltip_lines.append(f"Plan: {snapshot.extra['plan_type']}")
        for warning in snapshot.warnings:
            tooltip_lines.append(f"Note: {warning}")
        tooltip_lines.append("")

    if errors:
        tooltip_lines.append("Unavailable")
        for provider, error in errors.items():
            tooltip_lines.append(f"{provider}: {error}")
        tooltip_lines.append("")

    tooltip_lines.append(
        "Tracked: " + ", ".join(f"{name} ({count})" for name, count in program_counts.items())
    )

    return {
        "text": f"{short_name} {int(selected.max_utilization)}%",
        "tooltip": "\n".join(tooltip_lines).strip(),
        "class": selected.status,
        "percentage": int(selected.max_utilization),
        "alt": selected_provider,
    }

