from __future__ import annotations

import unittest

import app


class DiscoveryWarningTest(unittest.TestCase):
    def test_discovery_get_handles_dict_and_object(self) -> None:
        discovery_dict = {"warning": "dictionary warning", "models": ["demo-model"]}

        class DiscoveryObject:
            warning = "object warning"
            models = ["real-model"]

        self.assertEqual(app._discovery_get(discovery_dict, "warning"), "dictionary warning")
        self.assertEqual(app._discovery_get(discovery_dict, "models", []), ["demo-model"])
        self.assertEqual(app._discovery_get(DiscoveryObject(), "warning"), "object warning")
        self.assertEqual(app._discovery_get(DiscoveryObject(), "models", []), ["real-model"])
        self.assertIsNone(app._discovery_get(None, "warning"))


if __name__ == "__main__":
    unittest.main()
