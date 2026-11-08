from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from import_discovery import read_rows, refresh_identity


class DiscoveryTests(unittest.TestCase):
    def test_json_provider_fields_are_preserved(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "provider.json"
            path.write_text(json.dumps({"items": [{"name": "Example GmbH", "website": "https://example.de", "address": "Alexanderplatz 1", "postcode": "10178", "city": "Berlin", "contact:email": "info@example.de"}]}), encoding="utf-8")
            row = read_rows(path, "Apify")[0]
        self.assertEqual(row["company_name"], "Example GmbH")
        self.assertEqual(row["postal_code"], "10178")
        self.assertEqual(row["city"], "Berlin")
        self.assertEqual(row["source_url"], "https://example.de")

    @patch("import_discovery.requests.get")
    def test_vdiv_refresh_repairs_url_shaped_identity(self, get):
        response = Mock(ok=True, text="<html><title>Example Hausverwaltung GmbH | Berlin</title><body>10178 Berlin</body></html>")
        get.return_value = response
        row = refresh_identity({"source_type": "VDIV", "company_name": "www.example.de", "source_url": "https://example.de", "address": ""}, 5)
        self.assertEqual(row["company_name"], "Example Hausverwaltung GmbH")
        self.assertEqual(row["postal_code"], "10178")
        self.assertEqual(row["identity_status"], "Refreshed")


if __name__ == "__main__":
    unittest.main()
