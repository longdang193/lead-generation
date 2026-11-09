from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from typed_contracts import (
    ActionReceipt,
    EvidenceClaim,
    Goal,
    NativeActionRequest,
    WorkerResult,
    normalize_native_claim,
    normalize_native_research_run,
    normalize_native_verifier_decision,
)


class TypedContractTests(unittest.TestCase):
    def test_goal_rejects_unknown_fields(self):
        with self.assertRaises(ValidationError):
            Goal(goal_id="g1", objective="find leads", unexpected=True)

    def test_evidence_claim_requires_http_source_and_excerpt(self):
        with self.assertRaises(ValidationError):
            EvidenceClaim(
                claim_id="c1",
                company_id="C1",
                claim_type="event",
                value={"event_id": "E1"},
                source_url="not-a-url",
                evidence_excerpt="event",
                source_kind="official_site",
                confidence="high",
                retrieved_at=datetime.now(timezone.utc),
            )

    def test_action_and_result_hashes_are_boundaries(self):
        with self.assertRaises(ValidationError):
            NativeActionRequest(
                run_id="r1", action_id="a1", attempt_id="t1", company_id="C1", action_type="signals", scope="C1",
                contract_version="1", strategy_version="1", profile_version="1", idempotency_key="k", request_hash="bad",
            )
        with self.assertRaises(ValidationError):
            WorkerResult(run_id="r1", action_id="a1", attempt_id="t1", company_id="C1", status="Completed", result_hash="bad")

    def test_receipt_cannot_settle_more_than_requested(self):
        with self.assertRaises(ValidationError):
            ActionReceipt(
                run_id="r1", action_id="a1", attempt_id="t1", company_id="C1", action_type="signals", scope="C1",
                contract_version="1", strategy_version="1", profile_version="1", idempotency_key="k",
                request_hash="a" * 64, result_hash="b" * 64, terminal_status="Completed",
                budget_requested=1, budget_settled=2, created_at=datetime.now(timezone.utc),
            )

    def test_receipt_json_round_trip_allows_missing_artifact_hash(self):
        receipt = ActionReceipt(
            run_id="r1", action_id="a1", attempt_id="t1", company_id="C1", action_type="signals", scope="C1",
            contract_version="1", strategy_version="1", profile_version="1", idempotency_key="k",
            request_hash="a" * 64, result_hash="b" * 64, terminal_status="Completed",
            budget_requested=1, budget_settled=1, created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(ActionReceipt.model_validate(receipt.model_dump(mode="json")).artifact_hash, None)

    def test_native_worker_and_verifier_round_trip_through_typed_boundary(self):
        repository_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            companies.write_text("company_id,company_name,domain,source_url\nC1,Example,example.de,https://example.de/\n", encoding="utf-8")
            website = root / "website.jsonl"
            website.write_text(json.dumps({
                "company_id": "C1",
                "retrieved_at": "2026-11-09T00:00:00+00:00",
                "claims": [{"field": "service_fit", "value": "Confirmed", "evidence_url": "https://example.de/services", "evidence_excerpt": "Example serves residential owners."}],
            }) + "\n", encoding="utf-8")
            worker_output = root / "worker.json"
            worker = subprocess.run([
                sys.executable, str(repository_root / "scripts" / "native_worker.py"),
                "--repo-root", str(root), "--profile", "signal-researcher", "--run-id", "run-1",
                "--lane", "portfolio", "--company-id", "C1", "--companies-input", str(companies),
                "--website-evidence", str(website), "--output", str(worker_output),
            ], check=False, capture_output=True, text=True)
            self.assertEqual(worker.returncode, 0, worker.stderr)
            payload = json.loads(worker_output.read_text(encoding="utf-8"))
            typed_run = normalize_native_research_run(payload["research_run"])
            self.assertEqual(typed_run.status.value, "Not searched")
            self.assertEqual(typed_run.attempts[0].status, "Unavailable")
            typed_claim = normalize_native_claim(payload["claims"][0])
            self.assertEqual(typed_claim.claim_id, payload["claims"][0]["candidate_claim_id"])
            self.assertEqual(typed_claim.value, "Confirmed")
            self.assertEqual(typed_claim.source_kind.value, "official_site")

            claims = root / "claims.jsonl"
            claims.write_text(json.dumps(payload["claims"][0]) + "\n", encoding="utf-8")
            verifier_output = root / "verifier.json"
            verifier = subprocess.run([
                sys.executable, str(repository_root / "scripts" / "native_verifier.py"),
                "--repo-root", str(root), "--profile", "evidence-verifier", "--run-id", "run-1",
                "--lane", "portfolio", "--company-id", "C1", "--claims", str(claims),
                "--output", str(verifier_output),
            ], check=False, capture_output=True, text=True)
            self.assertEqual(verifier.returncode, 0, verifier.stderr)
            decision = json.loads(verifier_output.read_text(encoding="utf-8"))["decisions"][0]
            typed_decision = normalize_native_verifier_decision(decision)
            self.assertEqual(typed_decision.claim_id, typed_claim.claim_id)
            self.assertEqual(typed_decision.candidate_sha256, typed_claim.candidate_sha256)
            self.assertEqual(typed_decision.decision, "Verified")
            self.assertEqual(typed_decision.assurance_level.value, "structural")
            self.assertEqual(typed_decision.verifier_run_id, "run-1:verifier")


if __name__ == "__main__":
    unittest.main()
