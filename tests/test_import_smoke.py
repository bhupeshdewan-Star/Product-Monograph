from __future__ import annotations

import unittest


class ImportSmokeTest(unittest.TestCase):
    def test_app_imports(self) -> None:
        import app  # noqa: F401

    def test_core_packages_import(self) -> None:
        from src.monograph import generator  # noqa: F401
        from src.agents.api import server  # noqa: F401


if __name__ == "__main__":
    unittest.main()
