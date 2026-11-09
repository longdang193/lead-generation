from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from typed_contracts import ActionReceipt, EvidenceClaim, Goal, NativeActionRequest, WorkerResult


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


if __name__ == "__main__":
    unittest.main()

