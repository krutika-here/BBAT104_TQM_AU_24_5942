"""
Online Quiz System - Flask Web Application
Course: BBAT104 - Fundamentals of Total Quality Management
Roll Number: 39 | Registration: AU-24-5942 | Academic Session 2026-27
Assigned Quality Goal: Q04 - Improve Security
Evaluation Scope: Review 1 & Review 2 (Base System & CRUD + 5 Security Features)
"""

import os
import secrets
import sqlite3
import threading
import time
from collections import OrderedDict
from functools import wraps
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

import database

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production" or os.environ.get("HTTPS") == "on"

_SUBMISSION_LOCK = threading.Lock()
_SUBMITTED_ATTEMPTS = OrderedDict()
_MAX_REMEMBERED_SUBMISSIONS = 1000

# Initialize database schema and seeds on startup
database.init_db()


# --- Security & Anti-CSRF Helpers ---

class CSRFTokenStr(str):
    """String subclass that is also callable to support both {{ csrf_token }} and {{ csrf_token() }} in templates."""
    def __call__(self):
        return str(self)

def get_csrf_token():
    """Generate or retrieve a cryptographically secure CSRF synchronizer token."""
    token = session.get("csrf_token") or session.get("attempt_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
        session["attempt_csrf_token"] = token
    return CSRFTokenStr(token)

def get_attempt_csrf_token():
    return get_csrf_token()

def verify_csrf(token):
    """Validate incoming token against session-stored CSRF token."""
    expected = session.get("csrf_token") or session.get("attempt_csrf_token")
    return bool(expected and token and secrets.compare_digest(str(token), str(expected)))


@app.context_processor
def inject_template_globals():
    """Inject current authenticated user and CSRF generator into all Jinja2 templates."""
    current_user = None
    user_id = session.get("user_id")
    if user_id:
        current_user = database.get_user_by_id(user_id)
    return {
        "current_user": current_user,
        "csrf_token": get_csrf_token,
    }


@app.after_request
def add_security_headers(response):
    """Apply defensive HTTP security headers to all responses."""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# --- Role-Based Access Control (RBAC) Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                database.log_audit_event(
                    event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
                    actor_username=session.get("username", "anonymous"),
                    actor_role=user_role or "unknown",
                    target_entity=request.path,
                    outcome="BLOCKED",
                    ip_address=request.remote_addr,
                    details=f"Required roles: {allowed_roles}, User role: {user_role}"
                )
                return render_template("forbidden.html", message="Your account role does not have authorization to access this administrative resource."), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- Authentication & Account Management Routes (Q04 Feature 1) ---

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate user with username/email and password, enforcing RBAC."""
    next_url = request.args.get("next") or request.form.get("next")
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template("login.html", error="Please enter both username/email and password.", identifier=identifier, next_url=next_url), 400

        user = database.verify_user_credentials(identifier, password)
        if not user:
            database.log_audit_event(
                event_type="AUTH_LOGIN_FAILURE",
                actor_username=identifier,
                actor_role="anonymous",
                target_entity="auth/login",
                outcome="FAILURE",
                ip_address=request.remote_addr,
                details="Invalid credentials or inactive account"
            )
            return render_template("login.html", error="Invalid username/email or password.", identifier=identifier, next_url=next_url), 401

        # Session Fixation Defense: regenerate session
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        session["attempt_csrf_token"] = session["csrf_token"]

        database.log_audit_event(
            event_type="AUTH_LOGIN_SUCCESS",
            actor_username=user["username"],
            actor_role=user["role"],
            target_entity="auth/login",
            outcome="SUCCESS",
            ip_address=request.remote_addr
        )

        flash(f"Welcome back, {user['username']}! Signed in successfully.", "success")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        if user["role"] in {"admin", "instructor"}:
            return redirect(url_for("quizzes_manage"))
        return redirect(url_for("quizzes"))

    return render_template("login.html", next_url=next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Self-registration for student accounts (prevents self-assignment of admin role)."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.", username=username, email=email), 400

        try:
            user_id = database.create_user(username, email, password, role="student")
            database.log_audit_event(
                event_type="AUTH_REGISTER_SUCCESS",
                actor_username=username,
                actor_role="student",
                target_entity=f"user:{user_id}",
                outcome="SUCCESS",
                ip_address=request.remote_addr
            )
            flash("Account registered successfully! Please sign in with your credentials.", "success")
            return redirect(url_for("login"))
        except ValueError as err:
            return render_template("register.html", error=str(err), username=username, email=email), 400
        except sqlite3.IntegrityError:
            return render_template("register.html", error="A user with that username or email already exists.", username=username, email=email), 409

    return render_template("register.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Invalidate active user session and record audit event."""
    username = session.get("username", "anonymous")
    role = session.get("role", "anonymous")
    database.log_audit_event(
        event_type="AUTH_LOGOUT",
        actor_username=username,
        actor_role=role,
        target_entity="auth/logout",
        outcome="SUCCESS",
        ip_address=request.remote_addr
    )
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("index"))


# --- Password Reset Workflow (Q04 Feature 2) ---

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Request password reset token with user enumeration defense."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        email = request.form.get("email", "").strip()
        if not email:
            return render_template("forgot_password.html", error="Please enter your email address."), 400

        result = database.create_password_reset_token(email)
        if result:
            raw_token, user = result
            database.log_audit_event(
                event_type="PASSWORD_RESET_REQUESTED",
                actor_username=user["username"],
                actor_role=user["role"],
                target_entity=f"user:{user['id']}",
                outcome="SUCCESS",
                ip_address=request.remote_addr
            )
            reset_link = url_for("reset_password", token=raw_token, _external=True)
            return render_template(
                "forgot_password.html",
                message="If an account with that email exists, reset instructions have been generated.",
                reset_link=reset_link,
                email=email
            )
        else:
            database.log_audit_event(
                event_type="PASSWORD_RESET_REQUESTED",
                actor_username=email,
                actor_role="anonymous",
                target_entity="auth/reset",
                outcome="FAILURE",
                ip_address=request.remote_addr,
                details="Unregistered or inactive email"
            )
            return render_template(
                "forgot_password.html",
                message="If an account with that email exists, reset instructions have been generated.",
                email=email
            )

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Verify single-use reset token and update password."""
    reset_record = database.verify_password_reset_token(token)
    if not reset_record:
        database.log_audit_event(
            event_type="PASSWORD_RESET_INVALID",
            actor_username="unknown",
            actor_role="anonymous",
            target_entity="auth/reset",
            outcome="BLOCKED",
            ip_address=request.remote_addr,
            details="Expired, used, or malformed token"
        )
        flash("The password reset token is invalid, expired, or has already been used.", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not verify_csrf(csrf):
            abort(400, description="Invalid or missing CSRF token.")

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            return render_template(
                "reset_password.html",
                token=token,
                reset_record=reset_record,
                error="Passwords do not match."
            ), 400

        try:
            success = database.consume_password_reset_token(token, new_password)
            if success:
                database.log_audit_event(
                    event_type="PASSWORD_RESET_COMPLETED",
                    actor_username=reset_record["username"],
                    actor_role=reset_record["role"],
                    target_entity=f"user:{reset_record['user_id']}",
                    outcome="SUCCESS",
                    ip_address=request.remote_addr
                )
                flash("Your password has been reset successfully! Please sign in with your new password.", "success")
                return redirect(url_for("login"))
            else:
                return render_template(
                    "reset_password.html",
                    token=token,
                    reset_record=reset_record,
                    error="Unable to reset password. The token may have expired or been consumed."
                ), 400
        except ValueError as err:
            return render_template(
                "reset_password.html",
                token=token,
                reset_record=reset_record,
                error=str(err)
            ), 400

    return render_template("reset_password.html", token=token, reset_record=reset_record)


# --- Quiz Management CRUD Routes (Review 2 Base System) ---

@app.route("/quizzes/manage")
@role_required("admin", "instructor")
def quizzes_manage():
    """List quizzes with administrative CRUD management actions."""
    return render_template("quiz_manage.html", quizzes=database.get_all_quizzes())


@app.route("/quizzes/create", methods=["GET", "POST"])
@role_required("admin", "instructor")
def quiz_create():
    """Create a new quiz record."""
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        title = request.form.get("title", "")
        description = request.form.get("description", "")
        time_limit_mins = request.form.get("time_limit_mins", "")
        pass_percentage = request.form.get("pass_percentage", "")

        try:
            quiz_id = database.create_quiz(title, description, time_limit_mins, pass_percentage)
            database.log_audit_event(
                event_type="QUIZ_CREATED",
                actor_username=session.get("username", "staff"),
                actor_role=session.get("role", "staff"),
                target_entity=f"quiz:{quiz_id}",
                outcome="SUCCESS",
                ip_address=request.remote_addr,
                details=f"Title: {title}"
            )
            flash("Quiz created successfully!", "success")
            return redirect(url_for("quizzes_manage"))
        except (ValueError, sqlite3.IntegrityError) as err:
            return render_template(
                "quiz_form.html",
                error=str(err),
                title=title,
                description=description,
                time_limit_mins=time_limit_mins,
                pass_percentage=pass_percentage
            ), 400

    return render_template("quiz_form.html")


@app.route("/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
@role_required("admin", "instructor")
def quiz_edit(quiz_id):
    """Update quiz metadata."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        title = request.form.get("title", "")
        description = request.form.get("description", "")
        time_limit_mins = request.form.get("time_limit_mins", "")
        pass_percentage = request.form.get("pass_percentage", "")

        try:
            database.update_quiz(quiz_id, title, description, time_limit_mins, pass_percentage)
            database.log_audit_event(
                event_type="QUIZ_UPDATED",
                actor_username=session.get("username", "staff"),
                actor_role=session.get("role", "staff"),
                target_entity=f"quiz:{quiz_id}",
                outcome="SUCCESS",
                ip_address=request.remote_addr,
                details=f"Title: {title}"
            )
            flash("Quiz updated successfully!", "success")
            return redirect(url_for("quizzes_manage"))
        except (ValueError, sqlite3.IntegrityError) as err:
            return render_template(
                "quiz_form.html",
                quiz=quiz,
                error=str(err)
            ), 400

    return render_template("quiz_form.html", quiz=quiz)


@app.route("/quizzes/<int:quiz_id>/delete", methods=["POST"])
@role_required("admin", "instructor")
def quiz_delete(quiz_id):
    """Delete a quiz using integrity-preserving cascade."""
    token = request.form.get("csrf_token")
    if not verify_csrf(token):
        abort(400, description="Invalid or missing CSRF token.")

    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    try:
        database.delete_quiz(quiz_id)
        database.log_audit_event(
            event_type="QUIZ_DELETED",
            actor_username=session.get("username", "staff"),
            actor_role=session.get("role", "staff"),
            target_entity=f"quiz:{quiz_id}",
            outcome="SUCCESS",
            ip_address=request.remote_addr,
            details=f"Deleted quiz: {quiz['title']}"
        )
        flash(f"Quiz '{quiz['title']}' deleted successfully.", "success")
    except ValueError as err:
        flash(str(err), "danger")

    return redirect(url_for("quizzes_manage"))


# --- Question & Answer CRUD Routes (Review 2 Base System) ---

@app.route("/quizzes/<int:quiz_id>/questions")
@role_required("admin", "instructor")
def quiz_questions_manage(quiz_id):
    """List questions for a designated quiz with answer keys visible to instructors."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    questions = database.get_questions_by_quiz(quiz_id)
    return render_template("question_manage.html", quiz=quiz, questions=questions)


@app.route("/quizzes/<int:quiz_id>/questions/add", methods=["GET", "POST"])
@role_required("admin", "instructor")
def question_add(quiz_id):
    """Add a question to a quiz with options, answer key, and marks."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        text = request.form.get("text", "")
        opt_a = request.form.get("opt_a", "")
        opt_b = request.form.get("opt_b", "")
        opt_c = request.form.get("opt_c", "")
        opt_d = request.form.get("opt_d", "")
        correct_opt = request.form.get("correct_opt", "")
        marks = request.form.get("marks", 1)

        try:
            q_id = database.add_question(quiz_id, text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks)
            database.log_audit_event(
                event_type="QUESTION_CREATED",
                actor_username=session.get("username", "staff"),
                actor_role=session.get("role", "staff"),
                target_entity=f"question:{q_id}",
                outcome="SUCCESS",
                ip_address=request.remote_addr,
                details=f"Quiz #{quiz_id}"
            )
            flash("Question added successfully!", "success")
            return redirect(url_for("quiz_questions_manage", quiz_id=quiz_id))
        except ValueError as err:
            return render_template(
                "question_form.html",
                quiz=quiz,
                error=str(err),
                text=text,
                opt_a=opt_a,
                opt_b=opt_b,
                opt_c=opt_c,
                opt_d=opt_d,
                correct_opt=correct_opt,
                marks=marks
            ), 400

    return render_template("question_form.html", quiz=quiz)


@app.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@role_required("admin", "instructor")
def question_edit(question_id):
    """Edit question stem, options, correct option, or marks."""
    question = database.get_question_by_id(question_id)
    if question is None:
        return render_template("not_found.html"), 404

    quiz = database.get_quiz_by_id(question["quiz_id"])
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not verify_csrf(token):
            abort(400, description="Invalid or missing CSRF token.")

        text = request.form.get("text", "")
        opt_a = request.form.get("opt_a", "")
        opt_b = request.form.get("opt_b", "")
        opt_c = request.form.get("opt_c", "")
        opt_d = request.form.get("opt_d", "")
        correct_opt = request.form.get("correct_opt", "")
        marks = request.form.get("marks", 1)

        try:
            database.update_question(question_id, text, opt_a, opt_b, opt_c, opt_d, correct_opt, marks)
            database.log_audit_event(
                event_type="QUESTION_UPDATED",
                actor_username=session.get("username", "staff"),
                actor_role=session.get("role", "staff"),
                target_entity=f"question:{question_id}",
                outcome="SUCCESS",
                ip_address=request.remote_addr
            )
            flash("Question updated successfully!", "success")
            return redirect(url_for("quiz_questions_manage", quiz_id=question["quiz_id"]))
        except ValueError as err:
            return render_template(
                "question_form.html",
                question=question,
                quiz=quiz,
                error=str(err)
            ), 400

    return render_template("question_form.html", question=question, quiz=quiz)


@app.route("/questions/<int:question_id>/delete", methods=["POST"])
@role_required("admin", "instructor")
def question_delete(question_id):
    """Safely delete a question from a quiz."""
    token = request.form.get("csrf_token")
    if not verify_csrf(token):
        abort(400, description="Invalid or missing CSRF token.")

    question = database.get_question_by_id(question_id)
    if question is None:
        return render_template("not_found.html"), 404

    quiz_id = question["quiz_id"]
    database.delete_question(question_id)
    database.log_audit_event(
        event_type="QUESTION_DELETED",
        actor_username=session.get("username", "staff"),
        actor_role=session.get("role", "staff"),
        target_entity=f"question:{question_id}",
        outcome="SUCCESS",
        ip_address=request.remote_addr,
        details=f"Quiz #{quiz_id}"
    )
    flash("Question deleted successfully.", "success")
    return redirect(url_for("quiz_questions_manage", quiz_id=quiz_id))


# --- Security Audit Trail Route (Q04 Feature 4) ---

@app.route("/audit-logs")
@role_required("admin")
def audit_logs_view():
    """Exclusive administrator view of the tamper-evident security audit trail."""
    event_type = request.args.get("event_type", "").strip() or None
    logs = database.get_audit_logs(limit=200, event_type=event_type)
    return render_template("audit_logs.html", audit_logs=logs, selected_event=event_type)


# --- Results & Gradebook Routes (Review 2 CRUD) ---

@app.route("/results", endpoint="results_placeholder")
@app.route("/results", endpoint="results_view")
def results_placeholder():
    """Display role-governed assessment results and gradebook records."""
    user_id = session.get("user_id")
    user_role = session.get("role")

    if user_role in {"admin", "instructor"}:
        attempts = database.get_all_attempts()
        return render_template("results.html", attempts=attempts, is_staff=True)
    elif user_id and user_role == "student":
        attempts = database.get_attempts_by_user(user_id)
        if not attempts:
            username = session.get("username", "")
            attempts = database.get_attempts_by_roll(username)
        return render_template("results.html", attempts=attempts, is_staff=False)
    else:
        return render_template(
            "placeholder.html",
            module_title="Student Results & Performance Gradebook",
            phase_info="Scheduled for Phase 6 (Sign in for Gradebook)",
            description="Historical attempt analytics, pass/fail statistics, and student performance records will be displayed here upon signing in."
        )

results_view = results_placeholder


# --- Examination Engine & Attempt Pipeline ---

def finalize_quiz_attempt(attempt, answers, timed_out=False):
    token_id = attempt.get("submission_token")
    if not isinstance(token_id, str) or not token_id:
        abort(400, description="This attempt cannot be submitted. Start a new quiz.")

    with _SUBMISSION_LOCK:
        if token_id in _SUBMITTED_ATTEMPTS:
            session.pop("attempt", None)
            flash("This quiz attempt has already been submitted.", "info")
            return redirect(url_for("quizzes"))

        quiz_id = attempt["quiz_id"]
        quiz = database.get_quiz_by_id(quiz_id)
        if quiz is None:
            session.pop("attempt", None)
            return render_template("not_found.html"), 404

        question_ids = attempt["question_ids"]
        questions = database.get_questions_by_quiz(quiz_id)
        if [question["id"] for question in questions] != question_ids:
            session.pop("attempt", None)
            abort(409, description="Quiz questions changed during this attempt. Start the quiz again.")
        if not questions:
            session.pop("attempt", None)
            abort(409, description="The quiz no longer has any questions.")

        score = sum(
            question["marks"]
            for question in questions
            if answers.get(str(question["id"])) == question["correct_option"]
        )
        total_marks = sum(question["marks"] for question in questions)
        percentage = round(score / total_marks * 100 if total_marks > 0 else 0, 2)
        status = "Passed" if percentage >= float(quiz["pass_percentage"]) else "Failed"

        database.save_attempt(
            student_name=attempt["student_name"],
            student_roll=attempt["student_roll"],
            quiz_id=quiz_id,
            score=score,
            total_marks=total_marks,
            percentage=percentage,
            status=status,
            user_id=attempt.get("user_id"),
        )

        database.log_audit_event(
            event_type="QUIZ_ATTEMPT_SUBMITTED",
            actor_username=attempt["student_name"],
            actor_role=session.get("role", "student"),
            target_entity=f"quiz:{quiz_id}",
            outcome="SUCCESS",
            ip_address=request.remote_addr,
            details=f"Score: {score}/{total_marks} ({percentage}%), Outcome: {status}, TimedOut: {timed_out}"
        )

        _SUBMITTED_ATTEMPTS[token_id] = None
        _SUBMITTED_ATTEMPTS.move_to_end(token_id)
        if len(_SUBMITTED_ATTEMPTS) > _MAX_REMEMBERED_SUBMISSIONS:
            _SUBMITTED_ATTEMPTS.popitem(last=False)

    session.pop("attempt", None)
    result_token = secrets.token_urlsafe(32)
    session["pending_result"] = {
        "token": result_token,
        "quiz_title": quiz["title"],
        "score": score,
        "total_marks": total_marks,
        "percentage": percentage,
        "status": status,
        "timed_out": timed_out,
    }
    return redirect(url_for("attempt_result", result_token=result_token))


@app.route("/attempt/result/<result_token>")
def attempt_result(result_token):
    """Display and consume a result belonging only to the current session."""
    result = session.get("pending_result")
    token = result.get("token", "") if isinstance(result, dict) else ""
    if not isinstance(token, str) or not secrets.compare_digest(token, result_token):
        abort(404)

    session.pop("pending_result", None)
    return render_template("attempt_result.html", result=result)


@app.route("/")
def index():
    """Show the quiz catalogue dashboard without exposing private attempts."""
    quizzes = database.get_all_quizzes()
    question_count = sum(quiz["question_count"] for quiz in quizzes)
    return render_template(
        "index.html",
        quizzes=quizzes,
        quiz_count=len(quizzes),
        question_count=question_count,
    )


@app.route("/quizzes")
def quizzes():
    """List quizzes available in the SQLite database."""
    return render_template("quizzes.html", quizzes=database.get_all_quizzes())


@app.route("/quizzes/<int:quiz_id>")
def quiz_details(quiz_id):
    """Show quiz metadata and question count."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    questions = database.get_questions_by_quiz(quiz_id)
    return render_template(
        "quiz_details.html",
        quiz=quiz,
        question_count=len(questions),
        csrf_token=get_attempt_csrf_token(),
    )


@app.route("/quizzes/<int:quiz_id>/start", methods=["POST"])
def start_quiz(quiz_id):
    """Start a browser quiz attempt for the self-identified or authenticated student."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    if not verify_csrf(request.form.get("csrf_token")):
        abort(400, description="Invalid or missing form token. Reload the quiz details page and try again.")

    student_name = request.form.get("student_name", "").strip()
    student_roll = request.form.get("student_roll", "").strip()

    # If logged in as student, auto-populate if left empty
    if not student_name and session.get("username"):
        student_name = session.get("username")
    if not student_roll and session.get("username"):
        student_roll = session.get("username")

    questions = database.get_questions_by_quiz(quiz_id)
    if not student_name or not student_roll:
        error = "Enter both your name and roll number to start the quiz."
    elif len(student_name) > 100 or len(student_roll) > 50:
        error = "Name must be at most 100 characters and roll number at most 50 characters."
    else:
        error = None

    if error:
        return render_template(
            "quiz_details.html",
            quiz=quiz,
            question_count=len(questions),
            csrf_token=get_attempt_csrf_token(),
            error=error,
        ), 400
    if not questions:
        return render_template(
            "quiz_details.html",
            quiz=quiz,
            question_count=0,
            csrf_token=get_attempt_csrf_token(),
            error="This quiz has no questions and cannot be started.",
        ), 400

    try:
        time_limit_seconds = int(quiz["time_limit_mins"]) * 60
    except (TypeError, ValueError):
        abort(409, description="This quiz has no valid configured time limit.")
    if time_limit_seconds <= 0:
        abort(409, description="This quiz has no valid configured time limit.")

    # Preserve user session while setting up attempt
    user_id = session.get("user_id")
    username = session.get("username")
    role = session.get("role")
    email = session.get("email")

    session.clear()
    if user_id:
        session["user_id"] = user_id
        session["username"] = username
        session["role"] = role
        session["email"] = email

    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    session["attempt_csrf_token"] = token
    session["attempt"] = {
        "quiz_id": quiz_id,
        "student_name": student_name,
        "student_roll": student_roll,
        "question_ids": [question["id"] for question in questions],
        "answers": {},
        "submission_token": secrets.token_urlsafe(32),
        "started_at": time.time(),
        "time_limit_seconds": time_limit_seconds,
        "user_id": user_id,
    }
    return redirect(url_for("quiz_question", question_number=1))


@app.route("/attempt/question/<int:question_number>", methods=["GET", "POST"])
def quiz_question(question_number):
    """Render an attempt question and save answer changes while navigating."""
    attempt = session.get("attempt")
    if not attempt:
        return redirect(url_for("quizzes"))

    question_ids = attempt["question_ids"]
    if question_number < 1 or question_number > len(question_ids):
        abort(404)

    deadline = attempt["started_at"] + attempt["time_limit_seconds"]
    if request.method == "POST":
        if not verify_csrf(request.form.get("csrf_token")):
            abort(400, description="Invalid or missing form token. Reload the question and try again.")
        if time.time() >= deadline:
            return finalize_quiz_attempt(attempt, attempt["answers"], timed_out=True)
        action = request.form.get("action")
        answer = request.form.get("answer", "").upper()
        if answer and answer not in {"A", "B", "C", "D"}:
            abort(400, description="Select one of the available answer options.")
        answers = dict(attempt["answers"])
        if answer:
            answers[str(question_ids[question_number - 1])] = answer
        else:
            answers.pop(str(question_ids[question_number - 1]), None)
        attempt["answers"] = answers
        session["attempt"] = attempt

        if action == "previous" and question_number > 1:
            return redirect(url_for("quiz_question", question_number=question_number - 1))
        if action == "next" and question_number < len(question_ids):
            return redirect(url_for("quiz_question", question_number=question_number + 1))
        if action not in {"previous", "next"}:
            abort(400, description="Unknown question navigation action.")
    elif time.time() >= deadline:
        return finalize_quiz_attempt(attempt, attempt["answers"], timed_out=True)

    questions = database.get_questions_by_quiz(attempt["quiz_id"])
    question = next(
        (item for item in questions if item["id"] == question_ids[question_number - 1]),
        None,
    )
    if question is None:
        session.pop("attempt", None)
        abort(409, description="Quiz questions changed during this attempt. Start the quiz again.")

    # Defense: Answer key strictly stripped from student view
    public_question = {
        "id": question["id"],
        "question_text": question["question_text"],
        "option_a": question["option_a"],
        "option_b": question["option_b"],
        "option_c": question["option_c"],
        "option_d": question["option_d"],
        "marks": question["marks"],
    }
    quiz = database.get_quiz_by_id(attempt["quiz_id"])
    quiz["time_limit_mins"] = attempt["time_limit_seconds"] // 60
    return render_template(
        "quiz_question.html",
        quiz=quiz,
        question=public_question,
        question_number=question_number,
        question_count=len(question_ids),
        deadline_ms=int(deadline * 1000),
        selected_answer=attempt["answers"].get(str(question["id"]), ""),
        csrf_token=get_attempt_csrf_token(),
    )


@app.route("/attempt/submit", methods=["POST"])
def submit_quiz():
    """Grade and persist one attempt without exposing prior student results."""
    attempt = session.get("attempt")
    if not attempt:
        return redirect(url_for("quizzes"))

    token = request.form.get("csrf_token", "")
    if not verify_csrf(token):
        abort(400, description="Invalid or missing form token. Reload the question and try again.")

    try:
        question_number = int(request.form.get("question_number", ""))
    except ValueError:
        abort(400, description="Invalid question number.")

    question_ids = attempt["question_ids"]
    if question_number < 1 or question_number > len(question_ids):
        abort(400, description="Invalid question number.")

    answer_values = request.form.getlist("answer")
    if len(answer_values) > 1:
        abort(400, description="Submit at most one answer for the current question.")
    answer = answer_values[0].strip().upper() if answer_values else ""
    if answer and answer not in {"A", "B", "C", "D"}:
        abort(400, description="Select one of the available answer options.")

    answers = dict(attempt["answers"])
    current_question_id = str(question_ids[question_number - 1])
    if answer:
        answers[current_question_id] = answer
    else:
        answers.pop(current_question_id, None)

    timed_out = time.time() >= (
        attempt["started_at"] + attempt["time_limit_seconds"]
    )
    if timed_out:
        answers = dict(attempt["answers"])
    return finalize_quiz_attempt(attempt, answers, timed_out=timed_out)


@app.route("/attempt/answer", methods=["POST"])
def save_attempt_answer():
    """Persist an answer selection immediately while the attempt is active."""
    attempt = session.get("attempt")
    if not attempt:
        return jsonify(error="No active quiz attempt."), 400

    token = request.form.get("csrf_token", "")
    if not verify_csrf(token):
        abort(400, description="Invalid or missing form token.")

    try:
        question_number = int(request.form.get("question_number", ""))
    except ValueError:
        abort(400, description="Invalid question number.")

    question_ids = attempt["question_ids"]
    if question_number < 1 or question_number > len(question_ids):
        abort(400, description="Invalid question number.")
    if time.time() >= attempt["started_at"] + attempt["time_limit_seconds"]:
        return jsonify(error="The quiz deadline has passed.", expired=True), 410

    answers = dict(attempt["answers"])
    question_id = str(question_ids[question_number - 1])
    answer = request.form.get("answer", "").strip().upper()
    if answer and answer not in {"A", "B", "C", "D"}:
        abort(400, description="Select one of the available answer options.")
    if answer:
        answers[question_id] = answer
    else:
        answers.pop(question_id, None)
    attempt["answers"] = answers
    session["attempt"] = attempt
    return "", 204


@app.route("/reports")
def reports_placeholder():
    """Placeholder view for Visual Reports module (scheduled for Review 4)."""
    return render_template(
        "placeholder.html",
        module_title="Visual Reports & Performance Analytics",
        phase_info="Scheduled for Phase 7 (Review 4 SQC Tools)",
        description="Interactive visual charts depicting score trends, topic mastery, and distribution analytics will be integrated here."
    )


@app.route("/tqm")
def tqm_placeholder():
    """Placeholder view for TQM SQC Tools & Defect Logging (scheduled for Review 3/4)."""
    return render_template(
        "placeholder.html",
        module_title="TQM Quality Audit, Checksheet & SQC Tools",
        phase_info="Scheduled for Phase 7 (Review 3 & Review 4 TQM Tools)",
        description="Live digital checksheet, FMEA risk matrix, SIPOC mapping, CTQ Tree, 80/20 Pareto analysis, and PDCA log will be active here."
    )


if __name__ == "__main__":
    # Local development server execution
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="127.0.0.1", port=port, debug=debug)
