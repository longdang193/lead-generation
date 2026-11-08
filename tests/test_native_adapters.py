from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class NativeAdapterTests(unittest.TestCase):
    def test_repository_owned_worker_and_verifier_execute(self):
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data" / "intermediate").mkdir(parents=True)
            (root / "data" / "processed").mkdir(parents=True)
            (root / "data" / "intermediate" / "website_evidence_2026-11-08.jsonl").write_text("\n", encoding="utf-8")
            with (root / "data" / "processed" / "contacts_2026-11-08.csv").open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=["company_id", "contact_name"]).writeheader()
            with (root / "data" / "intermediate" / "companies_normalized_2026-11-07.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain"])
                writer.writeheader()
                writer.writerow({"company_id": "C1", "company_name": "Example Hausverwaltung", "domain": "example.de"})
            worker_output = root / "worker.jsonl"
            worker = subprocess.run([
                sys.executable,
                str(repository_root / "scripts" / "native_worker.py"),
                "--repo-root", str(root),
                "--profile", "default",
                "--run-id", "run-1",
                "--lane", "signals",
                "--company-id", "C1",
                "--output", str(worker_output),
            ], check=False, capture_output=True, text=True)
            self.assertEqual(worker.returncode, 0, worker.stderr)
            payload = json.loads(worker_output.read_text(encoding="utf-8"))
            self.assertEqual(payload["research_run"]["status"], "Completed")
            self.assertEqual(payload["research_run"]["provider_status"], "Available")
            verifier_input = root / "claims.jsonl"
            verifier_input.write_text("", encoding="utf-8")
            verifier_output = root / "verifier.jsonl"
            verifier = subprocess.run([
                sys.executable,
                str(repository_root / "scripts" / "native_verifier.py"),
                "--repo-root", str(root),
                "--profile", "evidence-verifier",
                "--run-id", "run-1",
                "--lane", "verifier",
                "--company-id", "C1",
                "--claims", str(verifier_input),
                "--output", str(verifier_output),
            ], check=False, capture_output=True, text=True)
            self.assertEqual(verifier.returncode, 0, verifier.stderr)
            self.assertEqual(json.loads(verifier_output.read_text(encoding="utf-8"))["decisions"], [])


if __name__ == "__main__":
    unittest.main()
