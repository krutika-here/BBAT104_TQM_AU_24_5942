"""
Database module for Online Quiz System (BBAT104 - TQM Project).
Uses SQLite3 for local persistence and CRUD operations.
"""

import math
import os
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_system.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Quizzes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL UNIQUE,
        description TEXT,
        time_limit_mins INTEGER DEFAULT 10,
        pass_percentage REAL DEFAULT 50.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Questions table (CRUD)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL, -- 'A', 'B', 'C', or 'D'
        marks INTEGER DEFAULT 1,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
    )
    """)

    # Student Quiz Attempts / Results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        student_roll TEXT NOT NULL,
        quiz_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total_marks INTEGER NOT NULL,
        percentage REAL NOT NULL,
        status TEXT NOT NULL, -- 'Passed' or 'Failed'
        completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
    )
    """)

    # TQM Defect Log & Audit Table (For TQM Quality Metrics & Checksheets)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS defect_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL, -- 'Low', 'Medium', 'High', 'Critical'
        status TEXT DEFAULT 'Open', -- 'Open', 'In Progress', 'Resolved'
        logged_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Seed default data if quizzes table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM quizzes")
    count = cursor.fetchone()["count"]
    if count == 0:
        seed_sample_data(conn)

    conn.close()

def seed_sample_data(conn):
    cursor = conn.cursor()

    # Insert sample TQM quiz
    cursor.execute("""
    INSERT INTO quizzes (title, description, time_limit_mins, pass_percentage)
    VALUES (?, ?, ?, ?)
    """, (
        "BBAT104: Fundamentals of TQM",
        "Covers core TQM principles, Deming PDCA cycle, Six Sigma, and SQC tools.",
        10,
        50.0
    ))
    tqm_quiz_id = cursor.lastrowid

    # Insert sample questions for TQM quiz
    tqm_questions = [
        (
            tqm_quiz_id,
            "What does TQM stand for?",
            "Total Quality Management",
            "Technical Quality Measurement",
            "Team Quality Method",
            "Time Quality Metric",
            "A",
            1
        ),
        (
            tqm_quiz_id,
            "Which of the following is NOT one of the steps in the PDCA cycle?",
            "Plan",
            "Do",
            "Cancel",
            "Act",
            "C",
            1
        ),
        (
            tqm_quiz_id,
            "The 80/20 rule is primarily associated with which SQC tool?",
            "Ishikawa Fishbone Diagram",
            "Pareto Chart",
            "Control Chart",
            "Scatter Diagram",
            "B",
            1
        ),
        (
            tqm_quiz_id,
            "In TQM, the Japanese term 'Kaizen' refers to:",
            "Waste reduction",
            "Poka-Yoke error proofing",
            "Continuous Improvement",
            "Just-In-Time delivery",
            "C",
            1
        ),
        (
            tqm_quiz_id,
            "What does RPN stand for in Failure Mode and Effects Analysis (FMEA)?",
            "Risk Priority Number",
            "Root Process Notification",
            "Reliability Performance Notation",
            "Rate of Potential Neglect",
            "A",
            1
        )
    ]

    cursor.executemany("""
    INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, marks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, tqm_questions)

    # Insert sample Python Basics quiz
    cursor.execute("""
    INSERT INTO quizzes (title, description, time_limit_mins, pass_percentage)
    VALUES (?, ?, ?, ?)
    """, (
        "Python Programming Basics",
        "Assessment of Python syntax, data types, and functions.",
        5,
        60.0
    ))
    py_quiz_id = cursor.lastrowid

    py_questions = [
        (
            py_quiz_id,
            "Which keyword is used to define a function in Python?",
            "func",
            "define",
            "def",
            "function",
            "C",
            1
        ),
        (
            py_quiz_id,
            "Which data type is immutable in Python?",
            "List",
            "Dictionary",
            "Set",
            "Tuple",
            "D",
            1
        ),
        (
            py_quiz_id,
            "What is the output of print(type([]))?",
            "<class 'tuple'>",
            "<class 'list'>",
            "<class 'dict'>",
            "<class 'array'>",
            "B",
            1
        )
    ]

    cursor.executemany("""
    INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, marks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, py_questions)

    # Insert sample TQM Defect Log entry (Demonstrating continuous quality tracking)
    cursor.execute("""
    INSERT INTO defect_logs (category, description, severity, status)
    VALUES (?, ?, ?, ?)
    """, ("Input Validation", "Empty student roll number submission caught by Poka-Yoke rule", "Low", "Resolved"))

    conn.commit()

# --- Quiz CRUD Operations ---

def _required_text(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def _positive_integer(value, field_name):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a positive whole number.") from None

    if not number.is_finite() or number != number.to_integral_value() or number <= 0:
        raise ValueError(f"{field_name} must be a positive whole number.")
    return int(number)


def _validate_quiz_values(title, time_limit_mins, pass_percentage):
    title = _required_text(title, "Quiz title")
    time_limit_mins = _positive_integer(time_limit_mins, "Time limit")
    try:
        pass_percentage = float(pass_percentage)
    except (TypeError, ValueError):
        raise ValueError("Pass percentage must be between 0 and 100.") from None
    if not math.isfinite(pass_percentage) or not 0 <= pass_percentage <= 100:
        raise ValueError("Pass percentage must be between 0 and 100.")
    return title, time_limit_mins, pass_percentage


def _validate_question_values(text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks):
    question_text = _required_text(text, "Question text")
    options = (
        _required_text(opt_a, "Option A"),
        _required_text(opt_b, "Option B"),
        _required_text(opt_c, "Option C"),
        _required_text(opt_d, "Option D"),
    )
    if (
        not isinstance(correct_opt, str)
        or correct_opt.strip().upper() not in {"A", "B", "C", "D"}
    ):
        raise ValueError("Correct option must be A, B, C, or D.")
    correct_opt = correct_opt.strip().upper()
    marks = _positive_integer(marks, "Marks")
    return (question_text, *options, correct_opt, marks)


def get_all_quizzes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT q.*, COUNT(ques.id) AS question_count
    FROM quizzes q
    LEFT JOIN questions ques ON q.id = ques.quiz_id
    GROUP BY q.id
    ORDER BY q.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_quiz_by_id(quiz_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_quiz(title, description, time_limit_mins=10, pass_percentage=50.0):
    title, time_limit_mins, pass_percentage = _validate_quiz_values(
        title, time_limit_mins, pass_percentage
    )
    description = "" if description is None else description
    if not isinstance(description, str):
        raise ValueError("Quiz description must be text.")
    description = description.strip()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO quizzes (title, description, time_limit_mins, pass_percentage)
        VALUES (?, ?, ?, ?)
        """, (title, description, time_limit_mins, pass_percentage))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_quiz(quiz_id, title, description, time_limit_mins, pass_percentage):
    title, time_limit_mins, pass_percentage = _validate_quiz_values(
        title, time_limit_mins, pass_percentage
    )
    description = "" if description is None else description
    if not isinstance(description, str):
        raise ValueError("Quiz description must be text.")
    description = description.strip()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE quizzes
        SET title = ?, description = ?, time_limit_mins = ?, pass_percentage = ?
        WHERE id = ?
        """, (title, description, time_limit_mins, pass_percentage, quiz_id))
        conn.commit()
    finally:
        conn.close()

def delete_quiz(quiz_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("SELECT 1 FROM attempts WHERE quiz_id = ? LIMIT 1", (quiz_id,))
        if cursor.fetchone():
            raise ValueError("Cannot delete a quiz that has recorded student attempts.")
        cursor.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
        cursor.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
        conn.commit()
    finally:
        conn.close()

# --- Question CRUD Operations ---

def get_questions_by_quiz(quiz_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id ASC", (quiz_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_question(quiz_id, text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks=1):
    question_values = _validate_question_values(
        text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks
    )
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, *question_values))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_question(question_id, text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks=1):
    question_values = _validate_question_values(
        text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks
    )
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE questions
        SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?, marks = ?
        WHERE id = ?
        """, (*question_values, question_id))
        conn.commit()
    finally:
        conn.close()

def delete_question(question_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

# --- Attempts & Results Operations ---

def save_attempt(student_name, student_roll, quiz_id, score, total_marks, percentage, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO attempts (student_name, student_roll, quiz_id, score, total_marks, percentage, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_name.strip(), student_roll.strip().upper(), quiz_id, score, total_marks, percentage, status))
    conn.commit()
    attempt_id = cursor.lastrowid
    conn.close()
    return attempt_id

def get_all_attempts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, q.title AS quiz_title
    FROM attempts a
    JOIN quizzes q ON a.quiz_id = q.id
    ORDER BY a.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Defect Logs (TQM Requirement) ---

def log_defect(category, description, severity="Medium", status="Open"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO defect_logs (category, description, severity, status)
    VALUES (?, ?, ?, ?)
    """, (category, description, severity, status))
    conn.commit()
    conn.close()

def get_all_defects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM defect_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
