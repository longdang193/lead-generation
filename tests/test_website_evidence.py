from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from extract_website_evidence import process
from runtime_config import RuntimeConfig


class WebsiteEvidenceTests(unittest.TestCase):
    @patch("extract_website_evidence.fetch")
    def test_berlin_claim_uses_page_containing_excerpt(self, fetch):
        fetch.side_effect = [
            ("https://example.de/", "Hausverwaltung Home page", ["https://example.de/leistungen-about"]),
            ("https://example.de/leistungen-about", "Unser Standort Berlin betreut Wohnanlagen.", []),
        ]
        result, _ = process(
            {"company_id": "C1", "source_url": "https://example.de/"},
            RuntimeConfig(max_pages_per_company=2),
        )
        berlin_claim = next(claim for claim in result["claims"] if claim["field"] == "berlin_relevance")
        self.assertEqual(berlin_claim["evidence_url"], "https://example.de/leistungen-about")
        self.assertIn("Berlin", berlin_claim["evidence_excerpt"])


if __name__ == "__main__":
    unittest.main()
