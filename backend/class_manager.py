"""
PULSE — Class Manager
======================
Handles class-room codes that allow users to share deadline pools.
"""

import random
import string
from typing import Optional


def _generate_code(length: int = 6) -> str:
    """Generate a random alphanumeric class code (uppercase)."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


class ClassManager:
    """
    Manages classes (groups) with shared deadline pools.

    Each class is:
        {
            "code": "AB3X7Q",
            "name": "CS201 — Data Structures",
            "created_by": "user_id",
            "members": ["user_id", ...],
        }
    """

    def __init__(self):
        self._classes: dict[str, dict] = {}  # code → class dict

    def create_class(self, name: str, created_by: str = "anonymous") -> dict:
        """Create a new class with a unique 6-char code."""
        code = _generate_code()
        while code in self._classes:
            code = _generate_code()

        cls = {
            "code": code,
            "name": name,
            "created_by": created_by,
            "members": [created_by],
        }
        self._classes[code] = cls
        return cls

    def join_class(self, code: str, user_id: str = "anonymous") -> Optional[dict]:
        """Join an existing class by code. Returns the class or None."""
        code = code.upper().strip()
        cls = self._classes.get(code)
        if cls and user_id not in cls["members"]:
            cls["members"].append(user_id)
        return cls

    def get_class(self, code: str) -> Optional[dict]:
        return self._classes.get(code.upper().strip())

    def list_classes(self, user_id: Optional[str] = None) -> list[dict]:
        """List all classes, or only those a user belongs to."""
        if user_id:
            return [
                c for c in self._classes.values() if user_id in c["members"]
            ]
        return list(self._classes.values())

    def leave_class(self, code: str, user_id: str) -> bool:
        cls = self._classes.get(code.upper().strip())
        if cls and user_id in cls["members"]:
            cls["members"].remove(user_id)
            return True
        return False

    def load_all(self, classes: list[dict]):
        """Bulk-load classes from DB."""
        for c in classes:
            self._classes[c["code"]] = c
