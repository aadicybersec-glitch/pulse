# ⚡ PULSE Technical Documentation & Study Guide

Welcome to the technical breakdown of **PULSE**, an intelligent deadline management system. This guide is designed for absolute beginners to understand how a modern Python web application is structured and how its different "organs" work together.

---

## 1. Project Overview
PULSE is more than a "To-Do" list. It is an **Intelligent Agent** that:
- **Understands Human Language:** You don't pick dates from a calendar; you just type "Math homework due Friday at 5 PM."
- **Thinks Ahead:** It calculates "Stress Levels" based on how many deadlines are clustered together.
- **Alerts You:** It knows when you are in "Danger" or "Panic" mode based on time remaining.
- **Collaborates:** It uses "Class Codes" so a whole group of students can see the same deadlines.

---

## 2. The Tech Stack (What tools did we use?)

| Technology | Role | Why we used it |
|---|---|---|
| **Python** | The Brain | Extremely powerful for logic, math, and handling text (NLP). |
| **Flask** | The Messenger | A "Micro-framework" that lets Python talk to the internet (web browser). |
| **Vanilla HTML/CSS/JS** | The Face | Standard web technologies for a beautiful, responsive user interface. |
| **Firebase / JSON** | The Memory | Stores your deadlines so they don't disappear when you close the app. |
| **dateparser** | The Translator | A Python library that converts "tomorrow" into a real computer date. |

---

## 3. Project Structure (Folder Map)

```text
pulse/
├── backend/                # 🧠 THE BRAIN (Python logic)
│   ├── app.py              # The "Entry Point" - Routes web requests.
│   ├── nlp_parser.py       # Natural Language Processing - Interprets your typing.
│   ├── deadline_engine.py  # Business Logic - Sorts, ranks, and analyzes stress.
│   ├── db_manager.py       # Persistence - Saves data to a file or cloud.
│   └── time_utils.py       # Math - Calculates countdowns and danger levels.
├── frontend/               # 🎨 THE FACE (Web interface)
│   ├── index.html          # Structure of the page.
│   ├── styles.css          # Design (Colors, Glassmorphism, Dark mode).
│   └── script.js           # Logic for the browser (UI updates).
└── requirements.txt        # The "Shopping List" of Python libraries to install.
```

---

## 4. How the "Brain" Works (Technical Aspects)

### A. NLP Parsing (`nlp_parser.py`)
When you type "Physics Lab next Monday", Python doesn't naturally know what "next Monday" means.
- **Step 1:** We use a library called `dateparser`.
- **Step 2:** We "clean" the text (remove extra spaces, fix capitalization).
- **Step 3:** The parser converts the text into a **Datetime Object** (a specific format Python understands: `2024-05-20 15:00:00`).

### B. The Deadline Engine (`deadline_engine.py`)
This is the core of the project. It doesn't just store data; it performs **Enrichment**:
- **Sorting:** It keeps deadlines in order of "Most Urgent" to "Least Urgent."
- **Priority Boosting:** If three deadlines are due in the same 48-hour window, it "boosts" their priority because it knows you're busy!
- **Stress Score:** It uses a mathematical formula:
  `Stress = (Number of Deadlines) * (Urgency Multiplier)`
  This gives you a score from 0 to 100 to tell you how "burnt out" you might feel.

### C. Time Mathematics (`time_utils.py`)
Computers measure time in "Seconds since 1970" (Unix Time).
- We subtract `Deadline Time - Current Time`.
- We convert those seconds into `Days : Hours : Minutes`.
- **Danger Levels:**
  - `> 72h`: Green (Safe)
  - `24-72h`: Yellow (Caution)
  - `< 24h`: Red (Danger)
  - `< 1h`: Purple (Panic!)

---

## 5. The "Face" (Frontend Communication)

The Frontend and Backend talk to each other via an **API (Application Programming Interface)**.
1. **The Request:** When you click "Add," the JavaScript in `script.js` sends a "POST" request to the Python server.
2. **The Processing:** Python parses the text, saves it, and calculates the urgency.
3. **The Response:** Python sends back a "JSON" packet (a simple text format for data).
4. **The Update:** JavaScript receives the JSON and dynamically creates a new "Card" on your screen without refreshing the page!

---

## 6. Main Features Explained

1.  **Shared Class Pools:** By using a unique 6-character code (like `XJ92LA`), multiple users can connect to the same "Deadlines Database." This is great for group projects!
2.  **Live Countdowns:** The UI updates every second using a JavaScript `setInterval` function, making the app feel alive.
3.  **Glassmorphism Design:** A modern design trend using `backdrop-filter: blur()` and semi-transparent colors to make the app look like frosted glass.
4.  **Smart Suggestions:** The app looks at your schedule and gives tips like "Focus on Physics first!" based on real-time urgency.

---

## 7. The Code Section Breakdown (The "Organs" of the App)

### 📁 The Backend: "The Inner Workings"
*   **`app.py` (The Receptionist):** This is the entry point. It listens for requests from the web and routes them to the right Python function.
*   **`nlp_parser.py` (The Translator):** Uses the `dateparser` library to turn human sentences (like "next Friday") into computer dates.
*   **`deadline_engine.py` (The Brain):** The "logic center." It sorts deadlines by urgency, calculates stress scores, and assigns danger levels (Green/Yellow/Red).
*   **`db_manager.py` (The Librarian):** Handles "Memory." It saves data to a local file (`local_db.json`) or to the cloud (Firebase).
*   **`time_utils.py` (The Clock):** Contains the math for calculating exactly how many days, hours, and minutes are left until a deadline.

### 📁 The Frontend: "The User Interface"
*   **`index.html` (The Skeleton):** The structure of the website—where buttons and text boxes live.
*   **`styles.css` (The Skin):** The design. It uses "Glassmorphism" (frosted glass effect) and dark mode to make the app look modern.
*   **`script.js` (The Nervous System):** The logic in the browser. it runs the live countdown timers and "talks" to the Python backend using the Fetch API.

---

## 8. How the Code Flows (The "Story" of a Deadline)
1.  **Input:** You type a deadline into the website.
2.  **JavaScript (`script.js`)** sends that text to **Flask (`app.py`)**.
3.  **Flask** asks the **Parser (`nlp_parser.py`)** to figure out the date.
4.  **The Engine (`deadline_engine.py`)** calculates how stressed you should be and how urgent the task is.
5.  **The Librarian (`db_manager.py`)** saves the info so it’s never lost.
6.  **The Website** instantly shows a new colorful card with a live countdown!

---

## 9. Beginner's Python Glossary

If you're new to Python, here are the key concepts we used in this project:

- **Dictionaries (`{}`):** Used to store deadline data (e.g., `{"title": "Math", "due": "Friday"}`).
- **Decorators (`@app.route`):** These "wrap" functions in Flask to tell the computer "Run this function when someone visits the /add page."
- **Modules:** Splitting code into different files (`nlp_parser.py`, etc.) so it's easier to read and manage.
- **f-strings (`f"Hello {name}"`):** A way to easily plug variables into sentences.
- **Lists (`[]`):** Used to hold collections of deadlines.

---

## 10. 📂 The Ultimate File Directory (Every File Explained)

Here is a map of every file in your project and exactly what is inside it:

### 🧠 Backend (The Brain)
*   **`app.py` (The Main Server):** The "Receptionist." It contains all the web "Routes" (like `/add`) and handles how the browser talks to the Python logic.
*   **`nlp_parser.py` (The Interpreter):** Uses the `dateparser` library to understand human language (like "tomorrow") and turn it into a computer date.
*   **`deadline_engine.py` (The Logic Core):** The "Brain." It calculates **Stress Scores**, sorts deadlines, and decides if a task is "SAFE" or "DANGER."
*   **`db_manager.py` (The Data Guard):** Logic to save and load data. It connects to **Firebase** (Cloud) or a local file if you are offline.
*   **`class_manager.py` (The Team Manager):** Manages shared "Class Rooms" and generates 6-character random codes (like `XJ92LA`).
*   **`notifier.py` (The Alert System):** Sets timers that trigger notifications 24h, 3h, and 1h before a deadline using `APScheduler`.
*   **`time_utils.py` (The Math Toolkit):** Small tools that calculate the exact time difference between "Now" and the "Deadline."
*   **`local_db.json` (The Memory):** A text file that stores your data permanently on your hard drive.

### 🎨 Frontend (The Face)
*   **`index.html` (The Structure):** The skeleton—defines where buttons, text boxes, and the "Stress Meter" appear.
*   **`styles.css` (The Design):** The beauty—contains rules for **Glassmorphism**, dark mode, and animations.
*   **`script.js` (The Controller):** The interactivity—updates the countdown timers every second and sends data to the Python backend.
*   **`sw.js` (The Background Worker):** A "Service Worker" that allows the browser to show notifications even if the tab is closed.

### ⚙️ Other Files
*   **`requirements.txt`:** The "Shopping List" of Python libraries (like Flask) needed for the app.
*   **`Procfile`:** Instructions for cloud platforms on how to start the app.
*   **`.gitignore`:** Tells GitHub to ignore private or temporary files.

---

## 11. 🎤 Group Presentation: Pro Tips & Demo Script

If you are presenting this to your class, here is a "cheat sheet" to impress your teachers:

### Technical Highlights (Things to brag about!)
1.  **State Management:** Tell them the app uses a **Centralized Engine**. Instead of having code scattered everywhere, the `DeadlineEngine` is the single source of truth for all data logic.
2.  **Hybrid Database:** Mention that the app is "Resilient." It uses a **Local-First** approach with a Cloud Fallback (Firebase), so it works even if the internet is slow.
3.  **Advanced Sorting:** Mention that we don't just sort by date; we use a **Priority Boost** algorithm that detects "Deadline Clusters" (when too many things are due at once).
4.  **UX Focus:** Point out the **Glassmorphism** and **Real-time Countdowns**. Most student projects use static tables; ours feels like a professional SaaS startup app.

### 🚀 The "Perfect Demo" Script
1.  **Start with the Problem:** "We all hate missing deadlines, and typical To-Do lists are boring and manual."
2.  **Show the Magic (NLP):** Type something like *"Final Project due in 3 days at midnight"* into the input. Click add and watch everyone's face when the computer automatically calculates the exact date and time.
3.  **Explain the Danger:** Point to the Red or Purple card. "The app is telling us we are in 'DANGER' mode. It’s not just a list; it’s an assistant."
4.  **Show the Stress Meter:** "Look at our Stress Score. Because we have multiple deadlines, the engine flagged us as 'HIGH STRESS' and gave us a suggestion to start early."
5.  **Finish with Collaboration:** "Because we use Class Codes, I can share this code with my team, and we all see the same deadlines instantly."

---

**You are now ready to crush your project presentation! Good luck!** 🚀
