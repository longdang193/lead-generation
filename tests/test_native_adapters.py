from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from orchestrate_enrichment import _native_command_builder, build_verifier_queue
from lead_contract import candidate_claim_id, candidate_sha256
from promote_evidence import promote_verified_claims
from action_lifecycle import replay_lifecycle
from worker_dispatch import DispatchBudget, NativeExecutorConfig, _execution_fingerprints, dispatch_fixture_lanes, dispatch_native_lane, reconcile_lane_outputs, split_material_gap_queue
from run_manifest import atomic_write


class NativeAdapterTests(unittest.TestCase):
    def validate_research_run(self, research_run: dict[str, object]) -> None:
        schema = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(research_run)

    def write_cache_evidence(self, output: Path, item: dict[str, object], *, lane: str = "signals", claims_input: Path | None = None) -> None:
        cache_item = {**item, "profile": "default", "executable": sys.executable, "adapter_args": []}
        evidence = {"run_id": "run-1", "lane": lane, "company_id": item["company_id"], "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        evidence["payload_sha256"] = evidence["output_sha256"]
        evidence["fingerprints"] = _execution_fingerprints(cache_item, "run-1", lane)
        if claims_input is not None:
            evidence["claims_input_sha256"] = hashlib.sha256(claims_input.read_bytes()).hexdigest()
        output.with_name(output.name + ".meta.json").write_text(json.dumps(evidence), encoding="utf-8")

    def valid_research_payload(self, item: dict[str, object], run_id: str = "run-1") -> dict[str, object]:
        return {"research_run": {
            "record_type": "ResearchRun",
            "run_id": f"{run_id}:signals:{item['company_id']}",
            "campaign_id": item["campaign_id"],
            "company_id": item["company_id"],
            "research_type": "signals",
            "source": "fixture",
            "scope": item["scope"],
            "status": "Completed",
            "started_at": "2026-11-08T00:00:00+00:00",
            "completed_at": "2026-11-08T00:00:01+00:00",
            "result_count": 0,
            "truncated": False,
            "provider_status": "Available",
            "adapter_capability": "replay",
            "assurance_level": "replay",
            "scope_version": item["scope_version"],
            "scope_hash": item["scope_hash"],
            "attempts": [{"attempt_id": "attempt-1", "query_or_source": "fixture", "status": "Completed", "truncated": False}],
        }, "claims": []}

    def test_dispatch_reuses_valid_terminal_output_without_rerunning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"
            output_dir.mkdir(parents=True)
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            output = output_dir / "signals-C1.json"
            output.write_text(json.dumps(self.valid_research_payload(item)), encoding="utf-8")
            self.write_cache_evidence(output, item)
            def should_not_run(*args):
                raise AssertionError("valid terminal output was not reused")
            records = dispatch_native_lane([item], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default"), command_builder=should_not_run)
            self.assertEqual(records[0]["status"], "succeeded")
            self.assertTrue(records[0]["reused_terminal"])
            self.assertEqual(records[0]["attempts"], 0)

    def test_dispatch_stops_when_shared_attempt_budget_is_exhausted(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "candidate"
            output_dir.mkdir(parents=True)
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            budget = DispatchBudget(60, 1)
            deterministic_command = lambda queue_item, output_path, config: [sys.executable, "-c", "raise SystemExit(2)"]
            first = dispatch_native_lane([item], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default", max_retries=1), command_builder=deterministic_command, budget=budget)
            second = dispatch_native_lane([{**item, "company_id": "C2"}], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default", max_retries=1), command_builder=deterministic_command, budget=budget)
            self.assertEqual(first[0]["failure_class"], "deterministic")
            self.assertEqual(second[0]["failure_class"], "budget_exhausted")

    def test_lifecycle_bound_dispatch_settles_each_retry_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            atomic_write(manifest_path, {
                "run_id": "run-1",
                "budget_limit": 3,
                "authorization": {
                    "accepted_company_ids": ["C1"],
                    "allowed_action_types": ["signals"],
                    "scope_prefixes": {"signals": "signals:"},
                    "campaign_id": "campaign-1",
                    "campaign_version": "v1",
                    "scope_version": "admitted-work-item-v1",
                    "contract_version": "1",
                    "strategy_version": "1",
                    "profile_versions": {"signals": "signals-v1"},
                },
            })
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"
            attempts = {"count": 0}

            def command_builder(item, output_path, config):
                attempts["count"] += 1
                if attempts["count"] < 2:
                    return [sys.executable, "-c", "raise SystemExit(1)"]
                return [sys.executable, "-c", "from pathlib import Path; Path(__import__('sys').argv[1]).write_text('{}')", str(output_path)]

            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "admitted-work-item-v1", "scope_hash": "0" * 64}
            budget = DispatchBudget(60, 3)
            records = dispatch_native_lane(
                [item], "run-1", "signals", output_dir,
                NativeExecutorConfig(sys.executable, "default", max_retries=1, max_workers=1),
                command_builder=command_builder,
                budget=budget,
                lifecycle_root=root,
                manifest_path=manifest_path,
            )
            replay = replay_lifecycle(root, "run-1")
            self.assertEqual(records[0]["status"], "succeeded")
            self.assertEqual(attempts["count"], 2)
            self.assertEqual(replay["action_count"], 2)
            self.assertEqual(replay["budget_reserved"], 2)
            self.assertEqual(replay["budget_settled"], 2)
            self.assertTrue(all(action["settled"] for action in replay["actions"]))
            self.assertEqual(records[0]["capacity"]["attempted"], 2)
            self.assertEqual(records[0]["capacity"]["retried"], 1)
            self.assertEqual(records[0]["capacity"]["remaining"], 1)

    def test_shared_budget_reserves_verifier_capacity_until_released(self):
        budget = DispatchBudget(60, 120, reserved_attempts=30)
        self.assertTrue(all(budget.reserve_attempt() for _ in range(90)))
        self.assertFalse(budget.reserve_attempt())
        budget.release_reserved_attempts()
        self.assertTrue(all(budget.reserve_attempt() for _ in range(30)))
        self.assertFalse(budget.reserve_attempt())
        reconciliation = budget.reconciliation()
        self.assertEqual(reconciliation["verifier_reserved"], 0)
        self.assertEqual(reconciliation["reserve_backfill"], 30)
        self.assertEqual(reconciliation["remaining"], 0)

    def test_material_gap_queue_omits_only_valid_terminal_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "candidate"
            output_dir.mkdir(parents=True)
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            output = output_dir / "signals-C1.json"
            output.write_text(json.dumps(self.valid_research_payload(item)), encoding="utf-8")
            self.write_cache_evidence(output, item)
            config = NativeExecutorConfig(sys.executable, "default")
            pending, reused = split_material_gap_queue(
                [item, {**item, "company_id": "C2", "scope": "signals:C2"}],
                "run-1",
                "signals",
                output_dir,
                config=config,
            )
            self.assertEqual([row["company_id"] for row in pending], ["C2"])
            self.assertEqual([row["company_id"] for row in reused], ["C1"])
            self.assertTrue(reused[0]["reused_terminal"])

    def test_mutated_terminal_output_requires_reexecution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "candidate"
            output_dir.mkdir(parents=True)
            item = {"campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            output = output_dir / "signals-C1.json"
            output.write_text(json.dumps(self.valid_research_payload(item)), encoding="utf-8")
            self.write_cache_evidence(output, item)
            output.write_text(json.dumps({**self.valid_research_payload(item), "claims": [{"tampered": True}]}), encoding="utf-8")
            pending, reused = split_material_gap_queue([item], "run-1", "signals", output_dir)
            self.assertEqual([row["company_id"] for row in pending], ["C1"])
            self.assertEqual(reused, [])

    def test_mutated_execution_fingerprint_requires_reexecution(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "candidate"
            output_dir.mkdir(parents=True)
            item = {"campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64, "worker_profile": "default", "provider": "configured"}
            output = output_dir / "signals-C1.json"
            output.write_text(json.dumps(self.valid_research_payload(item)), encoding="utf-8")
            self.write_cache_evidence(output, item)
            mutated = {**item, "worker_profile": "changed-profile"}
            pending, reused = split_material_gap_queue([mutated], "run-1", "signals", output_dir)
            self.assertEqual([row["company_id"] for row in pending], ["C1"])
            self.assertEqual(reused, [])

    def test_stale_verifier_claims_input_requires_reexecution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "verifier"
            output_dir.mkdir(parents=True)
            claims = root / "claims.jsonl"
            claims.write_text("{\"candidate_claim_id\": \"claim-1\", \"candidate_sha256\": \"a\"}\n", encoding="utf-8")
            item = {"campaign_id": "campaign-1", "company_id": "C1", "lane": "verifier", "scope": "verifier:C1", "scope_version": "v1", "scope_hash": "0" * 64, "claims_path": claims}
            output = output_dir / "verifier-C1.json"
            output.write_text(json.dumps({"run_id": "run-1", "lane": "verifier", "campaign_id": "campaign-1", "company_id": "C1", "scope": "verifier:C1", "scope_version": "v1", "scope_hash": "0" * 64, "claims_input_sha256": hashlib.sha256(claims.read_bytes()).hexdigest(), "decisions": []}), encoding="utf-8")
            self.write_cache_evidence(output, item, lane="verifier", claims_input=claims)
            claims.write_text("{\"candidate_claim_id\": \"claim-2\", \"candidate_sha256\": \"b\"}\n", encoding="utf-8")
            pending, reused = split_material_gap_queue([item], "run-1", "verifier", output_dir)
            self.assertEqual([row["company_id"] for row in pending], ["C1"])
            self.assertEqual(reused, [])

    def test_deterministic_failure_is_attempted_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"
            calls = []

            def command_builder(item, output_path, config):
                calls.append(item["company_id"])
                return [sys.executable, "-c", "raise SystemExit(1)"]

            records = dispatch_native_lane(
                [{"company_id": "C1", "failure_class": "deterministic"}],
                "run-1",
                "signals",
                output_dir,
                NativeExecutorConfig(sys.executable, "default", max_retries=3),
                command_builder=command_builder,
            )
            self.assertEqual(calls, ["C1"])
            self.assertEqual(records[0]["attempts"], 1)
            self.assertEqual(records[0]["failure_class"], "deterministic")

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
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "company_name": "Company", "trusted_domain": "example.de", "location": "Berlin", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            code = "from pathlib import Path; import json, sys; Path(sys.argv[1]).write_text(json.dumps({'research_run': {'record_type': 'ResearchRun', 'run_id': 'run-1:signals:C1', 'campaign_id': 'campaign-1', 'company_id': 'C1', 'research_type': 'signals', 'source': 'fixture', 'scope': 'signals:C1', 'status': 'Completed', 'started_at': '2026-11-08T00:00:00+00:00', 'completed_at': '2026-11-08T00:00:01+00:00', 'result_count': 0, 'truncated': False, 'provider_status': 'Available', 'adapter_capability': 'replay', 'assurance_level': 'replay', 'scope_version': 'v1', 'scope_hash': '0000000000000000000000000000000000000000000000000000000000000000', 'attempts': [{'attempt_id': 'a1', 'query_or_source': 'fixture', 'status': 'Completed', 'truncated': False}]}, 'claims': [1]}))"

            def command_builder(queue_item, output_path, config):
                return [sys.executable, "-c", code, str(output_path)]

            records = dispatch_native_lane([item], "run-1", "signals", output_dir, NativeExecutorConfig(sys.executable, "default"), command_builder=command_builder)
            with self.assertRaisesRegex(ValueError, "claims are not objects"):
                reconcile_lane_outputs(records, [item], "run-1", "signals")
            (output_dir / "signals-C1.json").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                reconcile_lane_outputs(records, [item], "run-1", "signals")

    def test_native_verifier_nonempty_decision_promotes(self):
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims_path = root / "claims.jsonl"
            decisions_path = root / "decisions.jsonl"
            verifier_output = root / "verifier.json"
            verified_path = root / "verified.jsonl"
            claim = {
                "record_type": "EvidenceClaim",
                "company_id": "C1",
                "claim_type": "service_fit",
                "claim_value": "Confirmed",
                "source_url": "https://example.de/services",
                "source_domain": "example.de",
                "source_kind": "official",
                "evidence_excerpt": "Residential property management services.",
                "retrieved_at": "2026-11-08T00:00:00+00:00",
                "published_at": None,
                "as_of_date": None,
                "account_relationship": "direct",
                "confidence": "high",
                "research_run_id": "run-1:signals:C1",
                "candidate_status": "Candidate",
            }
            claim["candidate_claim_id"] = candidate_claim_id(claim)
            claim["candidate_sha256"] = candidate_sha256(claim)
            claims_path.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            result = subprocess.run([
                sys.executable,
                str(repository_root / "scripts" / "native_verifier.py"),
                "--repo-root", str(root),
                "--profile", "evidence-verifier",
                "--run-id", "run-1",
                "--lane", "verifier",
                "--company-id", "C1",
                "--scope-version", "v1",
                "--scope-hash", "0" * 64,
                "--claims", str(claims_path),
                "--output", str(verifier_output),
            ], check=False, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            decisions = json.loads(verifier_output.read_text(encoding="utf-8"))["decisions"]
            decisions_path.write_text("\n".join(json.dumps(decision) for decision in decisions) + "\n", encoding="utf-8")
            promoted = promote_verified_claims(claims_path, decisions_path, verified_path)
            self.assertEqual(len(promoted), 1)
            self.assertEqual(promoted[0]["candidate_claim_id"], claim["candidate_claim_id"])

    def test_personal_reconciliation_keeps_successful_outputs_when_one_worker_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "evidence" / "candidate" / "run-1" / "signals"

            def command_builder(item, output_path, config):
                if item["company_id"] == "C2":
                    return [sys.executable, "-c", "raise SystemExit(1)"]
                return [sys.executable, "-c", "from pathlib import Path; import json,sys; Path(sys.argv[1]).write_text(json.dumps({'research_run': {'record_type': 'ResearchRun', 'run_id': 'run-1:signals:C1', 'campaign_id': 'campaign-1', 'company_id': 'C1', 'research_type': 'signals', 'source': 'fixture', 'scope': 'signals:C1', 'status': 'Completed', 'started_at': '2026-11-08T00:00:00+00:00', 'completed_at': '2026-11-08T00:00:01+00:00', 'result_count': 0, 'truncated': False, 'provider_status': 'Available', 'adapter_capability': 'replay', 'assurance_level': 'replay', 'scope_version': 'v1', 'scope_hash': '0000000000000000000000000000000000000000000000000000000000000000', 'attempts': [{'attempt_id': 'a1', 'query_or_source': 'fixture', 'status': 'Completed', 'truncated': False}]}, 'claims': []}))", str(output_path)]

            queue = [
                {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "lane": "signals", "scope": "signals:C1", "scope_version": "v1", "scope_hash": "0" * 64},
                {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C2", "lane": "signals", "scope": "signals:C2", "scope_version": "v1", "scope_hash": "0" * 64},
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
            output_path.write_text(json.dumps({"run_id": "run-1", "lane": "verifier", "campaign_id": "legacy", "company_id": "C1", "scope": "verifier:C1", "scope_version": "v1", "scope_hash": "hash", "claims_input_sha256": __import__("hashlib").sha256(claims_path.read_bytes()).hexdigest(), "decisions": [{"candidate_claim_id": "foreign", "candidate_sha256": "b" * 64}]}), encoding="utf-8")
            item = {"run_id": "run-1", "lane": "verifier", "campaign_id": "legacy", "company_id": "C1", "scope": "verifier:C1", "scope_version": "v1", "scope_hash": "hash", "claims_path": claims_path}
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
            self.assertEqual(payload["research_run"]["assurance_level"], "replay")
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

    def test_native_verifier_reconciles_generated_verifier_scope(self):
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            verifier_input = root / "inputs"
            output_dir = root / "outputs"
            item = {"run_id": "run-1", "campaign_id": "campaign-1", "company_id": "C1", "company_name": "Company", "trusted_domain": "example.de", "location": "Berlin", "lane": "contacts", "scope": "contacts:C1", "scope_version": "v1", "scope_hash": "0" * 64}
            queue, _ = build_verifier_queue(accepted_ids={"C1"}, admitted_items=[item], claims_by_company={"C1": []}, claims_dir=verifier_input, run_id="run-1", delivery_policy="personal")
            verifier_item = queue[0]
            config = NativeExecutorConfig(sys.executable, "evidence-verifier", adapter_args=(str(repository_root / "scripts" / "native_verifier.py"), "--repo-root", str(root)))

            def command_builder(current_item, output_path, current_config):
                return _native_command_builder(current_item, output_path, current_config) + ["--claims", str(current_item["claims_path"])]

            records = dispatch_native_lane([verifier_item], "run-1", "verifier", output_dir, config, command_builder=command_builder)
            reconcile_lane_outputs(records, queue, "run-1", "verifier")


if __name__ == "__main__":
    unittest.main()
