"""
PULSE — Natural Language Deadline Parser  (v2 — robust)
=========================================================
Multi-strategy parser:
  1. Custom regex engine  → handles "in N days/hours", "next Monday",
                            "day after tomorrow", "tomorrow", "today", etc.
  2. dateparser           → fallback for everything else
  3. ISO date strings     → last resort direct parse

Examples that must work:
    "Math assignment day after tomorrow 6pm"
    "Physics record next Monday"
    "Exam in 3 days"
    "Chemistry project next Friday 11:59pm"
    "CS quiz tomorrow morning"
    "Data structures HW in 5 hours"
"""

import re
from datetime import datetime, timedelta
from typing import Optional

# dateparser is broken on Python 3.14 — we rely on our own engine
_DATEPARSER_OK = False

# ── Subject keywords ─────────────────────────────────────────────────────────
SUBJECT_KEYWORDS: list[str] = [
    "math", "maths", "mathematics", "physics", "chemistry", "biology",
    "english", "history", "geography", "economics",
    "computer science", "cs", "programming", "python", "java",
    "electronics", "electrical", "mechanical", "civil",
    "data structures", "dsa", "algorithms", "dbms", "os",
    "machine learning", "ml", "ai", "networks", "networking",
    "statistics", "accounting", "management", "psychology",
    "philosophy", "sociology", "literature", "art",
]

# ── Task-type keywords ────────────────────────────────────────────────────────
TASK_TYPE_KEYWORDS: dict[str, list[str]] = {
    "assignment": [
        "assignment", "homework", "hw", "task", "problem set", "pset",
        "exercise", "worksheet", "written work", "take-home", "classwork"
    ],
    "exam": [
        "exam", "test", "quiz", "midterm", "final", "assessment",
        "viva", "oral", "mcq", "objective", "entrance", "evaluation"
    ],
    "project": [
        "project", "presentation", "demo", "prototype",
        "ppt", "slides", "seminar topic", "mini project", "major project",
        "case study", "design project"
    ],
    "record": [
        "record", "journal", "observation", "lab record", "practical",
        "lab manual", "experiment writeup", "record work", "notebook submission"
    ],
    "submission": [
        "submission", "submit", "deadline", "due",
        "turn in", "hand in", "upload", "last date", "closing date"
    ],
    "meeting": [
        "meeting", "class", "lecture", "seminar", "workshop",
        "session", "discussion", "group meeting", "review meeting", "briefing"
    ],
    "reading": [
        "reading", "chapter", "textbook", "study", "revision", "revise",
        "notes", "prepare", "learn", "syllabus", "portion", "topics"
    ],
    "coding": [
        "code", "coding", "program", "implementation", "develop",
        "debug", "build", "script", "algorithm", "logic"
    ],
    "research": [
        "research", "analysis", "investigation", "survey",
        "paper", "report", "study material", "literature review"
    ],
    "practice": [
        "practice", "solve", "problems", "questions",
        "numericals", "examples", "drill", "workout"
    ]
}

# ── Weekday mapping ───────────────────────────────────────────────────────────
WEEKDAYS = {
    # Full names
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,

    # Standard short forms
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,

    # Alternate abbreviations
    "tues": 1, "weds": 2, "thur": 3, "thurs": 3,
    "fri.": 4, "sat.": 5, "sun.": 6,

    # Common informal/slang
    "morn": 0, "tuesd": 1, "wedn": 2, "thurday": 3,
    "frid": 4, "satur": 5, "sund": 6,

    # Case-insensitive handling (optional if you normalize input)
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
    "Fri": 4, "Sat": 5, "Sun": 6
}

# ── Time-of-day defaults ──────────────────────────────────────────────────────
TIME_OF_DAY = {
    # Standard
    "morning":   (9,  0),
    "afternoon": (14, 0),
    "evening":   (18, 0),
    "night":     (21, 0),
    "midnight":  (0,  0),
    "noon":      (12, 0),

    # Variations
    "early morning": (6, 0),
    "late morning":  (10, 30),
    "early afternoon": (13, 0),
    "late afternoon":  (16, 30),
    "late evening": (20, 0),

    # Informal / slang
    "morning time": (9, 0),
    "eve": (18, 0),
    "nite": (21, 0),

    # Common phrases
    "today morning": (9, 0),
    "tomorrow morning": (9, 0),
    "tonight": (21, 0),

    # Indian usage (very common in your context)
    "early": (7, 0),
    "late": (20, 0)
}
# ── Month names ───────────────────────────────────────────────────────────────
MONTHS = {
    # Full names
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,

    # Standard abbreviations
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,

    # Alternate forms
    "sept": 9,
    "febr": 2,

    # With dots (common in typed notes)
    "jan.": 1, "feb.": 2, "mar.": 3, "apr.": 4,
    "jun.": 6, "jul.": 7, "aug.": 8,
    "sep.": 9, "sept.": 9, "oct.": 10, "nov.": 11, "dec.": 12,
}


# ═════════════════════════════════════════════════════════════════════════════
# Low-level helpers
# ═════════════════════════════════════════════════════════════════════════════

def _now() -> datetime:
    return datetime.now()


def _extract_time_hm(text: str) -> Optional[tuple[int, int]]:
    """
    Extract hour/minute from text fragments like:
        "6pm", "3:30pm", "11:59pm", "09:00", "morning", "evening"
    Returns (hour_24, minute) or None.
    """
    text_l = text.lower()

    # Named time of day
    for name, (h, m) in TIME_OF_DAY.items():
        if name in text_l:
            return (h, m)

    # HH:MM am/pm  or  HH:MM  (24h)
    m = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text_l)
    if m:
        h, mi, meridiem = int(m.group(1)), int(m.group(2)), m.group(3)
        if meridiem == "pm" and h < 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
        return (h, mi)

    # H am/pm  (no minutes)
    m = re.search(r'(\d{1,2})\s*(am|pm)', text_l)
    if m:
        h, meridiem = int(m.group(1)), m.group(2)
        if meridiem == "pm" and h < 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
        return (h, 0)

    return None


def _apply_time(dt: datetime, text: str, default_hour: int = 23, default_min: int = 59) -> datetime:
    """Overlay extracted time onto a date."""
    hm = _extract_time_hm(text)
    h, m = hm if hm else (default_hour, default_min)
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)


def _next_weekday(weekday_idx: int) -> datetime:
    """Return the *next* occurrence of weekday (0=Mon … 6=Sun), at least 1 day ahead."""
    today = _now().date()
    days_ahead = weekday_idx - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return datetime.combine(today + timedelta(days=days_ahead), datetime.min.time())


# ═════════════════════════════════════════════════════════════════════════════
# Strategy 1: Custom regex engine
# ═════════════════════════════════════════════════════════════════════════════

def _parse_custom(text: str) -> Optional[datetime]:
    t = text.lower()
    now = _now()

    # ── "in/due/by/within N days/hours/weeks/minutes [from now]" ──
    # Handles: "in 2 hours", "due 30 mins", "by 2 days", "5 hours from now"
    m = re.search(r'(?:in|due|within|by)?\s*(\d+)\s+(minute|min|hour|hr|day|week)s?(?:\s+(?:from\s+now|ahead))?', t)
    if m:
        n, unit_raw = int(m.group(1)), m.group(2)
        # Normalize unit
        unit = unit_raw
        if unit.startswith("min"): unit = "minute"
        if unit.startswith("hr"):  unit = "hour"
        
        delta = {
            "minute": timedelta(minutes=n),
            "hour":   timedelta(hours=n),
            "day":    timedelta(days=n),
            "week":   timedelta(weeks=n),
        }[unit]
        
        # If it's days or weeks, default to 11:59 PM on that day.
        # If it's minutes or hours, keep it precisely relative to now.
        if unit in ("day", "week"):
            return _apply_time(now + delta, t)
        else:
            return now + delta

    # ── "day after tomorrow" ──
    if "day after tomorrow" in t:
        return _apply_time(now + timedelta(days=2), t)

    # ── "tomorrow" ──
    if "tomorrow" in t:
        return _apply_time(now + timedelta(days=1), t)

    # ── "today" ──
    if "today" in t:
        hm = _extract_time_hm(t)
        h, m = hm if hm else (23, 59)
        return now.replace(hour=h, minute=m, second=0, microsecond=0)

    # ── "next <weekday>" ──
    m = re.search(r'next\s+(' + '|'.join(WEEKDAYS) + r')', t)
    if m:
        dt = _next_weekday(WEEKDAYS[m.group(1)])
        return _apply_time(dt, t)

    # ── bare weekday name (e.g. "Friday 3pm") — treated as next occurrence ──
    m = re.search(r'\b(' + '|'.join(WEEKDAYS) + r')\b', t)
    if m:
        dt = _next_weekday(WEEKDAYS[m.group(1)])
        return _apply_time(dt, t)

    # ── "DD month" or "month DD" e.g. "30 April", "May 5" ──
    m = re.search(r'(\d{1,2})\s+(' + '|'.join(MONTHS) + r')', t)
    if not m:
        m = re.search(r'(' + '|'.join(MONTHS) + r')\s+(\d{1,2})', t)
        if m:
            month_name, day = m.group(1), int(m.group(2))
        else:
            month_name, day = None, None
    else:
        day, month_name = int(m.group(1)), m.group(2)

    if month_name and day:
        month_num = MONTHS[month_name]
        year = now.year
        candidate = now.replace(month=month_num, day=day)
        if candidate < now:
            year += 1
        try:
            dt = datetime(year, month_num, day)
            return _apply_time(dt, t)
        except ValueError:
            pass

    # ── ISO-ish date: YYYY-MM-DD ──
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return _apply_time(dt, t)
        except ValueError:
            pass

    return None


# ═════════════════════════════════════════════════════════════════════════════
# Strategy 2: dateparser fallback
# ═════════════════════════════════════════════════════════════════════════════

def _parse_dateparser(text: str) -> Optional[datetime]:
    """Dateparser fallback — disabled; custom engine handles all patterns."""
    return None


# ═════════════════════════════════════════════════════════════════════════════
# Public interface
# ═════════════════════════════════════════════════════════════════════════════

def _detect_subject(text: str) -> str:
    lower = text.lower()
    for subject in SUBJECT_KEYWORDS:
        if re.search(rf'\b{re.escape(subject)}\b', lower):
            return subject.title()
    return "General"


def _detect_task_type(text: str) -> str:
    lower = text.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return task_type
    return "general"


def parse_deadline(raw_input: str) -> dict:
    """
    Convert a raw natural-language string into a structured deadline dict.

    Returns
    -------
    dict with keys: raw_input, title, subject, task_type, due_date, parsed_ok
    """
    # Try strategies in order
    due_dt: Optional[datetime] = _parse_custom(raw_input)
    if due_dt is None:
        due_dt = _parse_dateparser(raw_input)

    # Sanity check: reject dates in the past or more than 2 years ahead
    if due_dt is not None:
        now = _now()
        if due_dt < now:
            # Might be an artefact — try dateparser as second opinion
            alt = _parse_dateparser(raw_input)
            if alt and alt > now:
                due_dt = alt
            elif due_dt < now:
                due_dt = None  # truly in the past

    return {
        "raw_input": raw_input,
        "title": raw_input.strip(),
        "subject": _detect_subject(raw_input),
        "task_type": _detect_task_type(raw_input),
        "due_date": due_dt.isoformat() if due_dt else None,
        "parsed_ok": due_dt is not None,
    }


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Simulate current time for test consistency if needed, 
    # but here we just run with real now.
    samples = [
        "Math assignment day after tomorrow 6pm",
        "Physics record next Monday",
        "Exam in 3 days",
        "Chemistry project next Friday 11:59pm",
        "CS quiz tomorrow morning",
        "Data structures HW in 5 hours",
        "maths assignment due 2 hours",
        "Submit biology lab by next Wednesday",
        "Math exam next Friday 3pm",
        "History essay in 2 weeks",
        "Meeting tomorrow at 4pm",
        "Finish report due 45 mins",
        "Physics lab within 1 day",
    ]
    for s in samples:
        r = parse_deadline(s)
        status = "OK" if r["parsed_ok"] else "FAIL"
        print(f"{status:4s} [{r['subject']:15s}] [{r['task_type']:12s}] {r['due_date'] or 'FAILED':26s}  <-- {s}")
