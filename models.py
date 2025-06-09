"""
Database models and operations for attendance management system.
"""

import sqlite3
import hashlib
import datetime
import secrets
from contextlib import contextmanager
from config import DATABASE_PATH

@contextmanager
def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()

# ---------- Helper functions ----------
def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def parse_datetime(datetime_str):
    if not datetime_str:
        return None
    try:
        return datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

# ---------- Existing Models ----------
class Student:
    @staticmethod
    def get_by_id(student_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            return cursor.fetchone()

    @staticmethod
    def create(username, password, name, email):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO students (username, password, name, email) VALUES (?, ?, ?, ?)",
                    (username, hashed_password, name, email)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

class Attendance:
    @staticmethod
    def mark_attendance(student_id):
        today = datetime.date.today()
        now = datetime.datetime.now()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM attendance WHERE student_id = ? AND date = ?", (student_id, today))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE attendance SET logged_in = 1, login_time = ? WHERE id = ?", (now, existing['id']))
            else:
                cursor.execute("INSERT INTO attendance (student_id, date, logged_in, login_time) VALUES (?, ?, 1, ?)",
                               (student_id, today, now))
            conn.commit()
            return True

    @staticmethod
    def get_attendance_percentage(student_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM attendance WHERE student_id = ?", (student_id,))
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) AS present FROM attendance WHERE student_id = ? AND logged_in = 1", (student_id,))
            present = cursor.fetchone()['present']

            start_date = conn.execute("SELECT MIN(date) as start_date FROM attendance WHERE student_id = ?", (student_id,)).fetchone()['start_date']
            end_date = conn.execute("SELECT MAX(date) as end_date FROM attendance WHERE student_id = ?", (student_id,)).fetchone()['end_date']

            percentage = round((present / total) * 100, 2) if total > 0 else 0

            return {
                "percentage": percentage,
                "present_days": present,
                "total_days": total,
                "start_date": parse_date(start_date),
                "end_date": parse_date(end_date)
            }

    @staticmethod
    def get_attendance_history(student_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, logged_in, login_time
                FROM attendance
                WHERE student_id = ?
                ORDER BY date DESC
            """, (student_id,))
            rows = cursor.fetchall()
            return [
                {
                    "date": row["date"],
                    "logged_in": row["logged_in"],
                    "login_time": parse_datetime(row["login_time"])
                }
                for row in rows
            ]


class Session:
    @staticmethod
    def create(student_id):
        token = secrets.token_hex(16)
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (student_id, session_token, expires_at) VALUES (?, ?, ?)",
                (student_id, token, expires_at)
            )
            conn.commit()
            return token

    @staticmethod
    def validate(token):
        now = datetime.datetime.now()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id FROM sessions WHERE session_token = ? AND expires_at > ?", (token, now))
            result = cursor.fetchone()
            return result['student_id'] if result else None

# ---------- New Models ----------
class Teacher:
    @staticmethod
    def get_by_id(teacher_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
            return cursor.fetchone()

    @staticmethod
    def create(name, email):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO teachers (name, email) VALUES (?, ?)", (name, email))
            conn.commit()

    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teachers")
            return cursor.fetchall()

    @staticmethod
    def create_student(username, password, name, email):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO students (username, password, name, email) VALUES (?, ?, ?, ?)",
                    (username, hashed_password, name, email)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    @staticmethod
    def assign_marks(student_id, subject_id, marks_obtained):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES (?, ?, ?)",
                (student_id, subject_id, marks_obtained)
            )
            conn.commit()

class Subject:
    @staticmethod
    def create(name, teacher_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO subjects (name, teacher_id) VALUES (?, ?)", (name, teacher_id))
            conn.commit()

    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subjects.*, teachers.name as teacher_name FROM subjects JOIN teachers ON subjects.teacher_id = teachers.id")
            return cursor.fetchall()

    @staticmethod
    def get_by_teacher(teacher_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE teacher_id = ?", (teacher_id,))
            return cursor.fetchall()


class Marks:
    @staticmethod
    def add_mark(student_id, subject_id, marks_obtained):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO marks (student_id, subject_id, marks_obtained) VALUES (?, ?, ?)",
                (student_id, subject_id, marks_obtained)
            )
            conn.commit()

    @staticmethod
    def get_student_marks(student_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT marks.*, subjects.name as subject_name 
                   FROM marks JOIN subjects ON marks.subject_id = subjects.id 
                   WHERE student_id = ?""",
                (student_id,)
            )
            return cursor.fetchall()
