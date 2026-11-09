from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from action_lifecycle import admit_action, replay_lifecycle, settle_action, validate_result
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


if __name__ == "__main__":
    unittest.main()

