from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import action_lifecycle
from action_lifecycle import admit_action, canonical_request_hash, lifecycle_snapshot_path, reject_result, replay_lifecycle, settle_action, validate_result
from action_receipts import canonical_json
from run_manifest import atomic_write


def action(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "run_id": "run-1",
        "action_id": "action-1",
        "attempt_id": "attempt-1",
        "company_id": "C1",
        "action_type": "signals",
        "scope": "signals:C1",
        "contract_version": "1",
        "strategy_version": "1",
        "profile_version": "signal-v1",
        "idempotency_key": "run-1/action-1/attempt-1",
        "request_hash": "a" * 64,
        "budget_units": 1,
        "provenance": {"source": "test"},
    }
    value.update(overrides)
    if "request_hash" not in overrides:
        value["request_hash"] = canonical_request_hash(value)
    return value


def result_for(request: dict[str, object], **overrides: object) -> dict[str, object]:
    result = {"claims": 1}
    value: dict[str, object] = {
        "run_id": request["run_id"],
        "action_id": request["action_id"],
        "attempt_id": request["attempt_id"],
        "company_id": request["company_id"],
        "status": "Completed",
        "result": result,
        "result_hash": hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest(),
    }
    value.update(overrides)
    return value


class ActionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.manifest = self.root / "manifest.json"
        atomic_write(self.manifest, {"run_id": "run-1", "budget_limit": 1})

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_admission_result_and_settlement_replay_durable_lifecycle(self):
        request = action()
        admitted = admit_action(self.root, request, self.manifest)
        validated = validate_result(self.root, result_for(request))
        receipt = {
            **request,
            "result_hash": validated.result_hash,
            "terminal_status": "Completed",
            "budget_requested": 1,
            "budget_settled": 1,
            "coverage_delta": {"signals": 1},
            "created_at": datetime.now(timezone.utc),
        }
        settle_action(self.root, receipt)
        replay = replay_lifecycle(self.root, "run-1")
        self.assertEqual(replay["budget_reserved"], 1)
        self.assertEqual(replay["budget_settled"], 1)
        self.assertEqual(replay["coverage"], {"signals": 1})
        self.assertEqual(replay["actions"][0]["status"], "Completed")

    def test_result_requires_admission_and_canonical_hash(self):
        request = action()
        with self.assertRaisesRegex(ValueError, "not admitted"):
            validate_result(self.root, result_for(request))
        admit_action(self.root, request, self.manifest)
        with self.assertRaisesRegex(ValueError, "result hash mismatch"):
            validate_result(self.root, result_for(request, result_hash="b" * 64))

    def test_concurrent_admission_cannot_overreserve_budget(self):
        requests = [action(action_id=f"action-{index}", attempt_id=f"attempt-{index}", idempotency_key=f"key-{index}") for index in range(2)]

        def attempt(request: dict[str, object]) -> bool:
            try:
                admit_action(self.root, request, self.manifest)
                return True
            except ValueError:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, requests))
        self.assertEqual(sum(outcomes), 1)

    def test_exact_duplicate_admission_is_idempotent(self):
        request = action()
        first = admit_action(self.root, request, self.manifest)
        second = admit_action(self.root, request, self.manifest)
        self.assertEqual(first.action_id, second.action_id)
        self.assertEqual(replay_lifecycle(self.root, "run-1")["action_count"], 1)

    def test_conflicting_duplicate_admission_cannot_change_contract_or_budget(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        with self.assertRaisesRegex(ValueError, "conflicting duplicate action admission"):
            admit_action(self.root, action(company_id="FOREIGN", budget_units=999), self.manifest)

    def test_admission_rejects_company_outside_manifest_scope(self):
        atomic_write(self.manifest, {
            "run_id": "run-1",
            "budget_limit": 1,
            "authorization": {
                "accepted_company_ids": ["C1"],
                "campaign_id": "campaign-1",
                "campaign_version": "v1",
                "scope_version": "admitted-work-item-v1",
            },
        })
        with self.assertRaisesRegex(ValueError, "accepted company scope"):
            admit_action(self.root, action(company_id="C2", provenance={"campaign_id": "campaign-1", "campaign_version": "v1", "scope_version": "admitted-work-item-v1"}), self.manifest)

    def test_admission_rejects_scope_and_version_outside_manifest_scope(self):
        atomic_write(self.manifest, {
            "run_id": "run-1",
            "budget_limit": 1,
            "authorization": {
                "accepted_company_ids": ["C1"],
                "allowed_action_types": ["signals"],
                "scope_prefixes": {"signals": "signals:"},
                "contract_version": "1",
                "strategy_version": "1",
                "profile_versions": {"signals": "signals-v1"},
            },
        })
        with self.assertRaisesRegex(ValueError, "request scope"):
            admit_action(self.root, action(scope="portfolio:C1", profile_version="signals-v1"), self.manifest)
        with self.assertRaisesRegex(ValueError, "request scope"):
            admit_action(self.root, action(scope="signals:C2"), self.manifest)
        with self.assertRaisesRegex(ValueError, "contract_version"):
            admit_action(self.root, action(contract_version="2"), self.manifest)
        with self.assertRaisesRegex(ValueError, "profile_version"):
            admit_action(self.root, action(profile_version="signals-v2"), self.manifest)

    def test_admission_rejects_forged_request_hash(self):
        request = action()
        request["request_hash"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "request hash mismatch"):
            admit_action(self.root, request, self.manifest)

    def test_rejected_result_is_durable_terminal_and_replayable(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        rejected = reject_result(self.root, request, ["malformed worker payload"], raw_result={"status": "invalid"})
        rejected_again = reject_result(self.root, request, ["malformed worker payload"], raw_result={"status": "invalid"})
        receipt = {
            **request,
            "result_hash": rejected.result_hash,
            "terminal_status": "Rejected",
            "validation_errors": ["malformed worker payload"],
            "budget_requested": 1,
            "budget_settled": 1,
            "coverage_delta": {},
            "created_at": datetime.now(timezone.utc),
        }
        settle_action(self.root, receipt)
        settle_action(self.root, receipt)
        replay = replay_lifecycle(self.root, "run-1")
        self.assertEqual(rejected.result_hash, rejected_again.result_hash)
        self.assertEqual(replay["actions"][0]["status"], "Rejected")
        self.assertEqual(replay["coverage"], {})
        self.assertEqual(len([event for event in replay_lifecycle(self.root, "run-1")["actions"] if event["status"] == "Rejected"]), 1)

    def test_coverage_is_bound_to_successful_action_type(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        validated = validate_result(self.root, result_for(request))
        receipt = {
            **request,
            "result_hash": validated.result_hash,
            "terminal_status": "Completed",
            "budget_requested": 1,
            "budget_settled": 1,
            "coverage_delta": {"foreign": 1},
            "created_at": datetime.now(timezone.utc),
        }
        with self.assertRaisesRegex(ValueError, "coverage key"):
            settle_action(self.root, receipt)

    def test_failed_action_cannot_report_coverage(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        failed = result_for(request, status="Failed")
        validated = validate_result(self.root, failed)
        with self.assertRaisesRegex(ValueError, "non-successful"):
            settle_action(self.root, {
                **request,
                "result_hash": validated.result_hash,
                "terminal_status": "Failed",
                "budget_requested": 1,
                "budget_settled": 1,
                "coverage_delta": {"signals": 1},
                "created_at": datetime.now(timezone.utc),
            })

    def test_exact_duplicate_result_validation_is_idempotent(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        result = result_for(request)
        first = validate_result(self.root, result)
        second = validate_result(self.root, result)
        self.assertEqual(first.result_hash, second.result_hash)
        self.assertFalse(replay_lifecycle(self.root, "run-1")["actions"][0]["settled"])

    def test_settlement_must_match_admitted_identity_and_validated_status(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        validated = validate_result(self.root, result_for(request))
        receipt = {
            **request,
            "company_id": "C2",
            "result_hash": validated.result_hash,
            "terminal_status": "Failed",
            "budget_requested": 1,
            "budget_settled": 1,
            "created_at": datetime.now(timezone.utc),
        }
        with self.assertRaisesRegex(ValueError, "company_id"):
            settle_action(self.root, receipt)

    def test_rejected_result_cannot_become_validated_or_settled(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        with self.assertRaisesRegex(ValueError, "validation failed"):
            validate_result(self.root, result_for(request, validation_errors=["invalid evidence"]))
        self.assertEqual(replay_lifecycle(self.root, "run-1")["actions"][0]["status"], "Admitted")

    def test_worker_artifact_is_verified_and_bound_to_result_event(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        artifact = self.root / "worker.json"
        artifact.write_text('{"ok": true}\n', encoding="utf-8")
        artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
        validated = validate_result(self.root, result_for(request, artifact={"path": "worker.json", "sha256": artifact_hash, "kind": "worker"}))
        receipt = {
            **request,
            "result_hash": validated.result_hash,
            "artifact_hash": artifact_hash,
            "terminal_status": "Completed",
            "budget_requested": 1,
            "budget_settled": 1,
            "created_at": datetime.now(timezone.utc),
        }
        settle_action(self.root, receipt)
        self.assertEqual(replay_lifecycle(self.root, "run-1")["budget_settled"], 1)
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            settle_action(self.root, {**receipt, "artifact_hash": "c" * 64})

    def test_replay_marks_validated_only_action_unsettled(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        validate_result(self.root, result_for(request))
        replay = replay_lifecycle(self.root, "run-1")
        self.assertFalse(replay["actions"][0]["settled"])

    def test_snapshot_replay_matches_journal_and_falls_back_when_corrupt(self):
        request = action()
        admit_action(self.root, request, self.manifest)
        validated = validate_result(self.root, result_for(request))
        settle_action(self.root, {
            **request,
            "result_hash": validated.result_hash,
            "terminal_status": "Completed",
            "budget_requested": 1,
            "budget_settled": 1,
            "coverage_delta": {"signals": 1},
            "created_at": datetime.now(timezone.utc),
        })
        journal = replay_lifecycle(self.root, "run-1")
        self.assertEqual(replay_lifecycle(self.root, "run-1", prefer_snapshot=True), journal)
        lifecycle_snapshot_path(self.root, "run-1").write_text("not-json\n", encoding="utf-8")
        self.assertEqual(replay_lifecycle(self.root, "run-1", prefer_snapshot=True), journal)

    def test_snapshot_backed_transition_does_not_read_full_journal(self):
        first = action()
        admit_action(self.root, first, self.manifest)
        atomic_write(self.manifest, {"run_id": "run-1", "budget_limit": 2})
        with patch.object(action_lifecycle, "_read", side_effect=AssertionError("full journal replay was used")):
            second = action(action_id="action-2", attempt_id="attempt-2", idempotency_key="run-1/action-2/attempt-2")
            admit_action(self.root, second, self.manifest)

    def test_one_thousand_admissions_have_equivalent_snapshot_and_journal_state(self):
        atomic_write(self.manifest, {"run_id": "run-1", "budget_limit": 1000})
        for index in range(1000):
            admit_action(self.root, action(action_id=f"action-{index}", attempt_id=f"attempt-{index}", idempotency_key=f"run-1/action-{index}/attempt-{index}"), self.manifest)
        journal = replay_lifecycle(self.root, "run-1")
        snapshot = replay_lifecycle(self.root, "run-1", prefer_snapshot=True)
        self.assertEqual(snapshot, journal)
        self.assertEqual(snapshot["action_count"], 1000)


if __name__ == "__main__":
    unittest.main()

