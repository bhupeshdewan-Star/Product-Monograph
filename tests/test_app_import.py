from __future__ import annotations

import importlib
import unittest


class AppImportTest(unittest.TestCase):
    def test_app_and_config_import(self) -> None:
        app = importlib.import_module("app")
        config = importlib.import_module("config")

        self.assertIsNotNone(app)
        self.assertIsNotNone(config)

        required = [
            "APP_NAME",
            "APP_TAGLINE",
            "APP_VERSION",
            "MEDICAL_DISCLAIMER",
            "APP_BUILD",
            "APP_THEME",
            "APP_COPYRIGHT",
            "APP_OWNER",
            "APP_RELEASE_DATE",
        ]
        for name in required:
            with self.subTest(name=name):
                self.assertTrue(hasattr(config, name), msg=f"Missing config constant: {name}")
                self.assertIsNotNone(getattr(config, name))

        self.assertTrue(hasattr(app, "main"))


if __name__ == "__main__":
    unittest.main()
