import os
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

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
                CREATE TABLE attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    student_roll TEXT NOT NULL,
                    quiz_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    total_marks INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    status TEXT NOT NULL,
                    completed_at TEXT DEFAULT CURRENT_TIMESTAMP
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

    def _save_answer(self, answer, question_number=1):
        page = self.client.get(f"/attempt/question/{question_number}")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', page.data
        ).group(1).decode()
        return self.client.post(
            "/attempt/answer",
            data={
                "csrf_token": csrf_token,
                "question_number": str(question_number),
                "answer": answer,
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

    def test_start_rejects_missing_or_nonpositive_time_limit(self):
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute(
                "UPDATE quizzes SET time_limit_mins = NULL WHERE id = 41"
            )

        response = self._start_attempt()
        self.assertEqual(response.status_code, 409)
        self.assertIn(b"no valid configured time limit", response.data)

        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute(
                "UPDATE quizzes SET time_limit_mins = 0 WHERE id = 41"
            )

        response = self._start_attempt()
        self.assertEqual(response.status_code, 409)

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

    def test_question_page_displays_database_configured_deadline(self):
        with patch("app.time.time", return_value=1000):
            response = self._start_attempt()
            self.assertEqual(response.status_code, 302)
            question = self.client.get("/attempt/question/1")

        self.assertEqual(question.status_code, 200)
        self.assertIn(b'Time remaining', question.data)
        self.assertIn(b'data-deadline-ms="1720000"', question.data)
        self.assertIn(b'12:00', question.data)
        self.assertIn(b'data-answer-url="/attempt/answer"', question.data)
        self.assertIn(b"Date.now()", question.data)
        self.assertIn(b"requestSubmit", question.data)
        self.assertIn(b"server enforces the configured deadline", question.data)

    def test_expired_attempt_is_automatically_graded_from_saved_answers(self):
        with patch("app.time.time", return_value=1000):
            self._start_attempt()
            self._answer_and_next("A", 1)

        with patch("app.time.time", return_value=1721):
            response = self.client.get("/attempt/question/2", follow_redirects=True)

        self.assertIn(b"Time expired. Your answers saved before the deadline were graded", response.data)
        self.assertIn(b"2 / 3", response.data)
        self.assertEqual(self._stored_attempt()[0][3:], (2, 3, 66.67, "Passed"))

    def test_changed_answer_is_saved_before_deadline_and_graded_on_expiry(self):
        with patch("app.time.time", return_value=1000):
            self._start_attempt()
            response = self._save_answer("A")
            self.assertEqual(response.status_code, 204)

        with patch("app.time.time", return_value=1721):
            response = self.client.get("/attempt/question/1", follow_redirects=True)

        self.assertIn(b"Time expired.", response.data)
        self.assertIn(b"2 / 3", response.data)
        self.assertEqual(self._stored_attempt()[0][3:], (2, 3, 66.67, "Passed"))

    def test_answer_autosave_rejects_expired_or_invalid_answer(self):
        with patch("app.time.time", return_value=1000):
            self._start_attempt()
            page = self.client.get("/attempt/question/1")
            csrf_token = re.search(
                rb'name="csrf_token" value="([^"]+)"', page.data
            ).group(1).decode()

        response = self.client.post(
            "/attempt/answer",
            data={
                "csrf_token": csrf_token,
                "question_number": "1",
                "answer": "X",
            },
        )
        self.assertEqual(response.status_code, 400)

        with patch("app.time.time", return_value=1721):
            response = self.client.post(
                "/attempt/answer",
                data={
                    "csrf_token": csrf_token,
                    "question_number": "1",
                    "answer": "A",
                },
            )

        self.assertEqual(response.status_code, 410)
        self.assertEqual(self._stored_attempt(), [])

    def test_late_answer_is_ignored_after_server_deadline(self):
        with patch("app.time.time", return_value=1000):
            self._start_attempt()
            self._answer_and_next("A", 1)
            page = self.client.get("/attempt/question/2")
            csrf_token = re.search(
                rb'name="csrf_token" value="([^"]+)"', page.data
            ).group(1).decode()

        with patch("app.time.time", return_value=1721):
            response = self.client.post(
                "/attempt/submit",
                data={
                    "csrf_token": csrf_token,
                    "question_number": "2",
                    "answer": "D",
                },
                follow_redirects=True,
            )

        self.assertIn(b"Time expired. Your answers saved before the deadline were graded", response.data)
        self.assertIn(b"2 / 3", response.data)
        self.assertEqual(self._stored_attempt()[0][3:], (2, 3, 66.67, "Passed"))

    def test_expired_page_replay_does_not_save_duplicate_attempt(self):
        with patch("app.time.time", return_value=1000):
            self._start_attempt()
            page = self.client.get("/attempt/question/1")
            csrf_token = re.search(
                rb'name="csrf_token" value="([^"]+)"', page.data
            ).group(1).decode()
            stale_cookie = self.client.get_cookie(app.config["SESSION_COOKIE_NAME"])

        with patch("app.time.time", return_value=1721):
            first = self.client.get("/attempt/question/1", follow_redirects=True)
            duplicate_client = app.test_client()
            duplicate_client.set_cookie(
                app.config["SESSION_COOKIE_NAME"],
                stale_cookie.value,
            )
            second = duplicate_client.post(
                "/attempt/submit",
                data={"csrf_token": csrf_token, "question_number": "1"},
                follow_redirects=True,
            )

        self.assertIn(b"Time expired. Your answers saved before the deadline were graded", first.data)
        self.assertIn(b"already been submitted", second.data)
        self.assertEqual(len(self._stored_attempt()), 1)

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

    def _submit_quiz(
        self,
        answer=None,
        question_number=1,
        client=None,
        csrf_token=None,
        follow_redirects=True,
    ):
        client = client or self.client
        if csrf_token is None:
            page = client.get(f"/attempt/question/{question_number}")
            csrf_token = re.search(
                rb'name="csrf_token" value="([^"]+)"', page.data
            ).group(1).decode()
        data = {
            "csrf_token": csrf_token,
            "question_number": str(question_number),
        }
        if answer is not None:
            data["answer"] = answer
        return client.post(
            "/attempt/submit",
            data=data,
            follow_redirects=follow_redirects,
        )

    def _answer_and_next(self, answer, question_number):
        page = self.client.get(f"/attempt/question/{question_number}")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', page.data
        ).group(1).decode()
        return self.client.post(
            f"/attempt/question/{question_number}",
            data={
                "csrf_token": csrf_token,
                "answer": answer,
                "action": "next",
            },
        )

    def _stored_attempt(self):
        with sqlite3.connect(database.DB_PATH) as connection:
            return connection.execute(
                "SELECT student_name, student_roll, quiz_id, score, total_marks, percentage, status "
                "FROM attempts"
            ).fetchall()

    def test_submission_grades_correct_answers_using_stored_marks(self):
        self._start_attempt()
        self._answer_and_next("A", 1)

        result = self._submit_quiz(answer="D", question_number=2)
        self.assertIn(b"Fixture Quiz", result.data)
        self.assertIn(b"3 / 3", result.data)
        self.assertIn(b"100.00%", result.data)
        self.assertIn(b"Submission complete. Your attempt was graded and saved.", result.data)
        self.assertIn(b"Passed", result.data)
        self.assertNotIn(b"Test Student", result.data)
        self.assertNotIn(b"TEST-1", result.data)
        self.assertEqual(
            self._stored_attempt(),
            [("Test Student", "TEST-1", 41, 3, 3, 100.0, "Passed")],
        )

    def test_submission_grades_incorrect_answers_as_zero(self):
        self._start_attempt()
        self._answer_and_next("B", 1)

        result = self._submit_quiz(answer="B", question_number=2)
        self.assertIn(b"0 / 3", result.data)
        self.assertIn(b"0.00%", result.data)
        self.assertIn(b"Failed", result.data)
        self.assertEqual(self._stored_attempt()[0][3:], (0, 3, 0.0, "Failed"))

    def test_unanswered_question_receives_no_marks(self):
        self._start_attempt()
        self._answer_and_next("A", 1)

        result = self._submit_quiz(question_number=2)
        self.assertIn(b"2 / 3", result.data)
        self.assertIn(b"66.67%", result.data)
        self.assertIn(b"Passed", result.data)
        self.assertEqual(self._stored_attempt()[0][3:], (2, 3, 66.67, "Passed"))

    def test_result_token_is_one_time_and_unknown_tokens_are_not_found(self):
        self._start_attempt()
        submission = self._submit_quiz(answer="A", follow_redirects=False)
        self.assertEqual(submission.status_code, 302)
        valid_url = submission.location
        self.assertTrue(valid_url.startswith("/attempt/result/"))
        response = self.client.get(valid_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Return to quiz catalogue", response.data)
        self.assertEqual(self.client.get(valid_url).status_code, 404)
        self.assertEqual(self.client.get("/attempt/result/unknown").status_code, 404)

    def test_another_session_cannot_access_a_result_token(self):
        self._start_attempt()
        submission = self._submit_quiz(answer="A", follow_redirects=False)
        result_url = submission.location

        other_session = app.test_client()
        response = other_session.get(result_url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_submission_is_rejected_without_saving_attempt(self):
        self._start_attempt()
        page = self.client.get("/attempt/question/1")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', page.data
        ).group(1).decode()

        response = self.client.post(
            "/attempt/submit",
            data={
                "csrf_token": csrf_token,
                "question_number": "1",
                "answer": "X",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._stored_attempt(), [])

        response = self.client.post(
            "/attempt/submit",
            data={"csrf_token": csrf_token, "question_number": "not-a-number"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._stored_attempt(), [])

    def test_duplicate_submission_with_stale_session_does_not_duplicate_attempt(self):
        self._start_attempt()
        page = self.client.get("/attempt/question/1")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', page.data
        ).group(1).decode()
        stale_cookie = self.client.get_cookie(app.config["SESSION_COOKIE_NAME"])
        duplicate_client = app.test_client()
        duplicate_client.set_cookie(app.config["SESSION_COOKIE_NAME"], stale_cookie.value)

        first = self._submit_quiz(answer="A", csrf_token=csrf_token)
        self.assertIn(b"Submission complete. Your attempt was graded and saved.", first.data)
        duplicate = self._submit_quiz(
            answer="A",
            client=duplicate_client,
            csrf_token=csrf_token,
        )

        self.assertIn(b"already been submitted", duplicate.data)
        self.assertEqual(len(self._stored_attempt()), 1)

    def test_submission_rejects_quiz_deleted_during_attempt(self):
        self._start_attempt()
        page = self.client.get("/attempt/question/1")
        csrf_token = re.search(
            rb'name="csrf_token" value="([^"]+)"', page.data
        ).group(1).decode()
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute("DELETE FROM quizzes WHERE id = 41")

        response = self._submit_quiz(
            answer="A",
            csrf_token=csrf_token,
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._stored_attempt(), [])


if __name__ == "__main__":
    unittest.main()
