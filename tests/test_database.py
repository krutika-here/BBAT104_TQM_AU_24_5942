import os
import sqlite3
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
