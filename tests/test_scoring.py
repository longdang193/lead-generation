from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from score_leads import build_rank_audit, calculate_fit, classify_signal, derive_account_signal, priority_reason, rank_account
from collect_buying_signals import account_research_state
from extract_website_evidence import claim


class ScoringTests(unittest.TestCase):
    def test_rank_requires_offer_bound_semantic_thesis(self):
        with self.assertRaisesRegex(ValueError, "semantic"):
            rank_account({"company_id": "C1", "structural_lead_fit": 80}, "offer-1", "2026-11-09")

    def test_verified_change_can_outrank_larger_account_without_trigger(self):
        offer_id = "offer-1"
        offer_version = "2026-11-09"
        smaller = {
            "company_id": "C1", "offer_id": offer_id, "offer_version": offer_version,
            "semantic_review_approved": True, "strongest_claim_ids": ["c1"],
            "structural_lead_fit": 70, "opportunity_score": 80, "need_score": 85,
            "change_score": 100, "direct_intent_score": 70, "access_score": 60,
            "evidence_confidence_score": 90, "buying_signal": "Verified trigger",
            "why_this_account": "Current change matches the offer", "why_now": "Verified change this quarter",
        }
        larger = {
            "company_id": "C2", "offer_id": offer_id, "offer_version": offer_version,
            "semantic_review_approved": True, "strongest_claim_ids": ["c2"],
            "structural_lead_fit": 95, "opportunity_score": 40, "need_score": 30,
            "change_score": 0, "direct_intent_score": 0, "access_score": 60,
            "evidence_confidence_score": 80, "buying_signal": "No trigger found",
            "why_this_account": "Large portfolio fit", "why_now": "No current change found",
        }
        self.assertGreater(rank_account(smaller, offer_id, offer_version).total_score, rank_account(larger, offer_id, offer_version).total_score)
        self.assertIn("Current change", priority_reason(smaller))

    def test_rank_audit_exposes_reproducible_dimension_contributions(self):
        row = {
            "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09",
            "semantic_review_approved": True, "strongest_claim_ids": ["c1"],
            "structural_lead_fit": 80, "opportunity_score": 70, "need_score": 60,
            "change_score": 50, "direct_intent_score": 40, "access_score": 30,
            "evidence_confidence_score": 90, "buying_signal": "No trigger found",
        }
        audit = build_rank_audit(row, "offer-1", "2026-11-09")
        self.assertEqual(sum(item.contribution for item in audit.contributions), audit.total_score)
        self.assertEqual(audit.rationale_claim_ids, ["c1"])
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
