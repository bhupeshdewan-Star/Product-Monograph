from __future__ import annotations

import unittest

import app


class AppSmokeTest(unittest.TestCase):
    def test_app_entrypoint_and_theme_shell_exist(self) -> None:
        self.assertTrue(callable(app.main))

        style = app._theme_styles("Light Mode")
        self.assertIn("--pmono-bg", style)
        self.assertIn(".stApp", style)


if __name__ == "__main__":
    unittest.main()
