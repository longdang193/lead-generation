from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_for_enrichment import eligible_for_enrichment, select_accounts


class SelectionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
