"""
Online Quiz System - Flask Web Application Shell
Course: BBAT104 - Fundamentals of Total Quality Management
Registration: AU-24-5942 | Academic Session 2026-27
Assigned Quality Goal: Q08 - Improve User Satisfaction
Phase: Phase 2 - Flask Website Shell Only
"""

import os
import secrets
import time
from flask import Flask, abort, redirect, render_template, request, session, url_for

import database

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_attempt_csrf_token():
    token = session.get("attempt_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["attempt_csrf_token"] = token
    return token

@app.route("/")
def index():
    """
    Homepage and main interactive dashboard placeholder.
    In Phase 2, statistics and module entries are clearly presented as placeholders.
    Database writes and quiz evaluation are explicitly disabled in this phase.
    """
    return render_template("index.html")

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

    session.clear()
    session["attempt_csrf_token"] = secrets.token_urlsafe(32)
    session["attempt"] = {
        "quiz_id": quiz_id,
        "student_name": student_name,
        "student_roll": student_roll,
        "question_ids": [question["id"] for question in questions],
        "answers": {},
        "started_at": time.time(),
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

    if request.method == "POST":
        if request.form.get("csrf_token") != session.get("attempt_csrf_token"):
            abort(400, description="Invalid or missing form token. Reload the question and try again.")
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
    return render_template(
        "quiz_question.html",
        quiz=database.get_quiz_by_id(attempt["quiz_id"]),
        question=public_question,
        question_number=question_number,
        question_count=len(question_ids),
        selected_answer=attempt["answers"].get(str(question["id"]), ""),
        csrf_token=get_attempt_csrf_token(),
    )

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
