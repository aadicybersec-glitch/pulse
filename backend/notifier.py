"""
PULSE — Notification Scheduler
================================
Schedules and triggers alerts at 24h, 3h, and 1h before each deadline.
Uses APScheduler with a background thread pool.
"""

import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger("pulse.notifier")
logger.setLevel(logging.INFO)

# In-memory notification log (most recent 200)
_notification_log: list[dict] = []
MAX_LOG_SIZE = 200


def _default_handler(notification: dict):
    """Default notification handler — logs to console and stores in memory."""
    _notification_log.append(notification)
    if len(_notification_log) > MAX_LOG_SIZE:
        _notification_log.pop(0)

    emoji = {"24h": "🔔", "3h": "⚠️", "1h": "🚨"}.get(notification["alert_type"], "📢")
    logger.info(
        f"{emoji} NOTIFICATION [{notification['alert_type']}]: "
        f"{notification['title']} — due {notification['due_date']}"
    )


class NotificationScheduler:
    """
    For each deadline, schedules up to 3 alerts:
        • 24 hours before
        •  3 hours before
        •  1 hour  before

    Notifications are stored in-memory and served via API.
    A custom `on_notify` callback can be supplied for external integrations.
    """

    ALERT_OFFSETS = {
        "24h": timedelta(hours=24),
        "3h": timedelta(hours=3),
        "1h": timedelta(hours=1),
    }

    def __init__(self, on_notify: Optional[Callable] = None):
        self._scheduler = BackgroundScheduler(daemon=True)
        self._on_notify = on_notify or _default_handler
        self._scheduled_ids: set[str] = set()
        self._scheduler.start()
        logger.info("NotificationScheduler started")

    def schedule_for_deadline(self, deadline: dict):
        """
        Schedule alerts for a single deadline.
        Skips alerts whose trigger time is already in the past.
        """
        due_str = deadline.get("due_date")
        if not due_str:
            return

        due_dt = datetime.fromisoformat(due_str)
        did = deadline["id"]

        for alert_type, offset in self.ALERT_OFFSETS.items():
            job_id = f"{did}_{alert_type}"

            if job_id in self._scheduled_ids:
                continue  # already scheduled

            trigger_time = due_dt - offset
            if trigger_time <= datetime.now():
                # Alert time already passed — fire immediately if deadline still active
                if due_dt > datetime.now():
                    self._fire_now(deadline, alert_type)
                self._scheduled_ids.add(job_id)
                continue

            self._scheduler.add_job(
                func=self._fire,
                trigger=DateTrigger(run_date=trigger_time),
                args=[deadline, alert_type],
                id=job_id,
                replace_existing=True,
            )
            self._scheduled_ids.add(job_id)
            logger.info(
                f"Scheduled {alert_type} alert for '{deadline['title']}' at {trigger_time}"
            )

    def cancel_for_deadline(self, deadline_id: str):
        """Remove all scheduled alerts for a deadline."""
        for alert_type in self.ALERT_OFFSETS:
            job_id = f"{deadline_id}_{alert_type}"
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
            self._scheduled_ids.discard(job_id)

    def get_log(self, limit: int = 50, class_code: Optional[str] = None) -> list[dict]:
        """Return recent notifications, newest first, optionally filtered by class."""
        log = _notification_log
        if class_code:
            log = [n for n in log if n.get("class_code") == class_code]
        return list(reversed(log[-limit:]))

    def pending_count(self) -> int:
        """Return number of jobs currently scheduled."""
        return len(self._scheduler.get_jobs())

    def shutdown(self):
        self._scheduler.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire(self, deadline: dict, alert_type: str):
        notification = self._build_notification(deadline, alert_type)
        self._on_notify(notification)

    def _fire_now(self, deadline: dict, alert_type: str):
        notification = self._build_notification(deadline, alert_type)
        notification["immediate"] = True
        self._on_notify(notification)

    @staticmethod
    def _build_notification(deadline: dict, alert_type: str) -> dict:
        messages = {
            "24h": f"📅 '{deadline['title']}' is due in 24 hours!",
            "3h": f"⏰ '{deadline['title']}' is due in 3 hours!",
            "1h": f"🚨 URGENT: '{deadline['title']}' is due in 1 hour!",
        }
        return {
            "deadline_id": deadline["id"],
            "title": deadline["title"],
            "subject": deadline.get("subject", ""),
            "due_date": deadline.get("due_date", ""),
            "alert_type": alert_type,
            "class_code": deadline.get("class_code"),
            "message": messages.get(alert_type, "Deadline approaching!"),
            "timestamp": datetime.now().isoformat() + "Z",
            "immediate": False,
        }
