from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from web_content import soup_from_response


class WebContentTests(unittest.TestCase):
    def test_response_bytes_preserve_utf8_text(self):
        response = SimpleNamespace(content="Über uns für Eigentümer".encode("utf-8"), text="�ber uns f�r Eigent�mer")
        self.assertIn("Über uns für Eigentümer", soup_from_response(response).get_text())

    def test_text_fallback_supports_lightweight_response_mocks(self):
        response = SimpleNamespace(text="Example Hausverwaltung")
        self.assertEqual(soup_from_response(response).get_text(), "Example Hausverwaltung")


if __name__ == "__main__":
    unittest.main()
