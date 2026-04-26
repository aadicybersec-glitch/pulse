"""
PULSE — Flask Application
===========================
Lightweight HTTP interface. All intelligence lives in Python modules;
Flask only routes requests and returns JSON.
"""

import logging
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Module imports (local backend)
# ---------------------------------------------------------------------------
from nlp_parser import parse_deadline
from deadline_engine import DeadlineEngine
from notifier import NotificationScheduler
from db_manager import DBManager
from class_manager import ClassManager
from time_utils import remaining_hms, danger_level

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger("pulse.app")

app = Flask(
    __name__,
    static_folder=str(Path(__file__).parent.parent / "frontend"),
    static_url_path="",
)
CORS(app)

# Core systems
engine = DeadlineEngine()
notifier = NotificationScheduler()
db = DBManager()
class_mgr = ClassManager()

# Boot: load existing data from DB into engine
_existing = db.fetch_deadlines()
engine.load_all(_existing)
for d in _existing:
    notifier.schedule_for_deadline(d)

_existing_classes = db.fetch_classes()
class_mgr.load_all(_existing_classes)

logger.info(f"Loaded {len(_existing)} deadlines, {len(_existing_classes)} classes from DB")


# =========================================================================
# ROUTES
# =========================================================================

# ---- Dashboard (serve frontend) ----------------------------------------

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return send_from_directory(app.static_folder, "index.html")


# ---- Add Deadline -------------------------------------------------------

@app.route("/add", methods=["POST"])
def add_deadline():
    """
    Accepts JSON body:
        { "input": "Math assignment day after tomorrow 6pm",
          "class_code": "AB3X7Q" (optional),
          "user": "user_name" (optional) }
    """
    body = request.get_json(force=True)
    raw_input = body.get("input", "").strip()
    if not raw_input:
        return jsonify({"error": "Missing 'input' field"}), 400

    # 1. NLP parse
    parsed = parse_deadline(raw_input)
    if not parsed["parsed_ok"]:
        return jsonify({
            "error": "Could not parse a date from your input. Try something like: 'Math exam next Friday 3pm'",
            "parsed": parsed,
        }), 422

    # 2. Enrich with class & user info
    class_code = body.get("class_code")
    if not class_code:
        return jsonify({"error": "Please join a class room first to add deadlines!"}), 403

    parsed["class_code"] = class_code
    parsed["created_by"] = body.get("user", "anonymous")

    # 3. Add to engine
    deadline = engine.add(parsed)

    # 4. Persist to DB
    db.push_deadline(deadline)

    # 5. Schedule notifications
    notifier.schedule_for_deadline(deadline)

    logger.info(f"Added deadline: {deadline['title']} → {deadline['due_date']}")
    return jsonify({"ok": True, "deadline": deadline}), 201


# ---- Get Deadlines ------------------------------------------------------

@app.route("/deadlines", methods=["GET"])
def get_deadlines():
    """
    Query params:
        class_code  – filter by class
        boosted     – if "true", include priority boost info
    """
    class_code = request.args.get("class_code")
    boosted = request.args.get("boosted", "false").lower() == "true"

    # Enforce class isolation: if no class_code is provided, return empty list
    if not class_code:
        return jsonify({
            "ok": True,
            "count": 0,
            "deadlines": [],
            "message": "Join a class to see deadlines."
        })

    if boosted:
        deadlines = engine.priority_boosted(class_code)
    else:
        deadlines = engine.all_sorted(class_code)

    return jsonify({
        "ok": True,
        "count": len(deadlines),
        "deadlines": deadlines,
    })


# ---- Single deadline countdown ------------------------------------------

@app.route("/deadline/<deadline_id>/countdown", methods=["GET"])
def countdown(deadline_id):
    d = engine.get(deadline_id)
    if not d:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True, "countdown": d.get("countdown"), "danger": d.get("danger")})


# ---- Complete / Delete ---------------------------------------------------

@app.route("/deadline/<deadline_id>/complete", methods=["POST"])
def complete_deadline(deadline_id):
    d = engine.mark_complete(deadline_id)
    if not d:
        return jsonify({"error": "Not found"}), 404
    db.update_deadline(deadline_id, {"completed": True})
    notifier.cancel_for_deadline(deadline_id)
    return jsonify({"ok": True, "deadline": d})


@app.route("/deadline/<deadline_id>", methods=["DELETE"])
def delete_deadline(deadline_id):
    engine.remove(deadline_id)
    db.delete_deadline(deadline_id)
    notifier.cancel_for_deadline(deadline_id)
    return jsonify({"ok": True})


# ---- Class routes --------------------------------------------------------

@app.route("/class/create", methods=["POST"])
def create_class():
    body = request.get_json(force=True)
    name = body.get("name", "Untitled Class")
    user = body.get("user", "anonymous")
    cls = class_mgr.create_class(name, user)
    db.push_class(cls)
    return jsonify({"ok": True, "class": cls}), 201


@app.route("/join", methods=["POST"])
def join_class():
    body = request.get_json(force=True)
    code = body.get("code", "").strip()
    user = body.get("user", "anonymous")
    if not code:
        return jsonify({"error": "Missing class code"}), 400
    cls = class_mgr.join_class(code, user)
    if not cls:
        return jsonify({"error": "Class not found"}), 404
    db.push_class(cls)  # persist updated members
    return jsonify({"ok": True, "class": cls})


@app.route("/classes", methods=["GET"])
def list_classes():
    user = request.args.get("user")
    return jsonify({"ok": True, "classes": class_mgr.list_classes(user)})


# ---- Analytics -----------------------------------------------------------

@app.route("/analytics/stress", methods=["GET"])
def stress():
    class_code = request.args.get("class_code")
    if not class_code:
        return jsonify({"ok": True, "score": 0, "level": "NONE", "message": "Join a class to see stress analytics."})
    return jsonify({"ok": True, **engine.stress_score(class_code)})


@app.route("/analytics/suggestions", methods=["GET"])
def suggestions():
    class_code = request.args.get("class_code")
    if not class_code:
        return jsonify({"ok": True, "suggestions": ["Join a class room to get smart suggestions."] })
    return jsonify({"ok": True, "suggestions": engine.suggestions(class_code)})


@app.route("/analytics/overdue", methods=["GET"])
def overdue():
    class_code = request.args.get("class_code")
    if not class_code:
        return jsonify({"ok": True, "count": 0, "subjects_affected": [], "message": "No class joined."})
    return jsonify({"ok": True, **engine.overdue_history(class_code)})


# ---- Notifications -------------------------------------------------------

@app.route("/notifications", methods=["GET"])
def notifications():
    limit = int(request.args.get("limit", 50))
    class_code = request.args.get("class_code")
    return jsonify({
        "ok": True,
        "notifications": notifier.get_log(limit, class_code),
        "pending_jobs": notifier.pending_count(),
    })


# =========================================================================
# Run
# =========================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
