from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from orchestrate_enrichment import _native_command_builder
from worker_dispatch import NativeExecutorConfig, dispatch_fixture_lanes, dispatch_native_lane, reconcile_lane_outputs


class NativeAdapterTests(unittest.TestCase):
    def validate_research_run(self, research_run: dict[str, object]) -> None:
        schema = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(research_run)

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

    def test_personal_reconciliation_keeps_successful_outputs_when_one_worker_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"

            def command_builder(item, output_path, config):
                if item["company_id"] == "C2":
                    return [sys.executable, "-c", "raise SystemExit(1)"]
                return [sys.executable, "-c", "from pathlib import Path; import json,sys; Path(sys.argv[1]).write_text(json.dumps({'research_run': {'run_id': 'run-1:signals:C1', 'campaign_id': 'campaign-1', 'company_id': 'C1', 'scope': 'signals:C1', 'scope_version': 'v1', 'scope_hash': 'hash'}, 'claims': []}))", str(output_path)]

            queue = [
                {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "hash"},
                {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C2", "lane": "signals", "scope": "signals:C2", "scope_version": "v1", "scope_hash": "hash"},
            ]
            records = dispatch_native_lane(queue, "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default", max_retries=0, max_workers=1), command_builder=command_builder)
            self.assertEqual([record["status"] for record in records], ["succeeded", "failed"])
            reconcile_lane_outputs(records, queue, "run-1", "signals", allow_partial=True)

    def test_verifier_reconciliation_rejects_foreign_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims_path = root / "claims.jsonl"
            claim = {"candidate_claim_id": "claim-1", "candidate_sha256": "a" * 64}
            claims_path.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            output_dir = root / "evidence" / "verifier" / "run-1" / "outputs"
            output_dir.mkdir(parents=True)
            output_path = output_dir / "verifier-C1.json"
            output_path.write_text(json.dumps({"decisions": [{"candidate_claim_id": "foreign", "candidate_sha256": "b" * 64}]}), encoding="utf-8")
            item = {"run_id": "run-1", "lane": "verifier", "company_id": "C1", "claims_path": claims_path}
            records = [{"run_id": "run-1", "lane": "verifier", "company_id": "C1", "status": "succeeded", "output_path": output_path.as_posix(), "output_sha256": __import__("hashlib").sha256(output_path.read_bytes()).hexdigest(), "attempts": 1}]
            with self.assertRaisesRegex(ValueError, "foreign decision"):
                reconcile_lane_outputs(records, [item], "run-1", "verifier")

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
            self.assertEqual(payload["research_run"]["status"], "Not searched")
            self.assertEqual(payload["research_run"]["provider_status"], "Unavailable")
            self.validate_research_run(payload["research_run"])
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

            fixture_item = {"run_id": "run-1", "lane": "signals", "company_id": "C1", "company_name": "Company", "trusted_domain": "example.de", "location": "Berlin", "campaign_id": "campaign-1", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "a" * 64}
            fixture_results = dispatch_fixture_lanes({"signals": [fixture_item]}, "run-1", root / "fixture")
            fixture_payload = json.loads(Path(fixture_results["signals"][0]["output_path"]).read_text(encoding="utf-8"))
            self.validate_research_run(fixture_payload["research_run"])

    def test_native_verifier_accepts_controller_scope_command(self):
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims = root / "claims.jsonl"
            claims.write_text("", encoding="utf-8")
            output = root / "verifier.json"
            item = {
                "run_id": "run-1",
                "campaign_id": "campaign-1",
                "lane": "verifier",
                "company_id": "C1",
                "company_name": "Company",
                "trusted_domain": "example.de",
                "location": "Berlin",
                "scope_version": "admitted-work-item-v1",
                "scope_hash": "a" * 64,
            }
            command = _native_command_builder(
                item,
                output,
                NativeExecutorConfig(sys.executable, "evidence-verifier", adapter_args=(str(repository_root / "scripts" / "native_verifier.py"), "--repo-root", str(root))),
            ) + ["--claims", str(claims)]
            result = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["decisions"], [])


if __name__ == "__main__":
    unittest.main()
