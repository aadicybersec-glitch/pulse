# ⚡ PULSE — Intelligent Deadline Management System

A **Python-driven intelligent system** that parses natural language deadlines, tracks urgency dynamically, triggers time-based alerts, and provides smart analytics for students and teams.

---

## 🧠 Architecture

PULSE is **not** a basic CRUD app. Python handles all the intelligence:

| Module | Responsibility |
|---|---|
| `nlp_parser.py` | Natural language → structured deadline (dateparser + keyword detection) |
| `deadline_engine.py` | Urgency sorting, danger levels, priority boost, stress analysis |
| `time_utils.py` | Countdown math, danger classification, human-friendly formatting |
| `notifier.py` | APScheduler-based alerts at 24h / 3h / 1h before each deadline |
| `db_manager.py` | Firebase Realtime DB with automatic local JSON fallback |
| `class_manager.py` | 6-char class codes for shared deadline pools |
| `app.py` | Thin Flask routing layer — no business logic here |

### Danger Levels

| Time Remaining | Level |
|---|---|
| > 72 hours | 🟢 SAFE |
| 24–72 hours | 🟡 CAUTION |
| 1–24 hours | 🔴 DANGER |
| < 1 hour | 🟣 PANIC |
| Past due | ⚫ OVERDUE |

### Advanced Features

1. **Smart Priority Boost** — When multiple deadlines cluster within 48h, the most urgent is flagged as CRITICAL
2. **Overdue Detection** — Missed deadlines are tracked with subject-level analytics
3. **Stress Analysis** — Weekly deadline density → score (0–100) with level bands
4. **Smart Suggestions** — Context-aware tips like "You have 5 deadlines in 2 days — start early"

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Install

```bash
cd pulse
pip install -r requirements.txt
```

### Run (Development)

```bash
cd backend
python app.py
```

Open **http://localhost:5000** in your browser.

### Run (Production)

```bash
cd backend
gunicorn app:app --bind 0.0.0.0:5000 --workers 2
```

---

## 🔥 Firebase Setup (Optional)

By default PULSE uses a local JSON file (`backend/local_db.json`). To connect Firebase:

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable **Realtime Database**
3. Download your service account key JSON
4. Set environment variables:

```bash
export FIREBASE_CRED_PATH=/path/to/serviceAccountKey.json
export FIREBASE_DB_URL=https://your-project.firebaseio.com
```

5. Restart the server — PULSE auto-detects and connects.

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/add` | Add deadline (NLP-parsed) |
| GET | `/deadlines` | List all deadlines (sorted by urgency) |
| GET | `/deadline/<id>/countdown` | Live countdown for one deadline |
| POST | `/deadline/<id>/complete` | Mark deadline complete |
| DELETE | `/deadline/<id>` | Remove deadline |
| POST | `/class/create` | Create a class room |
| POST | `/join` | Join a class by code |
| GET | `/classes` | List classes |
| GET | `/analytics/stress` | Stress score & analysis |
| GET | `/analytics/suggestions` | Smart suggestions |
| GET | `/analytics/overdue` | Overdue history |
| GET | `/notifications` | Notification log |

### Example: Add a deadline

```bash
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{"input": "Math assignment day after tomorrow 6pm"}'
```

---

## ☁️ Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment:** Python 3
5. Add env vars for Firebase (if using)
6. Deploy!

---

## 📁 Project Structure

```
pulse/
├── backend/
│   ├── app.py              # Flask routes (thin layer)
│   ├── nlp_parser.py        # Natural language → deadline
│   ├── deadline_engine.py   # Core intelligence
│   ├── notifier.py          # Alert scheduler
│   ├── db_manager.py        # Firebase / local persistence
│   ├── class_manager.py     # Class code management
│   └── time_utils.py        # Time math & formatting
├── frontend/
│   ├── index.html           # Dashboard UI
│   ├── styles.css           # Dark theme + glassmorphism
│   └── script.js            # Client-side controller
├── requirements.txt
└── README.md
```

---

## 🧪 Demo Flow

1. **Add deadline** → "Physics exam next Friday 3pm"
2. **NLP parses** → subject: Physics, type: exam, due: (next Friday 15:00)
3. **Engine enriches** → danger level, countdown, priority analysis
4. **Stored in DB** → Firebase or local JSON
5. **Dashboard shows** → card with live countdown, color-coded urgency
6. **Notifications fire** → alerts at 24h, 3h, 1h before
7. **Stress meter** → updates based on weekly deadline density
8. **Suggestions** → "You have 3 deadlines within 48 hours — plan ahead!"

---

Built with 🧠 Python intelligence at the core.
