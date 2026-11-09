from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import orchestrate_enrichment
from campaign_spec import load_campaign_spec
from run_manifest import entry


class EndToEndEnrichmentTests(unittest.TestCase):
    def write_campaign(self, root: Path, name: str = "berlin-hausverwaltung.json") -> dict[str, object]:
        campaign_path = root / "config" / "campaigns" / name
        campaign_path.parent.mkdir(parents=True, exist_ok=True)
        source = Path(__file__).resolve().parents[1] / "config" / "campaigns" / name
        campaign_path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        return load_campaign_spec(root, campaign_path).manifest_record()

    def test_fixture_run_reconciles_all_lanes_and_records_barriers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            with shortlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain", "verified_company_domain", "city", "resolution_status"])
                writer.writeheader()
                for index in range(30):
                    writer.writerow({"company_id": f"C{index:02d}", "company_name": f"Company {index:02d}", "domain": f"company{index:02d}.de", "verified_company_domain": f"company{index:02d}.de", "city": "Berlin", "resolution_status": "Accepted"})
            manifest = root / "evidence" / "manifests" / "active_run.json"
            manifest.parent.mkdir(parents=True)
            revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            manifest.write_text(json.dumps({"run_id": "run-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "campaign": self.write_campaign(root), "generated_at": "2026-11-08T00:00:00+00:00", "accepted_company_ids": [f"C{index:02d}" for index in range(30)], "inputs": {"provisional_shortlist": entry(root, shortlist)}, "outputs": {}, "barriers": {}}), encoding="utf-8")
            argv = ["orchestrate_enrichment.py", "run", "--root", str(root), "--manifest", str(manifest), "--shortlist", str(shortlist), "--fixture"]
            with patch.object(sys, "argv", argv):
                self.assertEqual(orchestrate_enrichment.main(), 0)
            result = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(result["barriers"]["research"])
            self.assertTrue(result["barriers"]["verifier"])
            self.assertTrue(result["barriers"]["readiness"])
            self.assertTrue(result["barriers"]["published"])
            self.assertEqual(result["status"], "completed")
            research_runs = list(result["research_runs"].values())
            self.assertEqual(sum(item["research_type"] == "signals" for item in research_runs), 30)
            self.assertEqual(sum(item["research_type"] == "portfolio" for item in research_runs), 30)
            self.assertEqual(sum(item["research_type"] == "contacts" for item in research_runs), 30)
            priority_rows = list(csv.DictReader((root / "data" / "processed" / "run-1" / "priority.csv").open(encoding="utf-8", newline="")))
            self.assertEqual(len(priority_rows), 30)
            self.assertEqual({row["assurance_level"] for row in priority_rows}, {"replay"})
            self.assertEqual({row["provider_status"] for row in priority_rows}, {"Available"})
            self.assertEqual({row["research_gap"] for row in priority_rows}, {"None"})
            self.assertEqual({row["next_action"] for row in priority_rows}, {"Ready"})
            self.assertTrue(all(row["buying_signal"] == "Strong" for row in priority_rows))
            self.assertTrue(all(row["sales_priority"] == "Pursue" for row in priority_rows))
            self.assertEqual((root / "evidence" / "reports" / "run-1" / "qa.md").read_text(encoding="utf-8").count("Errors: 0"), 1)

    def test_fixture_small_campaign_reuses_controller_with_two_lanes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            with shortlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain", "verified_company_domain", "city", "resolution_status"])
                writer.writeheader()
                for index in range(5):
                    writer.writerow({"company_id": f"S{index:02d}", "company_name": f"Small Company {index:02d}", "domain": f"small{index:02d}.de", "verified_company_domain": f"small{index:02d}.de", "city": "Berlin", "resolution_status": "Accepted"})
            campaign = self.write_campaign(root, "fixture-small.json")
            manifest = root / "evidence" / "manifests" / "small_run.json"
            manifest.parent.mkdir(parents=True)
            revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            manifest.write_text(json.dumps({"run_id": "small-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "campaign": campaign, "generated_at": "2026-11-08T00:00:00+00:00", "accepted_company_ids": [f"S{index:02d}" for index in range(5)], "inputs": {"provisional_shortlist": entry(root, shortlist)}, "outputs": {}, "barriers": {}}), encoding="utf-8")
            argv = ["orchestrate_enrichment.py", "run", "--root", str(root), "--manifest", str(manifest), "--shortlist", str(shortlist), "--campaign-config", str(root / "config" / "campaigns" / "fixture-small.json"), "--fixture"]
            with patch.object(sys, "argv", argv):
                self.assertEqual(orchestrate_enrichment.main(), 0)
            result = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual({key for key in result["outputs"] if key.startswith("queue_")}, {"queue_contacts", "queue_portfolio"})
            self.assertEqual(len(result["research_runs"]), 10)
            self.assertEqual(result["campaign"]["campaign_id"], "fixture-small")

    def test_failed_semantic_qa_does_not_replace_existing_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            with shortlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain", "verified_company_domain", "city", "resolution_status"])
                writer.writeheader()
                for index in range(30):
                    writer.writerow({"company_id": f"C{index:02d}", "company_name": f"Company {index:02d}", "domain": f"company{index:02d}.de", "verified_company_domain": f"company{index:02d}.de", "city": "Berlin", "resolution_status": "Accepted"})
            manifest = root / "evidence" / "manifests" / "active_run.json"
            manifest.parent.mkdir(parents=True)
            revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            manifest.write_text(json.dumps({"run_id": "run-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "campaign": self.write_campaign(root), "generated_at": "2026-11-08T00:00:00+00:00", "accepted_company_ids": [f"C{index:02d}" for index in range(30)], "inputs": {"provisional_shortlist": entry(root, shortlist)}, "outputs": {}, "barriers": {}}), encoding="utf-8")
            final_output = root / "output" / "run-1.xlsx"
            final_output.parent.mkdir(parents=True)
            final_output.write_bytes(b"existing workbook")
            original_run = orchestrate_enrichment.subprocess.run

            def fail_semantic_qa(command, *args, **kwargs):
                if any("qa_leads.py" in str(part) for part in command):
                    return subprocess.CompletedProcess(command, 1, "", "forced semantic QA failure")
                return original_run(command, *args, **kwargs)

            argv = ["orchestrate_enrichment.py", "run", "--root", str(root), "--manifest", str(manifest), "--shortlist", str(shortlist), "--fixture"]
            with patch.object(sys, "argv", argv), patch.object(orchestrate_enrichment.subprocess, "run", side_effect=fail_semantic_qa):
                self.assertEqual(orchestrate_enrichment.main(), 1)
            self.assertEqual(final_output.read_bytes(), b"existing workbook")
            self.assertTrue((root / "output" / "run-1.staging.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
