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
            manifest.write_text(json.dumps({"run_id": "run-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "inputs": {}, "outputs": {}, "barriers": {}}), encoding="utf-8")
            argv = ["orchestrate_enrichment.py", "run", "--root", str(root), "--manifest", str(manifest), "--shortlist", str(shortlist), "--fixture"]
            with patch.object(sys, "argv", argv):
                self.assertEqual(orchestrate_enrichment.main(), 0)
            result = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(result["barriers"]["research"])
            self.assertTrue(result["barriers"]["verifier"])
            self.assertEqual(len(result["research_runs"]["signals"]), 30)
            self.assertEqual(len(result["research_runs"]["portfolio"]), 30)
            self.assertEqual(len(result["research_runs"]["contacts"]), 30)


if __name__ == "__main__":
    unittest.main()
