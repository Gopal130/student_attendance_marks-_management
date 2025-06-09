#!/usr/bin/env python3
"""
Database initialization script for attendance management system.
Creates tables if they don't exist and populates sample data if tables are empty.
"""

import sqlite3
import hashlib
import datetime
from config import DATABASE_PATH

# --- Password hashing ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Connect to DB ---
with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    # --- Create Tables If Not Exist ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        department TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teachers (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        marks_obtained REAL NOT NULL,
        max_marks REAL NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    # --- Create marks_log table for trigger logging ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marks_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject_id INTEGER,
        marks_obtained REAL,
        inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # TRIGGER
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS log_marks_insert
    AFTER INSERT ON marks
    BEGIN
        INSERT INTO marks_log (student_id, subject_id, marks_obtained)
        VALUES (NEW.student_id, NEW.subject_id, NEW.marks_obtained);
    END;
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date DATE NOT NULL,
        logged_in BOOLEAN DEFAULT 0,
        login_time TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        UNIQUE (student_id, date)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        session_token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')

    # --- Insert Sample Data Only If Table is Empty ---

    # Students
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        students = [
            ('john_doe', hash_password('password123'), 'John Doe', 'john.doe@example.com'),
            ('jane_smith', hash_password('password123'), 'Jane Smith', 'jane.smith@example.com'),
            ('bob_johnson', hash_password('password123'), 'Bob Johnson', 'bob.johnson@example.com'),
            ('alice_williams', hash_password('password123'), 'Alice Williams', 'alice.williams@example.com'),
            ('charlie_brown', hash_password('password123'), 'Charlie Brown', 'charlie.brown@example.com'),
        ]
        cursor.executemany("INSERT INTO students (username, password, name, email) VALUES (?, ?, ?, ?)", students)

    # Teachers
    cursor.execute("SELECT COUNT(*) FROM teachers")
    if cursor.fetchone()[0] == 0:
        teachers = [
            ('Prof. Alan Turing', 'alan@univ.edu', hash_password('turing123'), 'Computer Science'),
            ('Prof. Ada Lovelace', 'ada@univ.edu', hash_password('ada123'), 'Mathematics')
        ]
        cursor.executemany("INSERT INTO teachers (name, email, password, department) VALUES (?, ?, ?, ?)", teachers)

    # Subjects
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        subjects = [
            ('Data Structures', 'CS101', 1),
            ('Discrete Math', 'MA102', 2)
        ]
        cursor.executemany("INSERT INTO subjects (name, code, teacher_id) VALUES (?, ?, ?)", subjects)

    # Marks
    cursor.execute("SELECT COUNT(*) FROM marks")
    if cursor.fetchone()[0] == 0:
        marks = [
            (1, 1, 85, 100),
            (1, 2, 78, 100),
            (2, 1, 88, 100),
            (2, 2, 92, 100)
        ]
        cursor.executemany("INSERT INTO marks (student_id, subject_id, marks_obtained, max_marks) VALUES (?, ?, ?, ?)", marks)

    # Attendance
    cursor.execute("SELECT COUNT(*) FROM attendance")
    if cursor.fetchone()[0] == 0:
        today = datetime.date.today()
        for student_id in range(1, 6):
            for days_ago in range(30):
                date = today - datetime.timedelta(days=days_ago)
                logged_in = 1
                login_time = None
                if date.weekday() >= 5 and days_ago % 3 == 0:
                    logged_in = 0
                elif days_ago % 7 == 0:
                    logged_in = 0
                if logged_in:
                    login_time = datetime.datetime.combine(date, datetime.time(8, (days_ago * 7 + student_id * 11) % 60))
                cursor.execute(
                    "INSERT INTO attendance (student_id, date, logged_in, login_time) VALUES (?, ?, ?, ?)",
                    (student_id, date, logged_in, login_time)
                )

    conn.commit()

print("✅ Database initialized successfully (tables created if needed, and sample data added if missing).")
