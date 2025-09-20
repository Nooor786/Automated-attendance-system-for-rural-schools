# db.py
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("attendance.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT,
        metadata TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        name TEXT,
        timestamp TEXT,
        method TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_student(student_id: str, name: str, metadata: str = ""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO students(student_id, name, metadata) VALUES (?, ?, ?)",
              (student_id, name, metadata))
    conn.commit()
    conn.close()

def get_students():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT student_id, name FROM students")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_attendance(student_id: str, name: str, method: str = "face"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.now().isoformat(timespec='seconds')
    c.execute("INSERT INTO attendance(student_id, name, timestamp, method) VALUES (?, ?, ?, ?)",
              (student_id, name, ts, method))
    conn.commit()
    conn.close()

def fetch_attendance(start_date=None, end_date=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = "SELECT student_id, name, timestamp, method FROM attendance"
    params = []
    if start_date and end_date:
        q += " WHERE date(timestamp) BETWEEN date(?) AND date(?)"
        params = [start_date, end_date]
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
