from __future__ import annotations

import unittest
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts.provider_clients import (
    actor_id,
    build_ted_search_body,
    normalize_apify_items,
    overpass_query,
)
import build_shortlist
from import_discovery import overpass_timeout, read_rows, source_access_limitation
from qa_leads import contact_email_status_summary, provider_limitation
from runtime_config import RuntimeConfig


class ProviderClientTests(unittest.TestCase):
    def test_actor_id_uses_apify_api_tilde_format(self):
        self.assertEqual(actor_id("apify/google-search-scraper"), "apify~google-search-scraper")
        self.assertEqual(actor_id("apify~google-search-scraper"), "apify~google-search-scraper")

    def test_ted_body_is_bounded_and_requests_required_fields(self):
        body = build_ted_search_body("meter replacement", limit=250)
        self.assertEqual(body["limit"], 250)
        self.assertEqual(body["paginationMode"], "PAGE_NUMBER")
        self.assertEqual(body["query"], 'FT~"meter replacement"')
        self.assertIn("buyer-name", body["fields"])
        self.assertIn("publication-number", body["fields"])

    def test_normalize_apify_items_keeps_source_provenance(self):
        rows = normalize_apify_items([{"title": "Example", "url": "https://example.com"}], actor="apify/google-search-scraper", run_id="run-1")
        self.assertEqual(rows[0]["company_name"], "Example")
        self.assertEqual(rows[0]["source_url"], "https://example.com")
        self.assertEqual(rows[0]["actor_id"], "apify/google-search-scraper")
        self.assertEqual(rows[0]["actor_run_id"], "run-1")

    def test_normalize_apify_items_flattens_google_organic_results(self):
        rows = normalize_apify_items([{"organicResults": [{"title": "Example", "url": "https://example.com"}]}], actor="apify/google-search-scraper", run_id="run-1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company_name"], "Example")

    def test_overpass_retries_capacity_errors(self):
        session = Mock()
        first = Mock(status_code=502, ok=False)
        second = Mock(status_code=200, ok=True)
        second.json.return_value = {"elements": [{"id": 1}]}
        session.get.side_effect = [first, second]
        payload = overpass_query("https://overpass.example/api/interpreter", "query", session=session, retries=1)
        self.assertEqual(payload["elements"], [{"id": 1}])
        self.assertEqual(session.get.call_count, 2)

    def test_public_contact_lookup_returns_empty_tuple_on_blank_url(self):
        self.assertEqual(build_shortlist.fetch_contacts("", Mock()), ("", "", ""))

    def test_source_access_limitation_does_not_mark_successful_rows_unavailable(self):
        self.assertEqual(source_access_limitation({}, [{"company_name": "Example"}]), "")
        self.assertEqual(source_access_limitation({}, []), "optional provider unavailable")
        self.assertEqual(source_access_limitation({"reason": "capacity"}, [{"company_name": "Example"}]), "capacity")

    def test_overpass_timeout_has_thirty_second_floor(self):
        self.assertEqual(overpass_timeout(RuntimeConfig(request_timeout_seconds=15)), 30)
        self.assertEqual(overpass_timeout(RuntimeConfig(request_timeout_seconds=45)), 45)

    def test_read_rows_accepts_normalized_apify_fields(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "apify.json"
            path.write_text(json.dumps({"items": [{"company_name": "Example", "source_url": "https://example.com", "source_record_id": "1"}]}), encoding="utf-8")
            rows = read_rows(path, "Apify")
        self.assertEqual(rows[0]["company_name"], "Example")
        self.assertEqual(rows[0]["source_url"], "https://example.com")
        self.assertEqual(rows[0]["source_type"], "Apify")
        self.assertEqual(rows[0]["source_record_id"], "1")
        self.assertIn("discovery_source_url", rows[0])

    def test_qa_provider_limitation_reflects_configured_credentials(self):
        configured = RuntimeConfig(apify_api_token="token", hunter_api_key="key", ted_api_base_url="https://ted.example")
        self.assertNotIn("all provider credentials were not configured", provider_limitation(configured).lower())
        self.assertIn("not configured", provider_limitation(RuntimeConfig()).lower())

    def test_contact_email_status_summary_preserves_unverified_count(self):
        summary = contact_email_status_summary([
            {"contact_email": "published@example.com", "verification_status": "Published"},
            {"contact_email": "verified@example.com", "verification_status": "Verified"},
            {"contact_email": "unverified@example.com", "verification_status": "Unverified"},
            {"contact_email": "Unknown", "verification_status": "Not found"},
        ])
        self.assertEqual(summary, {"Published": 1, "Verified": 1, "Unverified": 1})


if __name__ == "__main__":
    unittest.main()
