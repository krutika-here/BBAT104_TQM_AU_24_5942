"""
Automated Security & Base CRUD Test Suite for Review 2
Course: BBAT104 Fundamentals of TQM | Roll: 39 | Reg: AU-24-5942
Assigned Quality Goal: Q04 - Improve Security
Features Tested:
1. Role-Based Login & RBAC Enforcement (Feature 1)
2. Password Reset Lifecycle & Single-Use Tokens (Feature 2)
3. Input Validation & Bounds Enforcement (Feature 3)
4. Audit Trail Logging & Admin Access Control (Feature 4)
5. Sensitive Data Protection, Secret Isolation & Header Defense (Feature 5)
6. Complete CRUD: Quizzes, Questions, Attempts & Gradebook
"""

import os
import re
import secrets
import sqlite3
import tempfile
import time
import unittest

import database
from app import app


class SecurityAndCrudTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.database_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.database_directory.name, "test_security.db")
        database.init_db()

        # Seed test admin, instructor, student users
        self.admin_id = database.create_user("sysadmin", "admin@domain.com", "AdminPass@123", role="admin")
        self.instructor_id = database.create_user("prof_smith", "smith@domain.com", "ProfPass@123", role="instructor")
        self.student_id = database.create_user("student_bob", "bob@domain.com", "StudentPass@123", role="student")

        self.quiz_id = database.get_all_quizzes()[0]["id"]

    def tearDown(self):
        database.DB_PATH = self.original_database_path
        self.database_directory.cleanup()

    def _login(self, identifier, password):
        """Helper to log in a user and establish an authenticated session."""
        # First GET /login to obtain CSRF token
        resp = self.client.get("/login")
        token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.data.decode("utf-8"))
        csrf_token = token_match.group(1) if token_match else "dummy_csrf"

        return self.client.post("/login", data={
            "csrf_token": csrf_token,
            "identifier": identifier,
            "password": password,
        }, follow_redirects=True)

    def _get_csrf_token(self, path="/"):
        """Extract a valid CSRF token from a rendered page."""
        resp = self.client.get(path)
        token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.data.decode("utf-8"))
        return token_match.group(1) if token_match else ""

    # =========================================================================
    # FEATURE 1: ROLE-BASED LOGIN & RBAC TESTS
    # =========================================================================

    def test_login_success_and_session_regeneration(self):
        response = self._login("sysadmin", "AdminPass@123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"sysadmin (Admin)", response.data)
        self.assertIn(b"Logout", response.data)

        # Verify audit log recorded LOGIN_SUCCESS
        logs = database.get_audit_logs(event_type="AUTH_LOGIN_SUCCESS")
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0]["actor_username"], "sysadmin")
        self.assertEqual(logs[0]["actor_role"], "admin")

    def test_login_failure_with_wrong_password(self):
        response = self._login("sysadmin", "WrongPassword!")
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid username/email or password", response.data)

        # Verify audit log recorded LOGIN_FAILURE
        logs = database.get_audit_logs(event_type="AUTH_LOGIN_FAILURE")
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0]["actor_username"], "sysadmin")
        self.assertEqual(logs[0]["outcome"], "FAILURE")

    def test_student_cannot_access_quiz_management(self):
        self._login("student_bob", "StudentPass@123")
        response = self.client.get("/quizzes/manage")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"403 - Access Forbidden", response.data)

        # Verify unauthorized access event was audited
        logs = database.get_audit_logs(event_type="UNAUTHORIZED_ACCESS_ATTEMPT")
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0]["actor_username"], "student_bob")
        self.assertEqual(logs[0]["outcome"], "BLOCKED")

    def test_instructor_and_admin_can_access_quiz_management(self):
        # Instructor
        self._login("prof_smith", "ProfPass@123")
        resp_instructor = self.client.get("/quizzes/manage")
        self.assertEqual(resp_instructor.status_code, 200)
        self.assertIn(b"Quiz Management Console", resp_instructor.data)

        # Admin
        self._login("sysadmin", "AdminPass@123")
        resp_admin = self.client.get("/quizzes/manage")
        self.assertEqual(resp_admin.status_code, 200)
        self.assertIn(b"Quiz Management Console", resp_admin.data)

    def test_instructor_cannot_access_audit_logs(self):
        self._login("prof_smith", "ProfPass@123")
        response = self.client.get("/audit-logs")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"403 - Access Forbidden", response.data)

    def test_admin_can_access_audit_logs(self):
        self._login("sysadmin", "AdminPass@123")
        response = self.client.get("/audit-logs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Security Audit Trail", response.data)

    def test_csrf_protection_blocks_forged_requests(self):
        self._login("sysadmin", "AdminPass@123")
        # Submit without CSRF token
        response = self.client.post("/quizzes/create", data={
            "title": "Forged Quiz",
            "time_limit_mins": 10,
            "pass_percentage": 50,
        })
        self.assertEqual(response.status_code, 400)

    def test_logout_clears_session(self):
        self._login("student_bob", "StudentPass@123")
        csrf_token = self._get_csrf_token("/quizzes")
        resp = self.client.post("/logout", data={"csrf_token": csrf_token}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sign In", resp.data)
        self.assertNotIn(b"student_bob", resp.data)

    # =========================================================================
    # FEATURE 2: PASSWORD RESET LIFECYCLE TESTS
    # =========================================================================

    def test_password_reset_request_and_token_generation(self):
        csrf = self._get_csrf_token("/forgot-password")
        response = self.client.post("/forgot-password", data={
            "csrf_token": csrf,
            "email": "bob@domain.com",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"reset link has been generated", response.data)
        self.assertIn(b"/reset-password/", response.data)

    def test_password_reset_completion_and_invalidation(self):
        raw_token, user = database.create_password_reset_token("bob@domain.com")
        self.assertEqual(user["username"], "student_bob")

        # GET reset page
        get_resp = self.client.get(f"/reset-password/{raw_token}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn(b"Set New Password", get_resp.data)

        # POST new password
        csrf = self._get_csrf_token(f"/reset-password/{raw_token}")
        post_resp = self.client.post(f"/reset-password/{raw_token}", data={
            "csrf_token": csrf,
            "new_password": "NewBobPassword@456",
            "confirm_password": "NewBobPassword@456",
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertIn(b"Your password has been reset successfully", post_resp.data)

        # Token cannot be reused
        reuse_resp = self.client.get(f"/reset-password/{raw_token}", follow_redirects=True)
        self.assertIn(b"The password reset token is invalid, expired, or has already been used", reuse_resp.data)

        # Login with new password succeeds, old fails
        self.assertIsNotNone(database.verify_user_credentials("student_bob", "NewBobPassword@456"))
        self.assertIsNone(database.verify_user_credentials("student_bob", "StudentPass@123"))

    # =========================================================================
    # FEATURE 3: INPUT VALIDATION & BOUNDS TESTS
    # =========================================================================

    def test_registration_validation(self):
        csrf = self._get_csrf_token("/register")
        # Short password
        resp1 = self.client.post("/register", data={
            "csrf_token": csrf,
            "username": "valid_user",
            "email": "user@example.com",
            "password": "123",
            "confirm_password": "123",
        })
        self.assertEqual(resp1.status_code, 400)
        self.assertIn(b"at least 8 characters", resp1.data)

        # Mismatched passwords
        resp2 = self.client.post("/register", data={
            "csrf_token": csrf,
            "username": "valid_user2",
            "email": "user2@example.com",
            "password": "Password@123",
            "confirm_password": "DifferentPassword@456",
        })
        self.assertEqual(resp2.status_code, 400)
        self.assertIn(b"Passwords do not match", resp2.data)

    def test_quiz_crud_input_validation(self):
        self._login("prof_smith", "ProfPass@123")
        csrf = self._get_csrf_token("/quizzes/create")

        # Invalid pass percentage
        resp = self.client.post("/quizzes/create", data={
            "csrf_token": csrf,
            "title": "Invalid Bounds Quiz",
            "description": "Test",
            "time_limit_mins": 10,
            "pass_percentage": 150,  # Invalid: > 100
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Pass percentage must be between 0 and 100", resp.data)

    # =========================================================================
    # FEATURE 4: AUDIT TRAIL VERIFICATION
    # =========================================================================

    def test_audit_trail_captures_all_security_events(self):
        self._login("sysadmin", "AdminPass@123")
        csrf = self._get_csrf_token("/quizzes/create")

        # Create Quiz
        self.client.post("/quizzes/create", data={
            "csrf_token": csrf,
            "title": "Audited Quiz Module",
            "description": "Description",
            "time_limit_mins": 15,
            "pass_percentage": 60.0,
        })

        # Query audit logs
        logs = database.get_audit_logs(limit=20)
        event_types = [l["event_type"] for l in logs]
        self.assertIn("QUIZ_CREATED", event_types)
        self.assertIn("AUTH_LOGIN_SUCCESS", event_types)

    # =========================================================================
    # FEATURE 5: SENSITIVE DATA PROTECTION & HEADERS
    # =========================================================================

    def test_security_headers_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_answer_keys_not_exposed_in_client_quiz_view(self):
        response = self.client.get(f"/quizzes/{self.quiz_id}")
        self.assertNotIn(b"correct_option", response.data)
        self.assertNotIn(b"answer_key", response.data)

    # =========================================================================
    # BASE SYSTEM CRUD: QUIZZES, QUESTIONS, ATTEMPTS & RESULTS
    # =========================================================================

    def test_full_quiz_crud_lifecycle(self):
        self._login("prof_smith", "ProfPass@123")
        csrf = self._get_csrf_token("/quizzes/create")

        # 1. CREATE
        create_resp = self.client.post("/quizzes/create", data={
            "csrf_token": csrf,
            "title": "Total Quality Fundamentals 101",
            "description": "Module covering Deming 14 points and Kaizen",
            "time_limit_mins": 20,
            "pass_percentage": 50.0,
        }, follow_redirects=True)
        self.assertEqual(create_resp.status_code, 200)
        self.assertIn(b"Total Quality Fundamentals 101", create_resp.data)

        quizzes = database.get_all_quizzes()
        created = next(q for q in quizzes if q["title"] == "Total Quality Fundamentals 101")
        quiz_id = created["id"]

        # 2. READ
        read_resp = self.client.get(f"/quizzes/{quiz_id}")
        self.assertEqual(read_resp.status_code, 200)
        self.assertIn(b"Total Quality Fundamentals 101", read_resp.data)

        # 3. UPDATE
        edit_csrf = self._get_csrf_token(f"/quizzes/{quiz_id}/edit")
        update_resp = self.client.post(f"/quizzes/{quiz_id}/edit", data={
            "csrf_token": edit_csrf,
            "title": "Total Quality Fundamentals (Updated)",
            "description": "Updated syllabus",
            "time_limit_mins": 25,
            "pass_percentage": 65.0,
        }, follow_redirects=True)
        self.assertEqual(update_resp.status_code, 200)
        self.assertIn(b"Total Quality Fundamentals (Updated)", update_resp.data)

        # 4. DELETE
        delete_csrf = self._get_csrf_token("/quizzes/manage")
        del_resp = self.client.post(f"/quizzes/{quiz_id}/delete", data={
            "csrf_token": delete_csrf,
        }, follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(database.get_quiz_by_id(quiz_id))

    def test_full_question_crud_lifecycle(self):
        self._login("prof_smith", "ProfPass@123")
        csrf = self._get_csrf_token(f"/quizzes/{self.quiz_id}/questions/add")

        # 1. CREATE Question
        create_q = self.client.post(f"/quizzes/{self.quiz_id}/questions/add", data={
            "csrf_token": csrf,
            "text": "What is the primary objective of Six Sigma methodology?",
            "opt_a": "Defect reduction to 3.4 DPMO",
            "opt_b": "Increasing product price",
            "opt_c": "Maximizing server latency",
            "opt_d": "Eliminating automated testing",
            "correct_opt": "A",
            "marks": 2,
        }, follow_redirects=True)
        self.assertEqual(create_q.status_code, 200)
        self.assertIn(b"Six Sigma methodology", create_q.data)

        questions = database.get_questions_by_quiz(self.quiz_id)
        created_q = next(q for q in questions if "Six Sigma" in q["question_text"])
        q_id = created_q["id"]

        # 2. READ Question (with correct option visible to instructor)
        self.assertEqual(created_q["correct_option"], "A")
        self.assertEqual(created_q["marks"], 2)

        # 3. UPDATE Question
        edit_csrf = self._get_csrf_token(f"/questions/{q_id}/edit")
        update_q = self.client.post(f"/questions/{q_id}/edit", data={
            "csrf_token": edit_csrf,
            "text": "What is the primary objective of Six Sigma methodology? (Updated)",
            "opt_a": "Defect reduction to 3.4 DPMO",
            "opt_b": "Cost cutting",
            "opt_c": "Overtime elimination",
            "opt_d": "Zero documentation",
            "correct_opt": "A",
            "marks": 3,
        }, follow_redirects=True)
        self.assertEqual(update_q.status_code, 200)
        updated = database.get_question_by_id(q_id)
        self.assertEqual(updated["marks"], 3)
        self.assertIn("(Updated)", updated["question_text"])

        # 4. DELETE Question
        del_csrf = self._get_csrf_token(f"/quizzes/{self.quiz_id}/questions")
        del_q = self.client.post(f"/questions/{q_id}/delete", data={
            "csrf_token": del_csrf,
        }, follow_redirects=True)
        self.assertEqual(del_q.status_code, 200)
        self.assertIsNone(database.get_question_by_id(q_id))

    def test_results_and_gradebook_role_access(self):
        # Save a sample attempt
        database.save_attempt(
            student_name="Bob Student",
            student_roll="BOB-101",
            quiz_id=self.quiz_id,
            score=5,
            total_marks=5,
            percentage=100.0,
            status="Passed",
            user_id=self.student_id
        )

        # 1. Staff sees global gradebook with all students
        self._login("prof_smith", "ProfPass@123")
        staff_resp = self.client.get("/results")
        self.assertEqual(staff_resp.status_code, 200)
        self.assertIn(b"Student Examination Gradebook", staff_resp.data)
        self.assertIn(b"Bob Student", staff_resp.data)
        self.assertIn(b"BOB-101", staff_resp.data)

        # 2. Student sees their own personal results
        self._login("student_bob", "StudentPass@123")
        student_resp = self.client.get("/results")
        self.assertEqual(student_resp.status_code, 200)
        self.assertIn(b"My Quiz Examination Results", student_resp.data)
        self.assertIn(b"100.0%", student_resp.data)

    def test_health_check_endpoint(self):
        """Verify /health endpoint returns HTTP 200 and operational health JSON."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/json")
        data = resp.get_json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("database"), "connected")
        self.assertEqual(data.get("course"), "BBAT104")
        self.assertEqual(data.get("quality_goal"), "Q04 - Improve Security")


if __name__ == "__main__":
    unittest.main()

