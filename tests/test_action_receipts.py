from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from action_receipts import append_receipt, read_receipts, replay_run, settled_receipt_ids_for_checks


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

    def test_coverage_requires_one_completed_receipt_per_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            append_receipt(root, receipt(action_type="official_site", scope="official_site:C1", coverage_delta={"official_site": 1}))
            append_receipt(root, receipt(action_id="action-2", attempt_id="attempt-1", action_type="public_news", scope="public_news:C1", coverage_delta={"public_news": 1}))
            complete, receipt_ids = settled_receipt_ids_for_checks(root, "run-1", "C1", ["official_site", "public_news"])
            self.assertTrue(complete)
            self.assertEqual(len(receipt_ids), 2)

    def test_partial_or_scope_only_receipts_do_not_prove_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            append_receipt(root, receipt(terminal_status="Partial", coverage_delta={"official_site": 1}))
            append_receipt(root, receipt(action_id="action-2", attempt_id="attempt-1", action_type="public_news", scope="public_news:C1", coverage_delta={}))
            complete, receipt_ids = settled_receipt_ids_for_checks(root, "run-1", "C1", ["official_site", "public_news"])
            self.assertFalse(complete)
            self.assertEqual(receipt_ids, [])


if __name__ == "__main__":
    unittest.main()
