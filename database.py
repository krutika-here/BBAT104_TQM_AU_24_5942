"""
Database module for Online Quiz System (BBAT104 - TQM Project).
Uses SQLite3 for local persistence, RBAC user management, security audit logging,
and CRUD operations under Quality Goal Q04 - Improve Security.
"""

import hashlib
import math
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from werkzeug.security import generate_password_hash, check_password_hash

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

    # Ensure user_id column exists in attempts table for relational integrity
    cursor.execute("PRAGMA table_info(attempts)")
    attempt_columns = [col["name"] for col in cursor.fetchall()]
    if "user_id" not in attempt_columns:
        cursor.execute("ALTER TABLE attempts ADD COLUMN user_id INTEGER REFERENCES users(id)")

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

    # --- Q04 Security Tables ---

    # Users Table (RBAC: admin, instructor, student)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('admin', 'instructor', 'student')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Password Resets Table (Secure hashed tokens with 15-minute expiration)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Security Audit Trail Table (Append-only audit logs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        actor_username TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        target_entity TEXT,
        outcome TEXT NOT NULL,
        ip_address TEXT,
        details TEXT
    )
    """)

    conn.commit()

    # Seed default data if quizzes table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM quizzes")
    count = cursor.fetchone()["count"]
    if count == 0:
        seed_sample_data(conn)

    # Seed default RBAC users if users table is empty
    cursor.execute("SELECT COUNT(*) AS count FROM users")
    user_count = cursor.fetchone()["count"]
    if user_count == 0:
        seed_default_users(conn)

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

def seed_default_users(conn):
    """Seed initial accounts for Administrator, Instructor, and Student roles."""
    cursor = conn.cursor()
    default_accounts = [
        ("admin", "admin@tqm.quiz", generate_password_hash("Admin@1234"), "admin"),
        ("instructor", "instructor@tqm.quiz", generate_password_hash("Instructor@1234"), "instructor"),
        ("student", "student@tqm.quiz", generate_password_hash("Student@1234"), "student"),
    ]
    for username, email, pwd_hash, role in default_accounts:
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
        """, (username, email, pwd_hash, role))
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO quizzes (title, description, time_limit_mins, pass_percentage)
        VALUES (?, ?, ?, ?)
        """, (title, description.strip() if isinstance(description, str) else "", time_limit_mins, pass_percentage))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_quiz(quiz_id, title, description, time_limit_mins, pass_percentage):
    title, time_limit_mins, pass_percentage = _validate_quiz_values(
        title, time_limit_mins, pass_percentage
    )
    description = description.strip() if isinstance(description, str) else ""
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

def get_question_by_id(question_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

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
    try:
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
    finally:
        conn.close()

# --- Attempts & Results Operations ---

def save_attempt(student_name, student_roll, quiz_id, score, total_marks, percentage, status, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(attempts)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "user_id" in columns and user_id is not None:
            cursor.execute("""
            INSERT INTO attempts (student_name, student_roll, quiz_id, score, total_marks, percentage, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_name.strip(),
                student_roll.strip().upper(),
                quiz_id,
                score,
                total_marks,
                percentage,
                status,
                user_id
            ))
        else:
            cursor.execute("""
            INSERT INTO attempts (student_name, student_roll, quiz_id, score, total_marks, percentage, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                student_name.strip(),
                student_roll.strip().upper(),
                quiz_id,
                score,
                total_marks,
                percentage,
                status
            ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

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

def get_attempts_by_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, q.title AS quiz_title
    FROM attempts a
    JOIN quizzes q ON a.quiz_id = q.id
    WHERE a.user_id = ?
    ORDER BY a.id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_attempts_by_roll(student_roll):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT a.*, q.title AS quiz_title
    FROM attempts a
    JOIN quizzes q ON a.quiz_id = q.id
    WHERE UPPER(a.student_roll) = ?
    ORDER BY a.id DESC
    """, (student_roll.strip().upper(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Q04 Security: User & RBAC Account Management ---

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_user_inputs(username, email, password, role="student"):
    if not isinstance(username, str) or not USERNAME_REGEX.match(username.strip()):
        raise ValueError("Username must be 3-30 characters long and contain only letters, numbers, and underscores.")
    username = username.strip()

    if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()) or len(email.strip()) > 100:
        raise ValueError("Please provide a valid email address (up to 100 characters).")
    email = email.strip().lower()

    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if role not in {"admin", "instructor", "student"}:
        raise ValueError("Role must be 'admin', 'instructor', or 'student'.")

    return username, email, password, role

def create_user(username, email, password, role="student"):
    username, email, password, role = _validate_user_inputs(username, email, password, role)
    password_hash = generate_password_hash(password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
        """, (username, email, password_hash, role))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            return None
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_username(username):
    if not isinstance(username, str):
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email):
    if not isinstance(email, str):
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def verify_user_credentials(identifier, password):
    if not isinstance(identifier, str) or not isinstance(password, str):
        return None
    identifier = identifier.strip()
    user = get_user_by_username(identifier) or get_user_by_email(identifier)
    if not user:
        return None
    if not user["is_active"]:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None

def update_user_password(user_id, new_password):
    if not isinstance(new_password, str) or len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    password_hash = generate_password_hash(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
        """, (password_hash, user_id))
        conn.commit()
    finally:
        conn.close()

def update_user_role(user_id, new_role):
    if new_role not in {"admin", "instructor", "student"}:
        raise ValueError("Invalid role specified.")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, email, role, is_active, created_at
    FROM users
    ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Q04 Security: Password Reset Lifecycle ---

def create_password_reset_token(email):
    user = get_user_by_email(email)
    if not user or not user["is_active"]:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Invalidate any previously unused tokens for this user
        cursor.execute("UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0", (user["id"],))
        cursor.execute("""
        INSERT INTO password_resets (user_id, token_hash, expires_at, used)
        VALUES (?, ?, ?, 0)
        """, (user["id"], token_hash, expires_at))
        conn.commit()
        return raw_token, user
    finally:
        conn.close()

def verify_password_reset_token(raw_token):
    if not isinstance(raw_token, str) or not raw_token.strip():
        return None
    token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT pr.*, u.username, u.email, u.role, u.is_active
    FROM password_resets pr
    JOIN users u ON pr.user_id = u.id
    WHERE pr.token_hash = ? AND pr.used = 0 AND pr.expires_at >= ?
    """, (token_hash, now_str))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def consume_password_reset_token(raw_token, new_password):
    reset_record = verify_password_reset_token(raw_token)
    if not reset_record:
        return False

    update_user_password(reset_record["user_id"], new_password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset_record["id"],))
        conn.commit()
        return True
    finally:
        conn.close()

# --- Q04 Security: Tamper-Evident Audit Trail ---

def log_audit_event(event_type, actor_username, actor_role, target_entity="", outcome="SUCCESS", ip_address=None, details=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_logs'")
        if not cursor.fetchone():
            return
        cursor.execute("""
        INSERT INTO audit_logs (event_type, actor_username, actor_role, target_entity, outcome, ip_address, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(event_type).strip(),
            str(actor_username).strip() or "anonymous",
            str(actor_role).strip() or "anonymous",
            str(target_entity).strip() if target_entity else "",
            str(outcome).strip(),
            str(ip_address).strip() if ip_address else "",
            str(details).strip() if details else ""
        ))
        conn.commit()
    finally:
        conn.close()

def get_audit_logs(limit=100, offset=0, event_type=None):
    conn = get_connection()
    cursor = conn.cursor()
    if event_type:
        cursor.execute("""
        SELECT * FROM audit_logs
        WHERE event_type = ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """, (event_type, int(limit), int(offset)))
    else:
        cursor.execute("""
        SELECT * FROM audit_logs
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """, (int(limit), int(offset)))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Defect Logs (TQM Requirement) ---

def log_defect(category, description, severity="Medium", status="Open"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO defect_logs (category, description, severity, status)
        VALUES (?, ?, ?, ?)
        """, (category, description, severity, status))
        conn.commit()
    finally:
        conn.close()

def get_all_defects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM defect_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
