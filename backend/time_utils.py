"""
PULSE — Time Utilities
=======================
Centralised time-math used by the deadline engine, notifier, and API layer.
"""

from datetime import datetime, timedelta
from typing import Optional


def remaining_seconds(due_date: str) -> float:
    """
    Return the number of seconds between *now* and the ISO-8601 `due_date`.
    Negative values mean the deadline has already passed.
    """
    due_dt = datetime.fromisoformat(due_date).replace(tzinfo=None)
    delta = due_dt - datetime.now()
    return delta.total_seconds()


def remaining_hms(due_date: str) -> dict:
    """
    Return a dict with days, hours, minutes, seconds remaining.
    Includes a boolean `overdue` flag.
    """
    secs = remaining_seconds(due_date)
    overdue = secs < 0
    secs = abs(secs)

    days = int(secs // 86400)
    hours = int((secs % 86400) // 3600)
    minutes = int((secs % 3600) // 60)
    seconds = int(secs % 60)

    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "total_seconds": -secs if overdue else secs,
        "overdue": overdue,
        "formatted": format_countdown(days, hours, minutes, seconds, overdue),
    }


def format_countdown(
    days: int, hours: int, minutes: int, seconds: int, overdue: bool = False
) -> str:
    """Human-friendly countdown string."""
    prefix = "OVERDUE by " if overdue else ""
    if days > 0:
        return f"{prefix}{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"
    return f"{prefix}{hours:02d}:{minutes:02d}:{seconds:02d}"


def danger_level(due_date: str) -> str:
    """
    Classify urgency:
        > 72 h  → SAFE
        24-72 h → CAUTION
        1-24 h  → DANGER
        < 1 h   → PANIC
        past    → OVERDUE
    """
    secs = remaining_seconds(due_date)
    if secs < 0:
        return "OVERDUE"
    hours = secs / 3600
    if hours > 72:
        return "SAFE"
    if hours > 24:
        return "CAUTION"
    if hours > 1:
        return "DANGER"
    return "PANIC"


def danger_color(level: str) -> str:
    """Map danger level to a hex colour for the frontend."""
    return {
        "SAFE": "#00e676",
        "CAUTION": "#ffab00",
        "DANGER": "#ff5252",
        "PANIC": "#d500f9",
        "OVERDUE": "#616161",
    }.get(level, "#ffffff")


def is_within(due_date: str, hours: float) -> bool:
    """True if the deadline is within `hours` from now (and not overdue)."""
    secs = remaining_seconds(due_date)
    return 0 < secs <= hours * 3600


def smart_time_label(due_date: str) -> str:
    """Return a human-friendly relative label like '2 days left'."""
    secs = remaining_seconds(due_date)
    if secs < 0:
        return "Overdue"
    hours = secs / 3600
    if hours < 1:
        mins = int(secs / 60)
        return f"{mins} min left" if mins > 1 else "Less than a minute"
    if hours < 24:
        return f"{int(hours)} hr left"
    days = hours / 24
    if days < 7:
        return f"{int(days)} day{'s' if int(days) != 1 else ''} left"
    weeks = int(days / 7)
    return f"{weeks} week{'s' if weeks != 1 else ''} left"
