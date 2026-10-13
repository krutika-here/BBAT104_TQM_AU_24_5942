"""
Online Quiz System - Flask Web Application Shell
Course: BBAT104 - Fundamentals of Total Quality Management
Registration: AU-24-5942 | Academic Session 2026-27
Assigned Quality Goal: Q08 - Improve User Satisfaction
Phase: Phase 2 - Flask Website Shell Only
"""

import os
from flask import Flask, render_template

import database

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "bbat104-tqm-quiz-system-dev-key")

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
