from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lead_contract import candidate_sha256, claim_requirements_met, none_found_allowed
from qa_leads import append_schema_errors


SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))


def validate(record: dict[str, object]) -> None:
    jsonschema.Draft202012Validator(SCHEMA).validate(record)


class ResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claim = {
            "record_type": "EvidenceClaim",
            "candidate_claim_id": "claim-1",
            "company_id": "company-1",
            "claim_type": "service_fit",
            "claim_value": "Confirmed",
            "source_url": "https://example.de/services",
            "source_kind": "official_site",
            "evidence_excerpt": "Hausverwaltung in Berlin",
            "retrieved_at": "2026-11-08T10:00:00+00:00",
            "account_relationship": "direct",
            "confidence": "high",
            "research_run_id": "run-1",
            "candidate_status": "Candidate",
        }
        self.claim["candidate_sha256"] = candidate_sha256(self.claim)

    def test_each_record_type_has_its_own_required_fields(self):
        validate(self.claim)
        decision = {
            "record_type": "VerifierDecision",
            "candidate_claim_id": "claim-1",
            "candidate_sha256": self.claim["candidate_sha256"],
            "decision": "Verified",
            "reason_codes": ["page_local"],
            "verifier_id": "evidence-verifier",
            "verifier_run_id": "run-1",
            "verified_at": "2026-11-08T10:01:00+00:00",
        }
        validate(decision)
        research_run = {
            "record_type": "ResearchRun",
            "run_id": "run-1",
            "company_id": "company-1",
            "research_type": "signals",
            "source": "official_site",
            "scope": "company-1",
            "status": "Completed",
            "started_at": "2026-11-08T10:00:00+00:00",
            "completed_at": "2026-11-08T10:01:00+00:00",
            "result_count": 0,
            "truncated": False,
            "provider_status": "Available",
            "scope_version": "signals-v1",
            "scope_hash": "0" * 64,
            "attempts": [{"attempt_id": "a1", "query_or_source": "official_site", "status": "Completed", "truncated": False}],
        }
        validate(research_run)

    def test_verifier_decision_does_not_require_claim_fields(self):
        decision = {
            "record_type": "VerifierDecision",
            "candidate_claim_id": "claim-1",
            "candidate_sha256": "0" * 64,
            "decision": "Rejected",
            "reason_codes": ["not_page_local"],
            "verifier_id": "evidence-verifier",
            "verifier_run_id": "run-1",
            "verified_at": "2026-11-08T10:01:00+00:00",
        }
        validate(decision)

    def test_conditional_claim_requirements_are_enforced(self):
        buying_signal = copy.deepcopy(self.claim)
        buying_signal["claim_type"] = "buying_signal"
        self.assertFalse(claim_requirements_met(buying_signal)[0])
        portfolio = copy.deepcopy(self.claim)
        portfolio["claim_type"] = "portfolio_size"
        self.assertFalse(claim_requirements_met(portfolio)[0])
        contact = copy.deepcopy(self.claim)
        contact["claim_type"] = "contact"
        self.assertFalse(claim_requirements_met(contact)[0])

    def test_none_found_requires_complete_account_run(self):
        base = {
            "company_id": "C1",
            "scope": "signals:C1",
            "status": "Completed",
            "provider_status": "Available",
            "truncated": False,
            "attempts": [{"status": "Completed", "truncated": False}],
        }
        self.assertTrue(none_found_allowed(base, []))
        partial = dict(base, attempts=[{"status": "Partial", "truncated": False}])
        self.assertFalse(none_found_allowed(partial, []))
        unavailable = dict(base, provider_status="Unavailable")
        self.assertFalse(none_found_allowed(unavailable, []))
        self.assertFalse(none_found_allowed(dict(base, scope="signals:C2"), []))
        self.assertFalse(none_found_allowed(dict(base, scope="signals:C10"), []))

    def test_positive_const_condition_is_evaluated_as_json_schema_requires(self):
        errors: list[str] = []
        append_schema_errors(
            errors,
            {"record_type": "EvidenceClaim"},
            {"properties": {"record_type": {"type": "string"}}, "allOf": [{"if": {"properties": {"record_type": {"const": "EvidenceClaim"}}}, "then": {"required": ["company_id"]}}]},
            [],
            "evidence",
        )
        self.assertIn("evidence conditional required field company_id", errors[0])


if __name__ == "__main__":
    unittest.main()
