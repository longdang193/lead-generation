from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import import_discovery
from import_discovery import provider_output_paths, read_rows, refresh_identity
from runtime_config import RuntimeConfig


class DiscoveryTests(unittest.TestCase):
    def test_invalid_runtime_integer_is_reported_before_provider_calls(self):
        with TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text("REQUEST_TIMEOUT_SECONDS=not-an-integer\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REQUEST_TIMEOUT_SECONDS must be an integer"):
                RuntimeConfig.from_env(env)

    def test_process_environment_overrides_dotenv_and_works_without_dotenv(self):
        with TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text("RUN_DEADLINE_SECONDS=900\nMAX_TOTAL_ATTEMPTS=100\n", encoding="utf-8")
            with patch.dict(os.environ, {"RUN_DEADLINE_SECONDS": "1", "MAX_TOTAL_ATTEMPTS": "1"}, clear=False):
                configured = RuntimeConfig.from_env(env)
            self.assertEqual(configured.run_deadline_seconds, 1)
            self.assertEqual(configured.max_total_attempts, 1)
            with patch.dict(os.environ, {"RUN_DEADLINE_SECONDS": "2", "MAX_TOTAL_ATTEMPTS": "3"}, clear=False):
                no_file = RuntimeConfig.from_env(Path(directory) / "missing.env")
            self.assertEqual(no_file.run_deadline_seconds, 2)
            self.assertEqual(no_file.max_total_attempts, 3)

    def test_fetch_provider_outputs_have_safe_defaults(self):
        apify, overpass = provider_output_paths(None, None, root=Path("C:/tmp/run"))
        self.assertEqual(apify, Path("C:/tmp/run/data/raw/apify.json"))
        self.assertEqual(overpass, Path("C:/tmp/run/data/raw/overpass.json"))

    def test_apify_budget_below_provider_minimum_is_rejected_before_calls(self):
        config = RuntimeConfig(apify_max_spend_usd=0.01)
        self.assertEqual(
            config.validate(provider="apify"),
            ["APIFY_MAX_SPEND_USD must be at least 0.50 for Apify"],
        )

    @patch("import_discovery.run_apify_actor")
    @patch.object(import_discovery.RuntimeConfig, "from_env")
    def test_fetch_providers_rejects_invalid_apify_budget_before_call(self, from_env, run_apify_actor):
        from_env.return_value = RuntimeConfig(apify_api_token="configured", apify_max_spend_usd=0.01, overpass_api_url="")
        with TemporaryDirectory() as directory, patch.object(sys, "argv", ["import_discovery.py", "--fetch-providers", "--output", str(Path(directory) / "discovery.csv")]):
            self.assertEqual(import_discovery.main(), 2)
        run_apify_actor.assert_not_called()

    @patch("import_discovery.overpass_query")
    @patch("import_discovery.run_apify_actor")
    @patch.object(import_discovery.RuntimeConfig, "from_env")
    def test_fetch_providers_rejects_zero_and_nonfinite_apify_budgets_before_calls(self, from_env, run_apify_actor, overpass_query):
        for budget in (0.0, float("nan"), float("inf")):
            from_env.return_value = RuntimeConfig(apify_api_token="configured", apify_max_spend_usd=budget, overpass_api_url="configured")
            with self.subTest(budget=budget), TemporaryDirectory() as directory, patch.object(sys, "argv", ["import_discovery.py", "--fetch-providers", "--output", str(Path(directory) / "discovery.csv")]):
                self.assertEqual(import_discovery.main(), 2)
            run_apify_actor.assert_not_called()
            overpass_query.assert_not_called()
            run_apify_actor.reset_mock()
            overpass_query.reset_mock()

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

    @patch("import_discovery.requests.get")
    def test_vdiv_refresh_rejects_navigation_title_as_identity(self, get):
        response = Mock(ok=True, text="<html><title>Über uns | Example Hausverwaltung</title><body>10178 Berlin</body></html>")
        get.return_value = response
        row = refresh_identity({"source_type": "VDIV", "company_name": "www.example.de", "source_url": "https://example.de", "address": ""}, 5)
        self.assertEqual(row["company_name"], "www.example.de")
        self.assertEqual(row["identity_status"], "Review")


if __name__ == "__main__":
    unittest.main()
