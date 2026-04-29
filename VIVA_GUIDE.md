# PULSE Project Viva Guide: The "Heavy" Edition 🚀

This guide is designed to help you handle a deep technical viva. It covers everything from high-level architecture to the "secret sauce" of our NLP implementation.

---

## 1. Project Overview: What is PULSE?
**PULSE** (Personalized Universal Localized Scheduling Engine) is an intelligent deadline management system. Unlike a standard calendar, it uses **Natural Language Processing (NLP)** to turn human-speak (e.g., "Math record due next Friday 6pm") into structured data with real-time urgency tracking.

### Key Value Propositions:
- **Zero-Friction Entry**: No complex forms; just type and go.
- **Collaborative Intelligence**: Class-based deadline pools so one person can update for everyone.
- **Stress Analytics**: Calculates a "Stress Score" based on the volume and proximity of deadlines.

---

## 2. Technical Architecture
We followed a **Decoupled Client-Server Architecture**:

- **Frontend**: Single Page Application (SPA) built with Vanilla HTML5, CSS3 (Modern Glassmorphism), and Asynchronous JavaScript (ES6+).
- **Backend**: Python-based REST API using **Flask**.
- **Intelligence Layer**: Modular Python logic (`nlp_parser.py`, `deadline_engine.py`).
- **Database**: Persistent JSON-based Document Store (`local_db.json`).
- **Scheduling**: Internal threading for notification simulation (`notifier.py`).

---

## 3. The NLP Implementation (The "Heavy" Part) 🧠
The teacher will likely ask: *"How did you implement NLP? Did you use a library or build it yourself?"*

**The Answer:**
We implemented a **Multi-Strategy Hybrid Parser** in `nlp_parser.py`. We didn't just plug in a library; we built a custom engine to handle the specific context of student deadlines.

### The NLP Pipeline:
1.  **Normalization**: Lowercasing and stripping noise words (e.g., "please", "the", "by").
2.  **Strategy 1: Custom Regex Engine**:
    - We use Regular Expressions to catch **Relative Time Patterns**.
    - *Example*: `(\d+)\s+(minute|hour|day)s?` matches "in 2 hours".
    - *Example*: `next\s+(monday|tuesday...)` calculates the exact date of the next occurrence.
3.  **Strategy 2: Keyword Tokenization (Categorization)**:
    - **Subject Detection**: We maintain a dictionary of educational subjects (Math, CS, Physics). If "DSA" is mentioned, the system automatically tags it as "Data Structures".
    - **Task Type Detection**: Keywords like "record", "quiz", "exam" are used to assign a task type, which later influences the priority logic.
4.  **Temporal Resolution**:
    - We resolve fuzzy terms like "morning" (9:00 AM), "evening" (6:00 PM), and "midnight" (11:59 PM) into precise `datetime` objects.
5.  **Validation**: A sanity check ensures deadlines aren't set in the past.

---

## 4. The "Deadline Engine" Logic
This is where the raw data becomes "intelligent."

### Danger Level Calculation:
The system doesn't just show a date; it calculates a **Danger Level** dynamically:
- **CRITICAL**: < 6 hours remaining.
- **HIGH**: < 24 hours remaining.
- **MEDIUM**: < 3 days remaining.
- **LOW**: Everything else.

### Stress Score (The Algorithm):
We calculate the `stress_score` by summing the "weight" of all active deadlines in a class. A "Critical" deadline has a higher weight than a "Low" priority one. This gives a quantitative measure of student workload.

---

## 5. Potential Viva Questions & "Genius" Answers

| Question | The "Genius" Answer |
| :--- | :--- |
| **Why not use a real DB like MySQL or MongoDB?** | "For a lightweight campus tool, **JSON persistence** offers the best performance-to-complexity ratio. It allows for a schema-less structure which is perfect for NLP data where fields might vary. It also ensures zero-configuration for the end-user." |
| **How do you handle multi-user conflicts?** | "We implemented **Class Isolation**. Every user joins a `class_code`. The backend uses this code as a partition key. Deadlines are shared within a class room, but kept private from other classes." |
| **What happens if the NLP fails to parse the date?** | "The `nlp_parser` returns a `parsed_ok: False` flag. The Flask backend catches this and returns a `422 Unprocessable Entity` status code, prompting the user to provide a clearer date format." |
| **Is the system real-time?** | "Yes. We use `setInterval` on the frontend to poll the `/countdown` endpoint for the active deadlines, ensuring the timers and danger levels update every second without page refreshes." |
| **How did you handle timezones?** | "We use Python's `datetime.now()` for server-side calculations and ISO-8601 strings for data exchange, ensuring consistency between the Python backend and the JavaScript frontend." |

---

## 6. Code Walkthrough Highlights (Show these!)

1.  **`nlp_parser.py`**: Show the `_parse_custom` function. Point out the Regex patterns. This shows you understand pattern matching.
2.  **`deadline_engine.py`**: Show the `danger_level` logic. This shows you can implement business rules.
3.  **`app.py`**: Show the `@app.route("/add")`. Explain how it takes raw input, passes it to NLP, then saves it to the DB. This shows you understand the full stack.
4.  **`script.js`**: Show the `fetch()` calls. Explain how you handle the JSON response and dynamically build the HTML cards using template literals.

---

### Pro-Tip for the Viva:
When showing the code, don't just read the lines. Say: *"We modularized the logic so that the NLP engine is completely independent of the web server. This makes the system scalable and easy to test."* (Teachers LOVE the word "Modular").
