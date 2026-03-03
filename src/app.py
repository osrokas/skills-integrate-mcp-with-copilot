"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import sqlite3
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

DB_PATH = current_dir / "school.db"

DEFAULT_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS students (
                email TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                student_email TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(activity_id, student_email),
                FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY(student_email) REFERENCES students(email) ON DELETE CASCADE
            );
            """
        )

        count_row = conn.execute("SELECT COUNT(*) AS count FROM activities").fetchone()
        if count_row["count"] == 0:
            for name, details in DEFAULT_ACTIVITIES.items():
                cursor = conn.execute(
                    """
                    INSERT INTO activities (name, description, schedule, max_participants)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, details["description"], details["schedule"], details["max_participants"])
                )
                activity_id = cursor.lastrowid

                for email in details["participants"]:
                    conn.execute(
                        "INSERT OR IGNORE INTO students (email) VALUES (?)",
                        (email,)
                    )
                    conn.execute(
                        """
                        INSERT INTO registrations (activity_id, student_email)
                        VALUES (?, ?)
                        """,
                        (activity_id, email)
                    )


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with get_db_connection() as conn:
        activity_rows = conn.execute(
            """
            SELECT id, name, description, schedule, max_participants
            FROM activities
            ORDER BY name
            """
        ).fetchall()

        registration_rows = conn.execute(
            """
            SELECT r.activity_id, r.student_email
            FROM registrations r
            JOIN activities a ON a.id = r.activity_id
            ORDER BY a.name, r.student_email
            """
        ).fetchall()

    participants_by_activity = {}
    for row in registration_rows:
        participants_by_activity.setdefault(row["activity_id"], []).append(row["student_email"])

    response = {}
    for row in activity_rows:
        response[row["name"]] = {
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": participants_by_activity.get(row["id"], [])
        }

    return response


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with get_db_connection() as conn:
        activity_row = conn.execute(
            "SELECT id FROM activities WHERE name = ?",
            (activity_name,)
        ).fetchone()

        if activity_row is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        activity_id = activity_row["id"]
        existing_registration = conn.execute(
            """
            SELECT 1 FROM registrations
            WHERE activity_id = ? AND student_email = ?
            """,
            (activity_id, email)
        ).fetchone()

        if existing_registration is not None:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

        conn.execute(
            "INSERT OR IGNORE INTO students (email) VALUES (?)",
            (email,)
        )
        conn.execute(
            "INSERT INTO registrations (activity_id, student_email) VALUES (?, ?)",
            (activity_id, email)
        )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with get_db_connection() as conn:
        activity_row = conn.execute(
            "SELECT id FROM activities WHERE name = ?",
            (activity_name,)
        ).fetchone()

        if activity_row is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        activity_id = activity_row["id"]
        existing_registration = conn.execute(
            """
            SELECT 1 FROM registrations
            WHERE activity_id = ? AND student_email = ?
            """,
            (activity_id, email)
        ).fetchone()

        if existing_registration is None:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        conn.execute(
            "DELETE FROM registrations WHERE activity_id = ? AND student_email = ?",
            (activity_id, email)
        )

    return {"message": f"Unregistered {email} from {activity_name}"}
