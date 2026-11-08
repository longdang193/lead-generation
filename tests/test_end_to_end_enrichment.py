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
from run_manifest import entry


class EndToEndEnrichmentTests(unittest.TestCase):
    def test_fixture_run_reconciles_all_lanes_and_records_barriers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            with shortlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain", "city", "resolution_status"])
                writer.writeheader()
                for index in range(30):
                    writer.writerow({"company_id": f"C{index:02d}", "company_name": f"Company {index:02d}", "domain": f"company{index:02d}.de", "city": "Berlin", "resolution_status": "Accepted"})
            manifest = root / "evidence" / "manifests" / "active_run.json"
            manifest.parent.mkdir(parents=True)
            revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            manifest.write_text(json.dumps({"run_id": "run-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "generated_at": "2026-11-08T00:00:00+00:00", "accepted_company_ids": [f"C{index:02d}" for index in range(30)], "inputs": {"provisional_shortlist": entry(root, shortlist)}, "outputs": {}, "barriers": {}}), encoding="utf-8")
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
            self.assertTrue(all(row["buying_signal"] == "Strong" for row in priority_rows))
            self.assertTrue(all(row["sales_priority"] == "Pursue" for row in priority_rows))
            self.assertEqual((root / "evidence" / "reports" / "run-1" / "qa.md").read_text(encoding="utf-8").count("Errors: 0"), 1)


if __name__ == "__main__":
    unittest.main()
