"""
PULSE — Deadline Engine
========================
Central intelligence layer that manages, sorts, and analyses deadlines.
Implements Smart Priority Boost, Overdue Detection, Stress Analysis,
and Smart Suggestions.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from time_utils import (
    remaining_seconds,
    remaining_hms,
    danger_level,
    danger_color,
    smart_time_label,
)


class DeadlineEngine:
    """
    In-memory deadline manager. Works with or without Firebase — the
    db_manager calls into this engine after syncing.
    """

    def __init__(self):
        self._deadlines: dict[str, dict] = {}  # id → deadline dict

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, deadline: dict) -> dict:
        """
        Accept a parsed deadline dict (from nlp_parser) and enrich it.
        Returns the enriched deadline with id, danger level, etc.
        """
        did = deadline.get("id") or uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()

        enriched = {
            "id": did,
            "title": deadline.get("title", "Untitled"),
            "subject": deadline.get("subject", "General"),
            "task_type": deadline.get("task_type", "general"),
            "due_date": deadline.get("due_date"),
            "raw_input": deadline.get("raw_input", ""),
            "class_code": deadline.get("class_code", None),
            "created_by": deadline.get("created_by", "anonymous"),
            "created_at": now,
            "completed": False,
            "notified_24h": False,
            "notified_3h": False,
            "notified_1h": False,
        }

        # Compute live fields
        if enriched["due_date"]:
            enriched["danger"] = danger_level(enriched["due_date"])
            enriched["danger_color"] = danger_color(enriched["danger"])
            enriched["time_label"] = smart_time_label(enriched["due_date"])
            enriched["countdown"] = remaining_hms(enriched["due_date"])
        else:
            enriched["danger"] = "UNKNOWN"
            enriched["danger_color"] = "#ffffff"
            enriched["time_label"] = "No date"
            enriched["countdown"] = None

        self._deadlines[did] = enriched
        return enriched

    def remove(self, deadline_id: str) -> bool:
        return self._deadlines.pop(deadline_id, None) is not None

    def mark_complete(self, deadline_id: str) -> Optional[dict]:
        d = self._deadlines.get(deadline_id)
        if d:
            d["completed"] = True
        return d

    def get(self, deadline_id: str) -> Optional[dict]:
        d = self._deadlines.get(deadline_id)
        if d:
            self._refresh(d)
        return d

    def load_all(self, deadlines: list[dict]):
        """Bulk-load deadlines (e.g. from Firebase)."""
        for d in deadlines:
            self._deadlines[d["id"]] = d

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def all_sorted(self, class_code: Optional[str] = None) -> list[dict]:
        """Return deadlines sorted by urgency (soonest first)."""
        pool = list(self._deadlines.values())
        if class_code:
            pool = [d for d in pool if d.get("class_code") == class_code]

        for d in pool:
            self._refresh(d)

        # Sort: non-completed first, then by due_date ascending
        def sort_key(d):
            if d["completed"]:
                return (1, "9999")
            return (0, d.get("due_date") or "9999")

        pool.sort(key=sort_key)
        return pool

    def active_deadlines(self, class_code: Optional[str] = None) -> list[dict]:
        """Return only non-completed, non-overdue deadlines."""
        return [
            d for d in self.all_sorted(class_code)
            if not d["completed"] and d.get("danger") != "OVERDUE"
        ]

    def overdue_deadlines(self, class_code: Optional[str] = None) -> list[dict]:
        """Return deadlines that have passed without completion."""
        return [
            d for d in self.all_sorted(class_code)
            if not d["completed"] and d.get("danger") == "OVERDUE"
        ]

    # ------------------------------------------------------------------
    # 🔥 Advanced Feature 1: Smart Priority Boost
    # ------------------------------------------------------------------

    def priority_boosted(self, class_code: Optional[str] = None) -> list[dict]:
        """
        When multiple deadlines cluster within 48 hours, boost the
        earliest one as 'CRITICAL'. Returns the full sorted list
        with a `priority_boost` flag.
        """
        active = self.active_deadlines(class_code)

        # Find deadlines within next 48 hours
        window_48h = [
            d for d in active
            if d.get("due_date") and remaining_seconds(d["due_date"]) <= 48 * 3600
        ]

        for d in active:
            d["priority_boost"] = False
            d["boost_reason"] = None

        if len(window_48h) >= 2:
            # Boost the earliest one
            window_48h[0]["priority_boost"] = True
            window_48h[0]["boost_reason"] = (
                f"{len(window_48h)} deadlines within 48 hrs — this is the most urgent"
            )

        return self.all_sorted(class_code)

    # ------------------------------------------------------------------
    # 🔥 Advanced Feature 2: Overdue Detection (already in queries above)
    # ------------------------------------------------------------------

    def overdue_history(self, class_code: Optional[str] = None) -> dict:
        """Summary of overdue deadlines for analytics."""
        overdue = self.overdue_deadlines(class_code)
        return {
            "count": len(overdue),
            "deadlines": overdue,
            "subjects_affected": list({d["subject"] for d in overdue}),
        }

    # ------------------------------------------------------------------
    # 🔥 Advanced Feature 3: Stress Analysis
    # ------------------------------------------------------------------

    def stress_score(self, class_code: Optional[str] = None) -> dict:
        """
        Compute a 'stress score' based on deadline density.

        Score bands:
            0-2 deadlines/week  → LOW    (score 0-30)
            3-5 deadlines/week  → MEDIUM (score 31-60)
            6-8 deadlines/week  → HIGH   (score 61-80)
            9+  deadlines/week  → EXTREME(score 81-100)
        """
        now = datetime.now()
        week_end = now + timedelta(days=7)

        active = self.active_deadlines(class_code)
        this_week = [
            d for d in active
            if d.get("due_date")
            and now.isoformat() <= d["due_date"] <= week_end.isoformat()
        ]

        count = len(this_week)
        # Base score based on volume
        if count <= 2:
            score = count * 15
        elif count <= 5:
            score = 30 + (count - 2) * 10
        elif count <= 8:
            score = 60 + (count - 5) * 7
        else:
            score = 80 + (count - 8) * 5

        # Proximity penalty: deadlines within 24h add extra stress
        urgent_count = sum(
            1 for d in this_week
            if d.get("due_date") and remaining_seconds(d["due_date"]) <= 24 * 3600
        )
        score = min(score + urgent_count * 5, 100)

        # Determine level and message based on final score
        if score <= 30:
            level = "LOW"
            message = "Looking manageable! You've got this. 💪"
        elif score <= 60:
            level = "MEDIUM"
            message = "A moderate week ahead. Stay organized! 📋"
        elif score <= 80:
            level = "HIGH"
            message = "Heavy week incoming. Prioritize wisely! ⚡"
        else:
            level = "EXTREME"
            message = "🚨 Overloaded! Consider delegating or rescheduling."

        return {
            "score": score,
            "level": level,
            "message": message,
            "deadlines_this_week": count,
            "urgent_within_24h": urgent_count,
        }

    # ------------------------------------------------------------------
    # 🔥 Advanced Feature 4: Smart Suggestions
    # ------------------------------------------------------------------

    def suggestions(self, class_code: Optional[str] = None) -> list[str]:
        """Generate actionable suggestions based on current deadline state."""
        tips: list[str] = []
        active = self.active_deadlines(class_code)
        overdue = self.overdue_deadlines(class_code)
        stress = self.stress_score(class_code)

        # Cluster warning
        now = datetime.now()
        next_48h = [
            d for d in active
            if d.get("due_date")
            and 0 < remaining_seconds(d["due_date"]) <= 48 * 3600
        ]
        if len(next_48h) >= 3:
            tips.append(
                f"⚠️ You have {len(next_48h)} deadlines in the next 2 days — start early!"
            )
        elif len(next_48h) >= 2:
            tips.append(
                f"📌 {len(next_48h)} deadlines within 48 hours. Plan your time blocks."
            )

        # Overdue nudge
        if overdue:
            tips.append(
                f"🔴 {len(overdue)} overdue deadline(s). Submit or mark complete?"
            )

        # Subject clustering
        subjects = {}
        for d in active:
            s = d.get("subject", "General")
            subjects[s] = subjects.get(s, 0) + 1
        for subj, cnt in subjects.items():
            if cnt >= 3:
                tips.append(
                    f"📚 {cnt} upcoming {subj} tasks — consider a study block."
                )

        # Stress-based
        if stress["level"] == "EXTREME":
            tips.append("🧘 Stress is very high. Take short breaks between tasks.")
        elif stress["level"] == "HIGH":
            tips.append("💡 Try the 2-minute rule: if a task takes <2 min, do it now.")

        # Calm period
        if not active:
            tips.append("🎉 All clear! No pending deadlines. Enjoy the downtime.")

        if not tips:
            tips.append("✅ You're on track. Keep up the great work!")

        return tips

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh(self, d: dict):
        """Recompute live fields on a deadline dict."""
        if not d.get("due_date"):
            return
        d["danger"] = danger_level(d["due_date"])
        d["danger_color"] = danger_color(d["danger"])
        d["time_label"] = smart_time_label(d["due_date"])
        d["countdown"] = remaining_hms(d["due_date"])
