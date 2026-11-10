from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from score_leads import build_rank_audit, calculate_fit, classify_signal, derive_account_signal, priority_reason, project_commercial_dimensions, rank_account
from account_intelligence import project_account_intelligence
from typed_contracts import MaterialAssertion
from collect_buying_signals import account_research_state
from extract_website_evidence import claim


class ScoringTests(unittest.TestCase):
    def review(self, company_id: str, claim_id: str, assertion_id: str) -> dict[str, object]:
        return {
            "assertion_id": assertion_id, "company_id": company_id, "offer_id": "offer-1", "offer_version": "2026-11-09",
            "reviewed_claim_ids": [claim_id], "offer_criterion": "relevant_triggers", "entailment": "supported",
            "offer_relevance": "relevant", "temporal_relevance": "current", "contradiction_result": "none",
            "decision": "approved", "reason_codes": ["supported"], "reviewer_id": "reviewer-1", "receipt_id": "review-action:attempt-1",
        }

    def test_rank_requires_offer_bound_semantic_thesis(self):
        with self.assertRaisesRegex(ValueError, "semantic"):
            rank_account({"company_id": "C1", "structural_lead_fit": 80}, "offer-1", "2026-11-09")

    def test_verified_change_can_outrank_larger_account_without_trigger(self):
        offer_id = "offer-1"
        offer_version = "2026-11-09"
        smaller = {
            "company_id": "C1", "offer_id": offer_id, "offer_version": offer_version,
            "semantic_review_ids": ["r1"], "semantic_reviews": [self.review("C1", "c1", "r1")], "strongest_claim_ids": ["c1"],
            "structural_lead_fit": 70, "opportunity_score": 80, "need_score": 85,
            "change_score": 100, "direct_intent_score": 70, "access_score": 60,
            "evidence_confidence_score": 90, "buying_signal": "Verified trigger",
            "why_this_account": "Current change matches the offer", "why_now": "Verified change this quarter",
        }
        larger = {
            "company_id": "C2", "offer_id": offer_id, "offer_version": offer_version,
            "semantic_review_ids": ["r2"], "semantic_reviews": [self.review("C2", "c2", "r2")], "strongest_claim_ids": ["c2"],
            "structural_lead_fit": 95, "opportunity_score": 40, "need_score": 30,
            "change_score": 0, "direct_intent_score": 0, "access_score": 60,
            "evidence_confidence_score": 80, "buying_signal": "No trigger found",
            "why_this_account": "Large portfolio fit", "why_now": "No current change found",
        }
        self.assertGreater(rank_account(smaller, offer_id, offer_version).total_score, rank_account(larger, offer_id, offer_version).total_score)
        self.assertIn("Current change", priority_reason(smaller))

    def test_priority_reason_explains_semantic_selection(self):
        row = {
            "selection_rationale": {
                "summary": "Portfolio growth creates operating complexity",
                "observations": [{"observation": "New mandates", "implication": "More administrative load", "claim_id": "c1", "source_url": "https://example.com/account"}],
                "opportunity_hypothesis": "Scalable process support may be relevant",
                "counterevidence": ["Current software stack is unknown"],
                "confidence": "medium",
                "comparative_basis": "Stronger change evidence than comparable accounts",
                "reversal_condition": "Deprioritize if the workflow is already integrated",
                "recommended_action": "Research the current operating stack",
                "unresolved_gaps": ["Buyer identity"],
            }
        }
        reason = priority_reason(row)
        self.assertIn("Portfolio growth creates operating complexity", reason)
        self.assertIn("Stronger change evidence", reason)
        self.assertIn("Deprioritize if", reason)
        self.assertIn("Research the current operating stack", reason)

    def test_rank_audit_exposes_reproducible_dimension_contributions(self):
        row = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09",
            "semantic_review_ids": ["r1"], "semantic_reviews": [self.review("C1", "c1", "r1")], "strongest_claim_ids": ["c1"],
            "structural_lead_fit": 80, "opportunity_score": 70, "need_score": 60,
            "change_score": 50, "direct_intent_score": 40, "access_score": 30,
            "evidence_confidence_score": 90, "buying_signal": "No trigger found",
        }
        audit = build_rank_audit(row, "offer-1", "2026-11-09", semantic_reviews=row["semantic_reviews"])
        self.assertEqual(sum(item.contribution for item in audit.contributions), audit.total_score)
        self.assertEqual(audit.rationale_claim_ids, ["c1"])

    def test_explicit_zero_direct_intent_is_not_replaced_by_signal_strength(self):
        row = {"direct_intent_score": 0, "buying_signal": "Verified trigger"}
        from score_leads import _commercial_dimension_value
        self.assertEqual(_commercial_dimension_value(row, "direct_intent"), 0.0)

    def test_access_gap_does_not_receive_access_credit(self):
        thesis = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 80,
            "confidence": "high", "why_this_account": "Fit", "why_now": "Now", "problem_hypothesis": "Need",
            "strongest_claim_ids": ["c1"], "semantic_review_ids": ["r1"], "access_summary": "No buyer identified",
            "research_gap_impact": "Buyer identity could change outreach", "recommended_action": "research",
        }
        dimensions = project_commercial_dimensions(thesis, [])
        self.assertEqual(dimensions["access"]["value"], 0.0)

    def test_generated_dossier_uses_semantic_review_identity_for_ranking(self):
        claim = {
            "candidate_claim_id": "c1", "company_id": "C1", "claim_type": "event",
            "claim_value": {"event_id": "E1"}, "source_url": "https://example.com/source",
            "source_kind": "other", "evidence_excerpt": "Observed", "confidence": "high",
            "retrieved_at": "2026-11-09T00:00:00Z", "candidate_status": "Verified", "assurance_level": "source",
        }
        assertions = [
            {"assertion_id": "m1", "assertion_kind": "why_this_account", "statement": "Fit", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "offer_criterion": "relevant_triggers", "supporting_claim_ids": ["c1"]},
            {"assertion_id": "m2", "assertion_kind": "why_now", "statement": "Now", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "offer_criterion": "relevant_triggers", "supporting_claim_ids": ["c1"]},
            {"assertion_id": "m3", "assertion_kind": "problem_hypothesis", "statement": "Need", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "offer_criterion": "relevant_triggers", "supporting_claim_ids": ["c1"]},
        ]
        reviews = [
            {**self.review("C1", "c1", assertion["assertion_id"]), "assertion_hash": MaterialAssertion.model_validate(assertion).content_hash}
            for assertion in assertions
        ]
        thesis = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 0,
            "confidence": "high", "why_this_account": "Fit", "why_now": "Now", "problem_hypothesis": "Need",
            "strongest_claim_ids": ["c1"], "access_summary": "Path", "research_gap_impact": "None",
            "semantic_review_ids": ["m1", "m2", "m3"], "recommended_action": "contact",
            "material_assertions": assertions,
        }
        dossier = project_account_intelligence([claim], thesis, semantic_reviews=reviews)
        audit = rank_account({"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "buying_signal": "Verified trigger"}, "offer-1", "2026-11-09", dossier=dossier)
        self.assertTrue(audit.contributions)
    def test_rank_audit_uses_validated_signal_projection_not_forged_record_signal(self):
        row = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09",
            "semantic_review_ids": ["r1"], "strongest_claim_ids": ["c1"],
            "buying_signal": "Verified trigger", "validated_signal_state": "Research incomplete",
        }
        projected = {name: {"value": 80, "supporting_claim_ids": ["c1"], "offer_criterion": name} for name in ("fit", "opportunity", "need", "change", "direct_intent", "access", "evidence_confidence")}
        audit = build_rank_audit(row, "offer-1", "2026-11-09", semantic_reviews=[self.review("C1", "c1", "r1")], projected_dimensions=projected)
        self.assertEqual(audit.priority_state, "Research required")

    def test_production_thesis_rejects_unassured_supporting_claim(self):
        claim = {
            "candidate_claim_id": "c1", "company_id": "C1", "claim_type": "event", "claim_value": {"event_id": "E1"},
            "source_url": "https://example.com/source", "source_kind": "other", "evidence_excerpt": "Observed",
            "confidence": "high", "retrieved_at": "2026-11-09T00:00:00Z", "candidate_status": "Candidate", "assurance_level": "replay",
        }
        thesis = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 0,
            "confidence": "high", "why_this_account": "Fit", "why_now": "Now", "problem_hypothesis": "Need",
            "strongest_claim_ids": ["c1"], "access_summary": "Path", "research_gap_impact": "None",
            "semantic_review_ids": ["a1"], "recommended_action": "contact",
        }
        with self.assertRaisesRegex(ValueError, "source assurance"):
            project_account_intelligence([claim], thesis, semantic_reviews=[self.review("C1", "c1", "a1")])

    def test_production_thesis_requires_reviewed_exported_conclusions(self):
        claim = {
            "candidate_claim_id": "c1", "company_id": "C1", "claim_type": "event", "claim_value": {"event_id": "E1"},
            "source_url": "https://example.com/source", "source_kind": "other", "evidence_excerpt": "Observed",
            "confidence": "high", "retrieved_at": "2026-11-09T00:00:00Z", "candidate_status": "Verified", "assurance_level": "source",
        }
        thesis = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 0,
            "confidence": "high", "why_this_account": "Fit", "why_now": "Now", "problem_hypothesis": "Need",
            "strongest_claim_ids": ["c1"], "access_summary": "Path", "research_gap_impact": "None",
            "semantic_review_ids": ["a1"], "recommended_action": "contact",
        }
        with self.assertRaisesRegex(ValueError, "material assertions"):
            project_account_intelligence([claim], thesis, semantic_reviews=[self.review("C1", "c1", "a1")])

    def test_verified_trigger_cannot_override_disqualifying_fit(self):
        row = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09",
            "semantic_review_ids": ["r1"], "semantic_reviews": [self.review("C1", "c1", "r1")], "strongest_claim_ids": ["c1"],
            "structural_lead_fit": 0, "buying_signal": "Verified trigger",
        }
        self.assertEqual(rank_account(row, "offer-1", "2026-11-09").priority_state, "Disqualify")
    def test_freshness_only_signal_does_not_become_commercially_strong(self):
        today = date.today()
        self.assertEqual(classify_signal([]), "None found")
        self.assertEqual(classify_signal([{"publication_date": today.isoformat(), "deadline": "Unknown"}]), "Medium")
        self.assertEqual(classify_signal([{"publication_date": (today - timedelta(days=240)).isoformat(), "deadline": "Unknown"}]), "Medium")
        self.assertEqual(classify_signal([{"publication_date": (today - timedelta(days=500)).isoformat(), "deadline": "Unknown"}]), "Weak")
        self.assertEqual(classify_signal([{"publication_date": "Unknown", "deadline": "Unknown"}]), "Unknown")

    def test_signal_classification_accepts_manifest_bound_as_of_date(self):
        self.assertEqual(classify_signal([{"publication_date": "2026-01-01", "deadline": "Unknown"}], date(2026, 11, 9)), "Medium")

    def test_structural_portfolio_size_does_not_inflate_fit(self):
        fit, coverage = calculate_fit({
            "service_fit": "Confirmed",
            "residential_weg": "Confirmed",
            "portfolio_size": 500,
            "berlin_relevance": "Confirmed",
            "field_assurance": {"portfolio_size": "structural"},
        })
        self.assertEqual(coverage, 75)
        self.assertEqual(fit, 75.0)

    def test_recent_incomplete_event_does_not_borrow_strength_from_expired_event(self):
        self.assertEqual(
            classify_signal([
                {"publication_date": "2026-11-01", "deadline": "Unknown", "assurance_level": "source", "verification_status": "Verified", "event_type": "tender", "buyer": "C1", "title": "Open tender", "source_url": "https://example.de/open"},
                {"publication_date": "2026-01-01", "deadline": "2026-11-08", "assurance_level": "source", "verification_status": "Verified", "event_type": "tender", "buyer": "C1", "title": "Expired tender", "source_url": "https://example.de/expired"},
            ],
            date(2026, 11, 9),
        ), "Medium")

    def test_ordinary_weg_word_is_not_condominium_evidence(self):
        value, _, _ = claim("Wir weisen den Weg zu guter Verwaltung.", [r"wohnungseigent[üu]mergemeinschaft", r"\bweg[- ]verwaltung\b", r"eigent[üu]mergemeinschaft"])
        self.assertEqual(value, "Unknown")

    def test_fit_uses_fixed_denominator_without_silent_renormalization(self):
        fit, coverage = calculate_fit({"service_fit": "Confirmed"})
        self.assertEqual(coverage, 35)
        self.assertEqual(fit, 35.0)

    def test_account_research_states_do_not_use_global_none_found_defaults(self):
        self.assertEqual(account_research_state(configured=True, successful_terms=4, required_terms=4, event_count=0, account_scoped=True), ("Completed", "None found"))
        self.assertEqual(account_research_state(configured=True, successful_terms=2, required_terms=4, event_count=0), ("Partial", "Unknown"))
        self.assertEqual(account_research_state(configured=False, successful_terms=0, required_terms=4, event_count=0), ("Unavailable", "Unknown"))
        self.assertEqual(account_research_state(configured=True, successful_terms=4, required_terms=4, event_count=0, truncated=True), ("Partial", "Unknown"))
        self.assertEqual(account_research_state(configured=True, successful_terms=4, required_terms=4, event_count=0, account_scoped=False), ("Partial", "Unknown"))
        self.assertEqual(derive_account_signal({}, [], "Searched"), ("Unknown", "Unknown"))
        self.assertEqual(
            derive_account_signal({"research_status": "Completed", "signal_state": "None found", "coverage_status": "partial"}, [], "Searched"),
            ("Research incomplete", "Unknown"),
        )

    def test_positive_audit_without_verified_event_link_stays_unknown(self):
        self.assertEqual(
            derive_account_signal({"research_status": "Completed", "search_status": "Searched", "signal_state": "Strong"}, [], "Searched"),
            ("Unknown", "Unknown"),
        )

    def test_verified_event_survives_partial_signal_research(self):
        signal, status = derive_account_signal(
            {"research_status": "Partial", "signal_state": "Unknown"},
            [{"publication_date": date.today().isoformat(), "deadline": "2026-12-01", "event_type": "tender", "buyer": "C1", "title": "Current tender", "source_url": "https://example.de/tender", "assurance_level": "source", "verification_status": "Verified"}],
            "Searched",
        )
        self.assertEqual(signal, "Strong")
        self.assertEqual(status, "Unknown")

    def test_structural_event_without_verified_link_stays_unknown(self):
        self.assertEqual(
            derive_account_signal({"research_status": "Completed", "search_status": "Searched", "signal_state": "Unknown", "verified_claim_count": "1"}, [], "Searched"),
            ("Unknown", "Unknown"),
        )


if __name__ == "__main__":
    unittest.main()
