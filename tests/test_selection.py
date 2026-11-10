from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_for_enrichment import eligible_for_enrichment, select_accounts


class SelectionTests(unittest.TestCase):
    def test_production_selection_rejects_structural_only_rows(self):
        row = {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "90", "rank_audit": "", "dossier_hash": ""}
        qualification = {"resolution_status": "Accepted", "eligible": True}
        self.assertFalse(eligible_for_enrichment(row, qualification, production=True))

    def test_production_selection_requires_complete_dossier_lineage(self):
        row = {
            "company_id": "C1",
            "lead_tier": "A",
            "evidence_coverage": "90",
            "rank_audit": "rank-1",
            "dossier_hash": "dossier-1",
            "semantic_review_ids": "",
            "strongest_claim_ids": "claim-1",
            "projection_run_id": "run-1",
        }
        qualification = {"resolution_status": "Accepted", "eligible": True}
        self.assertFalse(eligible_for_enrichment(row, qualification, production=True))

    def test_production_selection_rejects_structural_sort_without_commercial_audit(self):
        row = {
            "company_id": "C1", "lead_tier": "A", "evidence_coverage": "90",
            "rank_audit": "{\"priority_state\": \"Priority\"}", "dossier_hash": "dossier-1",
            "semantic_review_ids": "review-1", "strongest_claim_ids": "claim-1", "projection_run_id": "run-1",
        }
        qualification = {"C1": {"resolution_status": "Accepted", "eligible": True}}
        self.assertEqual(select_accounts([row], qualification, 1, production=True), [])

    def test_missing_qualification_is_not_eligible(self):
        row = {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "75"}
        self.assertFalse(eligible_for_enrichment(row, {}))

    def test_qualification_must_explicitly_accept_company(self):
        row = {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "75"}
        self.assertFalse(eligible_for_enrichment(row, {"resolution_status": "Accepted", "eligible": False}))
        self.assertTrue(eligible_for_enrichment(row, {"resolution_status": "Accepted", "eligible": True}))

    def test_personal_probable_rows_remain_selectable_but_strict_rows_do_not(self):
        row = {"lead_tier": "Research", "evidence_coverage": "100"}
        qualification = {"resolution_status": "Accepted", "eligible": True, "berlin_relevance": "Probable"}
        self.assertFalse(eligible_for_enrichment(row, qualification, "strict"))
        self.assertTrue(eligible_for_enrichment(row, qualification, "personal"))

    def test_manifest_company_scope_excludes_other_eligible_rows(self):
        scores = [
            {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "75", "sales_priority": "Research", "structural_lead_fit": "80", "portfolio_potential": "50", "buying_signal": "None found"},
            {"company_id": "C2", "lead_tier": "A", "evidence_coverage": "75", "sales_priority": "Research", "structural_lead_fit": "80", "portfolio_potential": "50", "buying_signal": "None found"},
        ]
        qualification = {company_id: {"resolution_status": "Accepted", "eligible": True} for company_id in ("C1", "C2")}
        selected = select_accounts(scores, qualification, 30, {"C1"})
        self.assertEqual([row["company_id"] for row in selected], ["C1"])

    def test_source_assurance_and_research_gaps_break_score_ties(self):
        scores = [
            {"company_id": "replay", "lead_tier": "A", "evidence_coverage": "80", "sales_priority": "Pursue", "structural_lead_fit": "80", "portfolio_potential": "50", "buying_signal": "Strong", "assurance_level": "replay", "research_gap": "contact"},
            {"company_id": "source", "lead_tier": "A", "evidence_coverage": "80", "sales_priority": "Pursue", "structural_lead_fit": "80", "portfolio_potential": "50", "buying_signal": "Strong", "assurance_level": "source", "research_gap": "None"},
        ]
        qualification = {company_id: {"resolution_status": "Accepted", "eligible": True} for company_id in ("replay", "source")}
        selected = select_accounts(scores, qualification, 2)
        self.assertEqual([row["company_id"] for row in selected], ["source", "replay"])


if __name__ == "__main__":
    unittest.main()
