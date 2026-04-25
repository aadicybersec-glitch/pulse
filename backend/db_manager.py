"""
PULSE — Database Manager
==========================
Abstraction layer over Firebase Realtime Database.
Falls back to a local JSON file when Firebase credentials are unavailable,
allowing the system to run in development without cloud setup.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pulse.db")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Try to import Firebase
# ---------------------------------------------------------------------------
_firebase_available = False
try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db
    _firebase_available = True
except ImportError:
    logger.warning("firebase-admin not installed — using local JSON fallback")


# ---------------------------------------------------------------------------
# Local JSON fallback
# ---------------------------------------------------------------------------
LOCAL_DB_PATH = Path(__file__).parent / "local_db.json"


def _load_local() -> dict:
    if LOCAL_DB_PATH.exists():
        try:
            with open(LOCAL_DB_PATH, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            if "deadlines" not in data or not isinstance(data["deadlines"], dict):
                data["deadlines"] = {}
            if "classes" not in data or not isinstance(data["classes"], dict):
                data["classes"] = {}
            return data
        except Exception:
            pass
    return {"deadlines": {}, "classes": {}}


def _save_local(data: dict):
    with open(LOCAL_DB_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# DB Manager
# ---------------------------------------------------------------------------
class DBManager:
    """
    Unified interface for deadline & class persistence.

    Usage:
        db = DBManager()                           # local fallback
        db = DBManager(cred_path="serviceKey.json",
                       database_url="https://xxx.firebaseio.com")
    """

    def __init__(
        self,
        cred_path: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        self._use_firebase = False

        cred_path = cred_path or os.environ.get("FIREBASE_CRED_PATH")
        database_url = database_url or os.environ.get("FIREBASE_DB_URL")

        if _firebase_available and cred_path and database_url:
            try:
                if not firebase_admin._apps:
                    if cred_path.strip().startswith("{"):
                        cred = credentials.Certificate(json.loads(cred_path))
                    else:
                        cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {
                        "databaseURL": database_url
                    })
                self._use_firebase = True
                logger.info("Connected to Firebase Realtime Database")
            except Exception as e:
                logger.error(f"Firebase init failed: {e}. Using local fallback.")
        else:
            logger.info("Using local JSON database (set FIREBASE_CRED_PATH & FIREBASE_DB_URL for cloud)")

    # ------------------------------------------------------------------
    # Deadlines
    # ------------------------------------------------------------------

    def push_deadline(self, deadline: dict) -> str:
        """Save a deadline. Returns the ID."""
        did = deadline["id"]
        if self._use_firebase:
            ref = firebase_db.reference(f"/deadlines/{did}")
            ref.set(deadline)
        else:
            data = _load_local()
            data["deadlines"][did] = deadline
            _save_local(data)
        return did

    def fetch_deadlines(self, class_code: Optional[str] = None) -> list[dict]:
        """Fetch all deadlines, optionally filtered by class code."""
        if self._use_firebase:
            ref = firebase_db.reference("/deadlines")
            raw = ref.get() or {}
        else:
            raw = _load_local().get("deadlines", {})

        deadlines = list(raw.values()) if isinstance(raw, dict) else raw
        # Filter out potential None values from Firebase arrays
        deadlines = [d for d in deadlines if d]
        if class_code:
            deadlines = [d for d in deadlines if d.get("class_code") == class_code]
        return deadlines

    def delete_deadline(self, deadline_id: str) -> bool:
        if self._use_firebase:
            ref = firebase_db.reference(f"/deadlines/{deadline_id}")
            ref.delete()
        else:
            data = _load_local()
            if deadline_id in data["deadlines"]:
                del data["deadlines"][deadline_id]
                _save_local(data)
        return True

    def update_deadline(self, deadline_id: str, updates: dict):
        if self._use_firebase:
            ref = firebase_db.reference(f"/deadlines/{deadline_id}")
            ref.update(updates)
        else:
            data = _load_local()
            if deadline_id in data["deadlines"]:
                data["deadlines"][deadline_id].update(updates)
                _save_local(data)

    # ------------------------------------------------------------------
    # Classes
    # ------------------------------------------------------------------

    def push_class(self, cls: dict) -> str:
        code = cls["code"]
        if self._use_firebase:
            ref = firebase_db.reference(f"/classes/{code}")
            ref.set(cls)
        else:
            data = _load_local()
            data["classes"][code] = cls
            _save_local(data)
        return code

    def fetch_classes(self) -> list[dict]:
        if self._use_firebase:
            ref = firebase_db.reference("/classes")
            raw = ref.get() or {}
        else:
            raw = _load_local().get("classes", {})
        classes = list(raw.values()) if isinstance(raw, dict) else raw
        return [c for c in classes if c]

    def fetch_class(self, code: str) -> Optional[dict]:
        if self._use_firebase:
            ref = firebase_db.reference(f"/classes/{code}")
            return ref.get()
        else:
            return _load_local().get("classes", {}).get(code)
