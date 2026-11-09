from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from account_intelligence import build_account_timeline, calculate_structural_fit, validate_account_thesis


def claim(claim_id: str, company_id: str = "C1", status: str = "Verified", claim_type: str = "event", value: object | None = None) -> dict[str, object]:
    return {
        "candidate_claim_id": claim_id, "company_id": company_id, "claim_type": claim_type,
        "claim_value": value if value is not None else {"event_id": "E1", "event_type": "tender", "event_date": "2026-11-01"},
        "source_url": "https://example.com/source", "source_kind": "other", "evidence_excerpt": "Observed on source",
        "confidence": "high", "retrieved_at": datetime.now(timezone.utc).isoformat(), "candidate_status": status,
        "assurance_level": "source",
    }


class AccountIntelligenceTests(unittest.TestCase):
    def test_timeline_uses_composite_identity_and_preserves_lineage(self):
        rows = build_account_timeline([claim("c1", "C1", "Candidate"), claim("c2", "C2", "Rejected")])
        self.assertEqual([row["event_identity"] for row in rows], ["C1:E1", "C2:E1"])
        self.assertEqual({row["status"] for row in rows}, {"Candidate", "Rejected"})

    def test_thesis_must_reference_same_company_claims(self):
        with self.assertRaises(ValueError):
            validate_account_thesis({
                "company_id": "C1", "structural_fit": 50, "confidence": "medium", "recommended_action": "research",
                "hypotheses": [{"company_id": "C1", "hypothesis_type": "need", "statement": "Likely need", "supporting_claim_ids": ["c2"], "confidence": "medium"}],
            }, [claim("c2", "C2")])

    def test_thesis_hypothesis_must_match_enclosing_company(self):
        with self.assertRaises(ValueError):
            validate_account_thesis({
                "company_id": "C1", "structural_fit": 50, "confidence": "medium", "recommended_action": "research",
                "hypotheses": [{"company_id": "C2", "hypothesis_type": "need", "statement": "Likely need", "confidence": "medium"}],
            }, [claim("c1", "C1")])

    def test_promoted_claim_envelope_preserves_provenance(self):
        rows = build_account_timeline([{
            **claim("c1", "C1"),
            "record_type": "EvidenceClaim",
            "research_run_id": "run-1:signals:C1",
            "candidate_sha256": "a" * 64,
            "verified_at": "2026-11-09T00:00:00Z",
            "verifier_run_id": "run-1:verifier",
        }])
        self.assertEqual(rows[0]["claim_id"], "c1")

    def test_promoted_portfolio_and_wrapped_fit_values_are_supported(self):
        promoted = {
            **claim("c1", "C1", claim_type="portfolio_size", value={"value": 600}),
            "record_type": "EvidenceClaim", "research_run_id": "run-1:portfolio:C1", "candidate_sha256": "a" * 64,
            "source_domain": "example.com", "unit": "units", "as_of_date": "2026-11-09",
            "verified_at": "2026-11-09T00:00:00Z", "verifier_run_id": "run-1:verifier",
        }
        self.assertGreater(calculate_structural_fit([promoted]), 0.0)
        wrapped = claim("c2", "C1", claim_type="service_fit", value={"value": "Confirmed"})
        self.assertEqual(calculate_structural_fit([wrapped]), 35.0)
        contact = {
            **claim("c3", "C1", claim_type="contact", value="Alice Smith"),
            "record_type": "EvidenceClaim", "research_run_id": "run-1:contacts:C1", "candidate_sha256": "b" * 64,
            "source_domain": "example.com", "person_name": "Alice Smith", "role": "Owner",
            "company_affiliation": "Example GmbH", "email": "alice@example.com",
            "verified_at": "2026-11-09T00:00:00Z", "verifier_run_id": "run-1:verifier",
        }
        validate_account_thesis({
            "company_id": "C1", "structural_fit": 50, "confidence": "medium", "recommended_action": "research",
            "hypotheses": [{"company_id": "C1", "hypothesis_type": "need", "statement": "Contact is attributable", "supporting_claim_ids": ["c3"], "confidence": "medium"}],
        }, [contact])

    def test_fact_fit_ignores_hypotheses(self):
        self.assertEqual(calculate_structural_fit([claim("c1", claim_type="service_fit", value="Confirmed")]), 35.0)
        self.assertEqual(calculate_structural_fit([claim("c1", claim_type="service_fit", value="Not evident")]), 0.0)
        self.assertEqual(calculate_structural_fit([claim("c1", status="Rejected", claim_type="service_fit", value="Confirmed")]), 0.0)


    def test_duplicate_event_claims_preserve_lineage_without_extra_corroboration(self):
        first = claim("c1", "C1")
        second = {**claim("c2", "C1"), "source_url": "https://syndicated.example/copy"}
        rows = build_account_timeline([first, second])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["claim_ids"], ["c1", "c2"])
        self.assertEqual(rows[0]["corroboration_count"], 1)
        self.assertEqual(rows[0]["status"], "Verified")

    def test_same_source_family_does_not_gain_weight_from_distinct_excerpts(self):
        first = claim("c1", "C1")
        second = {**claim("c2", "C1"), "evidence_excerpt": "A separate excerpt from the same source"}
        rows = build_account_timeline([first, second])
        self.assertEqual(rows[0]["corroboration_count"], 1)

    def test_unsupported_hypothesis_is_marked_speculative(self):
        thesis = validate_account_thesis({
            "company_id": "C1", "structural_fit": 0, "confidence": "medium", "recommended_action": "research",
            "hypotheses": [{"company_id": "C1", "hypothesis_type": "need", "statement": "Likely need", "confidence": "medium"}],
        }, [])
        self.assertTrue(thesis.hypotheses[0].speculative)

    def test_projection_rejects_agent_structural_fit_mismatch(self):
        from account_intelligence import project_account_intelligence
        with self.assertRaisesRegex(ValueError, "deterministic fact score"):
            project_account_intelligence([claim("c1", claim_type="service_fit", value="Confirmed")], {
                "company_id": "C1", "structural_fit": 99, "confidence": "medium", "recommended_action": "research",
            })

if __name__ == "__main__":
    unittest.main()
