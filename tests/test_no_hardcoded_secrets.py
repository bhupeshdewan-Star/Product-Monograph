from __future__ import annotations

import re
from pathlib import Path
import unittest


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])(?:OPENAI|ANTHROPIC|GOOGLE|GROQ|DEEPSEEK|OPENROUTER)_API_KEY\s*=\s*['\"][^'\"]{12,}['\"]"),
]


class HardcodedSecretsTest(unittest.TestCase):
    def test_no_high_entropy_api_keys_in_source(self) -> None:
        root = Path(__file__).resolve().parents[1]
        files = [
            path
            for path in root.rglob("*.py")
            if "tests" not in path.parts and "__pycache__" not in path.parts
        ]

        violations: list[str] = []
        for path in files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    violations.append(str(path))
                    break

        self.assertEqual(violations, [], f"Potential hardcoded secrets found: {violations}")


if __name__ == "__main__":
    unittest.main()
