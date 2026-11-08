from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import collect_buying_signals


class BuyingSignalTests(unittest.TestCase):
    def test_shortlist_skips_ineligible_rows_before_applying_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text(
                "company_id,company_name,resolution_status\n"
                "C1,Company 1,Accepted\n"
                "C3,Company 3,Accepted\n"
                "C4,Company 4,Review\n",
                encoding="utf-8",
            )
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nMISSING\nC4\nC3\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=2)
            queries = []

            def fake_ted_search(_base_url, search_term, timeout, limit):
                queries.append(search_term)
                return []

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            self.assertEqual([query[0] for query in queries[::4]], ["Company 3", "Company 1"])

    def test_buyerless_notice_does_not_become_completed_no_match(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Alpha Hausverwaltung\n", encoding="utf-8")
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=30)

            def fake_ted_search(_base_url, search_term, timeout, limit):
                return [{"publication-number": "123", "links": {"html": {"ENG": "https://ted.example/notices/123"}}}]

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with audit.open(encoding="utf-8-sig", newline="") as handle:
                company_audit = next(row for row in csv.DictReader(handle) if row.get("company_id") == "C1" and row.get("research_status"))
            self.assertEqual(company_audit["research_status"], "Partial")
            self.assertEqual(company_audit["signal_state"], "Unknown")

    def test_mixed_verified_and_unattributable_notices_remain_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Alpha Hausverwaltung\n", encoding="utf-8")
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=30)

            def fake_ted_search(_base_url, search_term, timeout, limit):
                return [
                    {
                        "publication-number": "123",
                        "buyer-name": "Alpha Hausverwaltung GmbH",
                        "links": {"html": {"ENG": "https://ted.example/notices/123"}},
                    },
                    {"publication-number": "124", "links": {"html": {"ENG": "https://ted.example/notices/124"}}},
                ]

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with audit.open(encoding="utf-8-sig", newline="") as handle:
                company_audit = next(row for row in csv.DictReader(handle) if row.get("company_id") == "C1" and row.get("research_status"))
            self.assertEqual(company_audit["research_status"], "Partial")
            self.assertEqual(company_audit["signal_state"], "Unknown")

    def test_colliding_normalized_buyers_are_not_verified_in_scoped_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Alpha GmbH\nC2,Alpha AG\n", encoding="utf-8")
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=30)

            def fake_ted_search(_base_url, search_term, timeout, limit):
                return [{
                    "publication-number": "123",
                    "buyer-name": "Alpha GmbH",
                    "links": {"html": {"ENG": "https://ted.example/notices/123"}},
                }]

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with links.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.DictReader(handle)), [])

    def test_punctuated_ek_suffix_matches_verified_buyer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Müller Hausverwaltung\n", encoding="utf-8")
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=30)

            def fake_ted_search(_base_url, search_term, timeout, limit):
                return [{
                    "publication-number": "123",
                    "buyer-name": "Müller Hausverwaltung e.K.",
                    "links": {"html": {"ENG": "https://ted.example/notices/123"}},
                }]

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with links.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 1)

    def test_shortlist_preserves_rank_order_and_caps_account_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text(
                "company_id,company_name\n"
                + "\n".join(f"C{i},Company {i}" for i in range(1, 5))
                + "\n",
                encoding="utf-8",
            )
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC3\nC1\nC4\nC2\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=2)
            queries = []

            def fake_ted_search(_base_url, search_term, timeout, limit):
                queries.append(search_term)
                return []

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            self.assertEqual(len(queries), 8)
            self.assertTrue(all(query[0] == prefix for query, prefix in zip(queries, ["Company 3"] * 4 + ["Company 1"] * 4)))
            with audit.open(encoding="utf-8-sig", newline="") as handle:
                audit_rows = list(csv.DictReader(handle))
            searched_ids = [row["company_id"] for row in audit_rows if row.get("search_term")]
            self.assertEqual(searched_ids, ["C3"] * 4 + ["C1"] * 4)

    def test_shortlist_search_completes_no_match_only_after_all_account_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Alpha Hausverwaltung\nC2,Other Verwaltung\n", encoding="utf-8")
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id\nC1\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(ted_api_base_url="https://ted.example", request_timeout_seconds=1, max_priority_accounts=30)
            queries = []

            def fake_ted_search(_base_url, search_term, timeout, limit):
                queries.append(search_term)
                return []

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--shortlist", str(shortlist),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
                "--run-id", "test-run",
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with audit.open(encoding="utf-8-sig", newline="") as handle:
                audit_rows = list(csv.DictReader(handle))
            company_audit = next(row for row in audit_rows if row.get("company_id") == "C1" and row.get("research_status"))
            untouched_audit = next(row for row in audit_rows if row.get("company_id") == "C2" and row.get("research_status"))
            self.assertEqual(company_audit["research_status"], "Completed")
            self.assertEqual(company_audit["signal_state"], "None found")
            self.assertEqual(company_audit["search_status"], "Searched")
            self.assertEqual(untouched_audit["research_status"], "Not searched")
            self.assertEqual(untouched_audit["signal_state"], "Unknown")
            self.assertEqual(len(queries), 4)
            self.assertTrue(all(query[0] == "Alpha Hausverwaltung" for query in queries))
            self.assertEqual(json.loads(events.read_text(encoding="utf-8"))["status"], "Searched")

    def test_verified_company_event_match_completes_account_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name\nC1,Alpha Hausverwaltung\n", encoding="utf-8")
            events = root / "events.json"
            links = root / "links.csv"
            audit = root / "audit.csv"
            config = SimpleNamespace(
                ted_api_base_url="https://ted.example",
                request_timeout_seconds=1,
                max_priority_accounts=30,
            )

            def fake_ted_search(_base_url, search_term, timeout, limit):
                if search_term == "Zählertausch":
                    return [{
                        "publication-number": "123",
                        "buyer-name": "Alpha Hausverwaltung GmbH",
                        "notice-title": "Meter replacement",
                        "publication-date": "2026-11-01",
                        "deadline": "Unknown",
                        "buyer-country": "DE",
                        "links": {"html": {"eng": "https://ted.example/notices/123"}},
                    }]
                return []

            argv = [
                "collect_buying_signals.py",
                "--companies", str(companies),
                "--ted-output", str(events),
                "--links-output", str(links),
                "--audit-output", str(audit),
                "--run-id", "test-run",
            ]
            with patch.object(collect_buying_signals.RuntimeConfig, "from_env", return_value=config), patch.object(collect_buying_signals, "ted_search", side_effect=fake_ted_search), patch.object(sys, "argv", argv):
                self.assertEqual(collect_buying_signals.main(), 0)

            with audit.open(encoding="utf-8-sig", newline="") as handle:
                audit_rows = list(csv.DictReader(handle))
            company_audit = next(row for row in audit_rows if row.get("company_id") == "C1")
            self.assertEqual(company_audit["research_status"], "Completed")
            self.assertEqual(company_audit["search_status"], "Searched")
            self.assertEqual(company_audit["signal_state"], "Candidate")
            with links.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 1)
            self.assertEqual(json.loads(events.read_text(encoding="utf-8"))["status"], "Searched")


if __name__ == "__main__":
    unittest.main()
