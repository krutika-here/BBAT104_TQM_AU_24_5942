import unittest

from app import app


class FlaskApplicationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

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
            "/quizzes": b"Quiz Catalog &amp; Examination Portal",
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


if __name__ == "__main__":
    unittest.main()
