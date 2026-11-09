from __future__ import annotations

import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from typed_contracts import (
    AccountIndicator,
    AccountThesis,
    CoverageManifest,
    OfferProfile,
    RankAudit,
    RankContribution,
    SemanticReview,
)


class AccountIntelligenceContractTests(unittest.TestCase):
    def test_offer_profile_exposes_immutable_identity(self):
        offer = OfferProfile(
            offer_id="offer-1",
            offer_version="2026-11-09",
            solution="Property operations platform",
            target_customer="Residential property managers",
            problems_solved=["Manual portfolio operations"],
            value_propositions=["Reduce administrative work"],
            economic_buyer_roles=["Managing director"],
            relevant_triggers=["Portfolio expansion"],
            disqualifiers=["No residential portfolio"],
            incumbent_or_competitor_signals=["Legacy property software"],
        )

        with self.assertRaises((ValidationError, TypeError)):
            offer.offer_id = "offer-2"
        with self.assertRaises((ValidationError, TypeError)):
            offer.offer_version = "2026-11-10"

    def test_thesis_indicator_semantic_review_and_rank_audit_bind_to_same_offer_version(self):
        records = [
            AccountThesis(
                company_id="C1",
                offer_id="offer-1",
                offer_version="2026-11-09",
                structural_fit=80,
                confidence="high",
                why_this_account="Residential portfolio fit",
                why_now="Portfolio expansion is current",
                problem_hypothesis="Operations are manual",
                strongest_claim_ids=["claim-1"],
                access_summary="Managing director identified",
                research_gap_impact="Could change outreach timing",
                recommended_action="contact",
            ),
            AccountIndicator(
                company_id="C1",
                offer_id="offer-1",
                offer_version="2026-11-09",
                indicator_type="trigger",
                statement="Portfolio expansion",
                strength=90,
                recency="2026-11-09",
                confidence="high",
                supporting_claim_ids=["claim-1"],
                counterevidence_claim_ids=[],
                offer_criterion="relevant_triggers",
            ),
            SemanticReview(
                company_id="C1",
                assertion_id="assertion-1",
                offer_id="offer-1",
                offer_version="2026-11-09",
                reviewed_claim_ids=["claim-1"],
                offer_criterion="relevant_triggers",
                entailment="supported",
                offer_relevance="relevant",
                temporal_relevance="current",
                contradiction_result="none",
                decision="approved",
                reason_codes=["supported"],
                reviewer_id="reviewer-1",
            ),
            RankAudit(
                company_id="C1",
                offer_id="offer-1",
                offer_version="2026-11-09",
                priority_state="Priority — verified trigger",
                total_score=100,
                contributions=[
                    RankContribution(
                        dimension="fit",
                        value=80,
                        weight=1,
                        contribution=80,
                        offer_criterion="target_customer",
                    ),
                    RankContribution(
                        dimension="need",
                        value=20,
                        weight=1,
                        contribution=20,
                        offer_criterion="problems_solved",
                    ),
                ],
                rationale_claim_ids=["claim-1"],
            ),
        ]

        for record in records:
            with self.subTest(record=type(record).__name__):
                self.assertEqual(record.offer_id, "offer-1")
                self.assertEqual(record.offer_version, "2026-11-09")
                with self.assertRaises((ValidationError, TypeError)):
                    record.offer_id = "offer-2"
                with self.assertRaises((ValidationError, TypeError)):
                    record.offer_version = "2026-11-10"

    def test_commercial_records_require_offer_binding(self):
        with self.assertRaises(ValidationError):
            AccountThesis(
                company_id="C1",
                structural_fit=80,
                confidence="high",
                why_this_account="Residential portfolio fit",
                why_now="Portfolio expansion is current",
                problem_hypothesis="Operations are manual",
                strongest_claim_ids=["claim-1"],
                access_summary="Managing director identified",
                research_gap_impact="Could change outreach timing",
                recommended_action="contact",
            )
        with self.assertRaises(ValidationError):
            AccountIndicator(
                company_id="C1",
                indicator_type="trigger",
                statement="Portfolio expansion",
                strength=90,
                recency="2026-11-09",
                confidence="high",
                supporting_claim_ids=["claim-1"],
                offer_criterion="relevant_triggers",
            )
        with self.assertRaises(ValidationError):
            RankAudit(
                company_id="C1",
                priority_state="Priority — verified trigger",
                total_score=80,
                contributions=[
                    RankContribution(
                        dimension="fit",
                        value=80,
                        weight=1,
                        contribution=80,
                        offer_criterion="target_customer",
                    )
                ],
                rationale_claim_ids=["claim-1"],
            )

    def test_semantic_review_requires_entailment_offer_temporal_and_contradiction_decisions(self):
        fields = {
            "company_id": "C1",
            "assertion_id": "assertion-1",
            "offer_id": "offer-1",
            "offer_version": "2026-11-09",
            "reviewed_claim_ids": ["claim-1"],
            "offer_criterion": "relevant_triggers",
            "entailment": "supported",
            "offer_relevance": "relevant",
            "temporal_relevance": "current",
            "contradiction_result": "none",
            "decision": "approved",
            "reason_codes": ["supported"],
            "reviewer_id": "reviewer-1",
        }

        for required_field in ("entailment", "offer_relevance", "temporal_relevance", "contradiction_result"):
            with self.subTest(required_field=required_field):
                incomplete = {key: value for key, value in fields.items() if key != required_field}
                with self.assertRaises(ValidationError):
                    SemanticReview(**incomplete)

    def test_no_trigger_found_requires_complete_clean_coverage_manifest(self):
        base = {
            "company_id": "C1",
            "offer_id": "offer-1",
            "offer_version": "2026-11-09",
            "required_checks": ["official_site", "public_news"],
            "completed_checks": ["official_site", "public_news"],
            "provider_states": {"official_site": "available", "public_news": "available"},
            "truncated": False,
            "unresolved_candidates": 0,
            "trigger_state": "No trigger found",
        }

        self.assertEqual(CoverageManifest(**base).trigger_state, "No trigger found")

        invalid_manifests = (
            {**base, "completed_checks": ["official_site"]},
            {**base, "provider_states": {"official_site": "available", "public_news": "unavailable"}},
            {**base, "truncated": True},
            {**base, "unresolved_candidates": 1},
        )
        for manifest in invalid_manifests:
            with self.subTest(manifest=manifest):
                with self.assertRaises(ValidationError):
                    CoverageManifest(**manifest)


if __name__ == "__main__":
    unittest.main()
