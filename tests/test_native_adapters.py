from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from worker_dispatch import NativeExecutorConfig, dispatch_native_lane, reconcile_lane_outputs


class NativeAdapterTests(unittest.TestCase):
    def test_dispatch_discards_stale_output_and_honors_nonzero_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"
            output_dir.mkdir(parents=True)
            stale = output_dir / "signals-C1.json"
            stale.write_text("stale", encoding="utf-8")
            state = root / "attempts.txt"
            code = "from pathlib import Path; import json, sys; state=Path(sys.argv[1]); count=int(state.read_text() or '0') if state.exists() else 0; state.write_text(str(count + 1));\nif count < 1: raise SystemExit(1)\nPath(sys.argv[2]).write_text(json.dumps({'research_run': {}, 'claims': []}))"

            def command_builder(item, output_path, config):
                return [sys.executable, "-c", code, str(state), str(output_path)]

            records = dispatch_native_lane([{"company_id": "C1"}], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default", max_retries=1), command_builder=command_builder)
            self.assertEqual(records[0]["status"], "succeeded")
            self.assertEqual(records[0]["attempts"], 2)
            self.assertTrue((output_dir / "signals-C1.json").exists())

    def test_reconciliation_rejects_tampered_payload_and_non_object_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "company_name": "Company", "trusted_domain": "example.de", "location": "Berlin", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "hash"}
            code = "from pathlib import Path; import json, sys; Path(sys.argv[1]).write_text(json.dumps({'research_run': {'run_id': 'run-1:signals:C1', 'campaign_id': 'campaign-1', 'company_id': 'C1', 'scope': 'signals:C1', 'scope_version': 'v1', 'scope_hash': 'hash'}, 'claims': [1]}))"

            def command_builder(queue_item, output_path, config):
                return [sys.executable, "-c", code, str(output_path)]

            records = dispatch_native_lane([item], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default"), command_builder=command_builder)
            with self.assertRaisesRegex(ValueError, "claims are not objects"):
                reconcile_lane_outputs(records, [item], "run-1", "signals")
            (output_dir / "signals-C1.json").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                reconcile_lane_outputs(records, [item], "run-1", "signals")

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
