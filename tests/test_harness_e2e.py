from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from account_intelligence import project_account_intelligence
from action_receipts import replay_run
from harness_tools import invoke
from run_manifest import atomic_write, load


def _claim(claim_id: str, company_id: str, claim_type: str, value: object) -> dict[str, object]:
    return {
        "claim_id": claim_id, "company_id": company_id, "claim_type": claim_type, "value": value,
        "source_url": "https://example.com/account", "evidence_excerpt": "Page-local evidence",
        "source_kind": "official_site", "confidence": "high", "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "assurance_level": "source",
    }


class HarnessE2ETests(unittest.TestCase):
    def _trace(self, root: Path, run_id: str, *, strict: bool, stop_early: bool = False) -> dict[str, object]:
        manifest_path = root / "evidence" / "manifests" / f"native_handoff_{run_id}.json"
        manifest = {
            "record_type": "RunManifest", "run_id": run_id, "head_sha": "0" * 40, "git_revision": "0" * 40,
            "barriers": {"research": not stop_early, "verifier": not stop_early, "verified_evidence": not stop_early, "projection": not stop_early, "ranking": not stop_early, "readiness": not stop_early},
            "coverage": {"status": "complete" if strict and not stop_early else "partial"},
            "delivery": {"status": "complete" if strict and not stop_early else "partial"},
            "outputs": {},
        }
        atomic_write(manifest_path, manifest)
        goal = {"goal_id": run_id, "objective": "find Berlin property-management leads", "delivery_policy": "strict" if strict else "personal"}
        invoke({"action": "validate_goal", "payload": goal}, root)
        request_hash = "a" * 64
        result_hash = "b" * 64
        action = {
            "run_id": run_id, "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1", "action_type": "signals",
            "scope": "signals:C1", "contract_version": "1", "strategy_version": "1", "profile_version": "signal-v1",
            "idempotency_key": f"{run_id}/action-1/attempt-1", "request_hash": request_hash, "budget_units": 1,
        }
        invoke({"action": "admit_action", "payload": action}, root)
        invoke({"action": "validate_result", "payload": {"run_id": run_id, "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1", "status": "Partial" if stop_early else "Completed", "result_hash": result_hash, "result": {"claims": 1}}}, root)
        invoke({"action": "record_receipt", "payload": {key: value for key, value in {**action, "result_hash": result_hash, "terminal_status": "Unavailable" if stop_early else "Completed", "budget_requested": 1, "budget_settled": 1, "created_at": datetime.now(timezone.utc).isoformat(), "coverage_delta": {"signals": 0 if stop_early else 1}}.items() if key != "budget_units"}}, root)
        if not stop_early:
            claims = [_claim("c1", "C1", "service_fit", "Confirmed"), _claim("c2", "C1", "event", {"event_id": "E1", "event_type": "tender", "event_date": "2026-11-01"})]
            thesis = {"company_id": "C1", "structural_fit": 80, "confidence": "high", "recommended_action": "research contacts", "hypotheses": [{"company_id": "C1", "hypothesis_type": "opportunity", "statement": "Observed procurement activity may create a near-term opening", "supporting_claim_ids": ["c2"], "confidence": "medium"}]}
            projection = project_account_intelligence(claims, thesis)
            self.assertEqual(projection["timeline"][0]["event_identity"], "C1:E1")
            staged = root / "output" / f"{run_id}.staging.xlsx"
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(b"native-handoff-workbook")
            manifest["barriers"] = {key: True for key in manifest["barriers"]}
            manifest["outputs"] = {"workbook": {"path": staged.relative_to(root).as_posix(), "sha256": ""}}
            atomic_write(manifest_path, manifest)
            checked = invoke({"action": "check_finalization", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "delivery_policy": "strict" if strict else "personal"}}, root)
            self.assertTrue(checked["eligible"])
            invoke({"action": "publish_staged_output", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "staging_path": staged.relative_to(root).as_posix(), "final_path": f"output/{run_id}.xlsx", "status": "complete"}}, root)
        else:
            checked = invoke({"action": "check_finalization", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "delivery_policy": "personal"}}, root)
            self.assertFalse(checked["eligible"])
        return {"manifest": manifest_path, "replay": replay_run(root, run_id)}

    def test_two_valid_traces_and_early_stop_are_replayable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._trace(root, "run-1", strict=True)
            second = self._trace(root, "run-2", strict=False)
            stopped = self._trace(root, "run-3", strict=False, stop_early=True)
            self.assertTrue((root / "output" / "run-1.xlsx").exists())
            self.assertTrue((root / "output" / "run-2.xlsx").exists())
            self.assertFalse((root / "output" / "run-3.xlsx").exists())
            self.assertEqual(first["replay"]["budget_settled"], 1)
            self.assertEqual(second["replay"]["coverage"], {"signals": 1})
            self.assertEqual(stopped["replay"]["coverage"], {"signals": 0})
            self.assertTrue(load(first["manifest"])["barriers"]["published"])


if __name__ == "__main__":
    unittest.main()

