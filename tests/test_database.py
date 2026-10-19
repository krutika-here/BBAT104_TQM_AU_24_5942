import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

import database


class DatabaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.database_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.database_directory.name, "test.db")
        database.init_db()
        self.quiz_id = database.get_all_quizzes()[0]["id"]

    def tearDown(self):
        database.DB_PATH = self.original_database_path
        self.database_directory.cleanup()

    def test_create_and_update_quiz_reject_invalid_settings(self):
        quiz_id = database.create_quiz("Valid quiz", "  description  ", 10, 75)
        self.assertEqual(database.get_quiz_by_id(quiz_id)["description"], "description")
        database.update_quiz(quiz_id, "Updated quiz", "", 15, 80)
        self.assertEqual(database.get_quiz_by_id(quiz_id)["time_limit_mins"], 15)

        invalid_settings = (
            (0, 50),
            (-1, 50),
            (10, -0.1),
            (10, 100.1),
            (10, float("nan")),
        )
        for time_limit, pass_percentage in invalid_settings:
            with self.subTest(time_limit=time_limit, pass_percentage=pass_percentage):
                with self.assertRaises(ValueError):
                    database.create_quiz("Invalid quiz", "", time_limit, pass_percentage)
                with self.assertRaises(ValueError):
                    database.update_quiz(
                        self.quiz_id, "Updated quiz", "", time_limit, pass_percentage
                    )

        with self.assertRaises(ValueError):
            database.create_quiz("   ", "", 10, 50)

    def test_question_crud_rejects_blank_fields_invalid_key_and_marks(self):
        valid_question = (
            "Question text",
            "Option A",
            "Option B",
            "Option C",
            "Option D",
            "A",
            1,
        )
        question_id = database.add_question(self.quiz_id, *valid_question)
        database.update_question(
            question_id, "Updated question", "A", "B", "C", "D", "D", 2
        )
        question = next(
            question
            for question in database.get_questions_by_quiz(self.quiz_id)
            if question["id"] == question_id
        )
        self.assertEqual(
            (question["question_text"], question["correct_option"], question["marks"]),
            ("Updated question", "D", 2),
        )

        invalid_questions = (
            (" ", *valid_question[1:]),
            (valid_question[0], " ", *valid_question[2:]),
            (*valid_question[:5], "Z", 1),
            (*valid_question[:6], 0),
            (*valid_question[:6], -1),
        )
        for question in invalid_questions:
            with self.subTest(question=question):
                with self.assertRaises(ValueError):
                    database.add_question(self.quiz_id, *question)
                with self.assertRaises(ValueError):
                    database.update_question(question_id, *question)

    def test_question_cannot_reference_a_missing_quiz(self):
        with self.assertRaises(sqlite3.IntegrityError):
            database.add_question(
                999999, "Question", "A", "B", "C", "D", "A", 1
            )

    def test_quiz_with_attempts_cannot_be_deleted(self):
        question_id = database.add_question(
            self.quiz_id, "Question", "A", "B", "C", "D", "A", 1
        )
        database.save_attempt(
            "Student", "ROLL", self.quiz_id, 1, 1, 100.0, "Passed"
        )

        with self.assertRaisesRegex(ValueError, "recorded student attempts"):
            database.delete_quiz(self.quiz_id)

        self.assertIsNotNone(database.get_quiz_by_id(self.quiz_id))
        self.assertIn(question_id, [q["id"] for q in database.get_questions_by_quiz(self.quiz_id)])
        self.assertEqual(len(database.get_all_attempts()), 1)

    def test_quiz_without_attempts_and_its_questions_can_be_deleted(self):
        question_id = database.add_question(
            self.quiz_id, "Question", "A", "B", "C", "D", "A", 1
        )

        database.delete_quiz(self.quiz_id)

        self.assertIsNone(database.get_quiz_by_id(self.quiz_id))
        self.assertNotIn(question_id, [q["id"] for q in database.get_questions_by_quiz(self.quiz_id)])

    # --- Q04 Security Database Tests ---

    def test_default_users_seeded(self):
        users = database.get_all_users()
        usernames = {u["username"] for u in users}
        self.assertIn("admin", usernames)
        self.assertIn("instructor", usernames)
        self.assertIn("student", usernames)
        admin = database.get_user_by_username("admin")
        self.assertEqual(admin["role"], "admin")
        self.assertNotIn("password_hash", users[0])  # ensure password_hash not leaked in get_all_users

    def test_create_user_and_credential_verification(self):
        user_id = database.create_user("new_tester", "tester@test.com", "Password@123", role="student")
        self.assertIsInstance(user_id, int)
        user = database.get_user_by_id(user_id)
        self.assertEqual(user["username"], "new_tester")
        self.assertEqual(user["email"], "tester@test.com")
        self.assertEqual(user["role"], "student")

        # Verify correct credentials
        verified = database.verify_user_credentials("new_tester", "Password@123")
        self.assertIsNotNone(verified)
        self.assertEqual(verified["id"], user_id)

        # Verify case-insensitive email login
        verified_email = database.verify_user_credentials("TESTER@TEST.COM", "Password@123")
        self.assertIsNotNone(verified_email)

        # Verify rejection on bad password
        self.assertIsNone(database.verify_user_credentials("new_tester", "WrongPassword!"))

    def test_create_user_input_validation(self):
        # Invalid usernames
        with self.assertRaises(ValueError):
            database.create_user("ab", "valid@email.com", "Password@123")
        with self.assertRaises(ValueError):
            database.create_user("bad user!", "valid@email.com", "Password@123")

        # Invalid emails
        with self.assertRaises(ValueError):
            database.create_user("valid_user", "notanemail", "Password@123")

        # Short passwords
        with self.assertRaises(ValueError):
            database.create_user("valid_user", "valid@email.com", "short")

        # Invalid role
        with self.assertRaises(ValueError):
            database.create_user("valid_user", "valid@email.com", "Password@123", role="superhero")

    def test_password_reset_lifecycle(self):
        user_id = database.create_user("reset_user", "reset@test.com", "OldPassword@123")
        result = database.create_password_reset_token("reset@test.com")
        self.assertIsNotNone(result)
        raw_token, user = result
        self.assertEqual(user["id"], user_id)

        # Verify valid token
        reset_record = database.verify_password_reset_token(raw_token)
        self.assertIsNotNone(reset_record)
        self.assertEqual(reset_record["user_id"], user_id)

        # Consume token with new password
        success = database.consume_password_reset_token(raw_token, "NewPassword@456")
        self.assertTrue(success)

        # Token is single-use and cannot be reused
        self.assertFalse(database.consume_password_reset_token(raw_token, "AnotherPassword@789"))
        self.assertIsNone(database.verify_password_reset_token(raw_token))

        # Check new password works and old password fails
        self.assertIsNotNone(database.verify_user_credentials("reset_user", "NewPassword@456"))
        self.assertIsNone(database.verify_user_credentials("reset_user", "OldPassword@123"))

    def test_audit_logging_and_retrieval(self):
        database.log_audit_event(
            event_type="AUTH_LOGIN_SUCCESS",
            actor_username="test_admin",
            actor_role="admin",
            target_entity="system",
            outcome="SUCCESS",
            ip_address="127.0.0.1",
            details="User logged in from test"
        )
        logs = database.get_audit_logs(limit=10)
        self.assertTrue(len(logs) >= 1)
        latest = logs[0]
        self.assertEqual(latest["event_type"], "AUTH_LOGIN_SUCCESS")
        self.assertEqual(latest["actor_username"], "test_admin")
        self.assertEqual(latest["actor_role"], "admin")
        self.assertEqual(latest["outcome"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
