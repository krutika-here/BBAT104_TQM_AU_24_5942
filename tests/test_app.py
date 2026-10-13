import os
import re
import sqlite3
import tempfile
import unittest

import database
from app import app


class FlaskApplicationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.database_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.database_directory.name, "test.db")
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.executescript("""
                CREATE TABLE quizzes (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    time_limit_mins INTEGER,
                    pass_percentage REAL,
                    created_at TEXT
                );
                CREATE TABLE questions (
                    id INTEGER PRIMARY KEY,
                    quiz_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    option_a TEXT NOT NULL,
                    option_b TEXT NOT NULL,
                    option_c TEXT NOT NULL,
                    option_d TEXT NOT NULL,
                    correct_option TEXT NOT NULL,
                    marks INTEGER DEFAULT 1
                );
                INSERT INTO quizzes VALUES
                    (41, 'Fixture Quiz', 'Test-only catalog data', 12, 60.0, CURRENT_TIMESTAMP),
                    (42, 'Empty Fixture', '', 5, 50.0, CURRENT_TIMESTAMP);
                INSERT INTO questions VALUES
                    (101, 41, 'Fixture question one?', 'A1', 'B1', 'C1', 'D1', 'A', 2),
                    (102, 41, 'Fixture question two?', 'A2', 'B2', 'C2', 'D2', 'D', 1);
            """)

    def tearDown(self):
        database.DB_PATH = self.original_database_path
        self.database_directory.cleanup()

    def test_homepage_renders_dashboard_and_navigation(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Online Quiz System", response.data)
        self.assertIn(b"Dashboard", response.data)
        self.assertIn(b'href="/quizzes"', response.data)
        self.assertIn(b'href="/results"', response.data)
        self.assertIn(b'href="/reports"', response.data)
        self.assertIn(b'href="/tqm"', response.data)

    def test_incomplete_modules_are_labeled_as_placeholders(self):
        modules = {
            "/results": b"Student Results &amp; Performance Gradebook",
            "/reports": b"Visual Reports &amp; Performance Analytics",
            "/tqm": b"TQM Quality Audit, Checksheet &amp; SQC Tools",
        }

        for path, title in modules.items():
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertIn(title, response.data)
                self.assertIn(b"Phase 2 Scope Boundary", response.data)
                self.assertIn(b"Scheduled for Phase", response.data)

    def test_quiz_listing_uses_database_records_without_answer_keys(self):
        response = self.client.get("/quizzes")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fixture Quiz", response.data)
        self.assertIn(b"Empty Fixture", response.data)
        self.assertIn(b"2 questions", response.data)
        self.assertNotIn(b"correct_option", response.data)

    def test_empty_database_shows_empty_quiz_listing(self):
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute("DELETE FROM quizzes")

        response = self.client.get("/quizzes")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No quizzes available", response.data)

    def test_quiz_details_show_actual_question_count_and_settings(self):
        response = self.client.get("/quizzes/41")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fixture Quiz", response.data)
        self.assertIn(b"Available questions", response.data)
        self.assertIn(b">2<", response.data)
        self.assertIn(b"12 minutes", response.data)
        self.assertIn(b"60.0%", response.data)
        self.assertNotIn(b"correct_option", response.data)

    def test_empty_quiz_cannot_be_started_message_is_shown(self):
        response = self.client.get("/quizzes/42")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"cannot be started because it has no questions", response.data)

    def test_unknown_quiz_returns_not_found(self):
        response = self.client.get("/quizzes/999")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Quiz not found", response.data)

    def _csrf_token(self):
        response = self.client.get("/quizzes/41")
        return re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()

    def _start_attempt(self, quiz_id=41, student_name="Test Student", student_roll="TEST-1"):
        return self.client.post(
            f"/quizzes/{quiz_id}/start",
            data={
                "csrf_token": self._csrf_token(),
                "student_name": student_name,
                "student_roll": student_roll,
            },
        )

    def test_start_requires_self_reported_identity_and_valid_form_token(self):
        response = self.client.post("/quizzes/41/start", data={"student_name": "Student"})
        self.assertEqual(response.status_code, 400)

        response = self._start_attempt(student_name="  ", student_roll="TEST-1")
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Enter both your name and roll number", response.data)

    def test_start_rejects_unknown_or_empty_quiz(self):
        response = self.client.post("/quizzes/999/start", data={})
        self.assertEqual(response.status_code, 404)

        response = self._start_attempt(quiz_id=42)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"has no questions", response.data)

    def test_quiz_question_navigation_saves_and_restores_answers(self):
        response = self._start_attempt()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/attempt/question/1")

        response = self.client.get("/attempt/question/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fixture question one?", response.data)
        self.assertNotIn(b"correct_option", response.data)

        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', response.data
        ).group(1).decode()
        response = self.client.post(
            "/attempt/question/1",
            data={"csrf_token": csrf_token, "answer": "A", "action": "next"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/attempt/question/2")

        response = self.client.get("/attempt/question/2")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fixture question two?", response.data)

        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', response.data
        ).group(1).decode()
        response = self.client.post(
            "/attempt/question/2",
            data={"csrf_token": csrf_token, "answer": "D", "action": "previous"},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/attempt/question/1")
        self.assertIn(b'value="A" checked', response.data)

    def test_question_navigation_rejects_invalid_answer_and_question_number(self):
        self._start_attempt()
        response = self.client.get("/attempt/question/1")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', response.data
        ).group(1).decode()

        response = self.client.post(
            "/attempt/question/1",
            data={"csrf_token": csrf_token, "answer": "X", "action": "next"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/attempt/question/0").status_code, 404)


if __name__ == "__main__":
    unittest.main()
