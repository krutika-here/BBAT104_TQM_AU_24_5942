"""
Online Quiz System - Flask Web Application Shell
Course: BBAT104 - Fundamentals of Total Quality Management
Registration: AU-24-5942 | Academic Session 2026-27
Assigned Quality Goal: Q08 - Improve User Satisfaction
Phase: Phase 2 - Flask Website Shell Only
"""

import os
import secrets
import threading
import time
from collections import OrderedDict
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for

import database

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
_SUBMISSION_LOCK = threading.Lock()
_SUBMITTED_ATTEMPTS = OrderedDict()
_MAX_REMEMBERED_SUBMISSIONS = 1000


def get_attempt_csrf_token():
    token = session.get("attempt_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["attempt_csrf_token"] = token
    return token


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
    """Show the quiz catalogue and navigation without exposing private attempts."""
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
    """List quizzes available in the existing SQLite database."""
    return render_template("quizzes.html", quizzes=database.get_all_quizzes())


@app.route("/quizzes/<int:quiz_id>")
def quiz_details(quiz_id):
    """Show quiz metadata and its current available question count."""
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
    """Start a browser quiz attempt for the self-identified student."""
    quiz = database.get_quiz_by_id(quiz_id)
    if quiz is None:
        return render_template("not_found.html"), 404

    if request.form.get("csrf_token") != session.get("attempt_csrf_token"):
        abort(400, description="Invalid or missing form token. Reload the quiz details page and try again.")

    student_name = request.form.get("student_name", "").strip()
    student_roll = request.form.get("student_roll", "").strip()
    questions = database.get_questions_by_quiz(quiz_id)
    if not student_name or not student_roll:
        return render_template(
            "quiz_details.html",
            quiz=quiz,
            question_count=len(questions),
            csrf_token=get_attempt_csrf_token(),
            error="Enter both your name and roll number to start the quiz.",
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

    session.clear()
    session["attempt_csrf_token"] = secrets.token_urlsafe(32)
    session["attempt"] = {
        "quiz_id": quiz_id,
        "student_name": student_name,
        "student_roll": student_roll,
        "question_ids": [question["id"] for question in questions],
        "answers": {},
        "submission_token": secrets.token_urlsafe(32),
        "started_at": time.time(),
        "time_limit_seconds": time_limit_seconds,
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
        if not secrets.compare_digest(
            request.form.get("csrf_token", ""),
            session.get("attempt_csrf_token", ""),
        ):
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
    if not secrets.compare_digest(token, session.get("attempt_csrf_token", "")):
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
    if not secrets.compare_digest(token, session.get("attempt_csrf_token", "")):
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


@app.route("/results")
def results_placeholder():
    """Placeholder view for Results & Gradebook module (scheduled for Phase 6)."""
    return render_template(
        "placeholder.html",
        module_title="Student Results & Performance Gradebook",
        phase_info="Scheduled for Phase 6",
        description="Historical attempt analytics, pass/fail statistics, and student performance records will be displayed here."
    )

@app.route("/reports")
def reports_placeholder():
    """Placeholder view for Visual Reports module (Quality Goal Q08 Feature 2, scheduled for Phase 7)."""
    return render_template(
        "placeholder.html",
        module_title="Visual Reports & Performance Analytics",
        phase_info="Scheduled for Phase 7 (Quality Goal Q08)",
        description="Interactive visual charts depicting score trends, topic mastery, and distribution analytics will be integrated here."
    )

@app.route("/tqm")
def tqm_placeholder():
    """Placeholder view for TQM SQC Tools & Defect Logging (scheduled for Phase 7)."""
    return render_template(
        "placeholder.html",
        module_title="TQM Quality Audit, Checksheet & SQC Tools",
        phase_info="Scheduled for Phase 7 (BBAT104 Review 3/4 Alignment)",
        description="Live digital checksheet, FMEA risk matrix, SIPOC mapping, CTQ Tree, 80/20 Pareto analysis, and PDCA log will be active here."
    )

if __name__ == "__main__":
    # Local development server execution
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="127.0.0.1", port=port, debug=debug)
