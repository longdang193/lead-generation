from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from action_receipts import append_receipt, read_receipts, replay_run


def receipt(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "run_id": "run-1", "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1",
        "action_type": "signals", "scope": "signals:C1", "contract_version": "1", "strategy_version": "1",
        "profile_version": "signal-v1", "idempotency_key": "run-1/action-1/attempt-1", "request_hash": "a" * 64,
        "result_hash": "b" * 64, "terminal_status": "Completed", "budget_requested": 2, "budget_settled": 1,
        "coverage_delta": {"signals": 1}, "created_at": datetime.now(timezone.utc),
    }
    value.update(overrides)
    return value


class ActionReceiptTests(unittest.TestCase):
    def test_duplicate_is_idempotent_and_replay_is_durable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = append_receipt(root, receipt())
            append_receipt(root, first)
            self.assertEqual(len(read_receipts(root, "run-1")), 1)
            self.assertEqual(replay_run(root, "run-1")["budget_settled"], 1)
            self.assertEqual(replay_run(root, "run-1")["coverage"], {"signals": 1})

    def test_conflicting_duplicate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            append_receipt(root, receipt())
            with self.assertRaises(ValueError):
                append_receipt(root, receipt(result_hash="c" * 64))


if __name__ == "__main__":
    unittest.main()

