from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_for_enrichment import eligible_for_enrichment


class SelectionTests(unittest.TestCase):
    def test_missing_qualification_is_not_eligible(self):
        row = {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "75"}
        self.assertFalse(eligible_for_enrichment(row, {}))

    def test_qualification_must_explicitly_accept_company(self):
        row = {"company_id": "C1", "lead_tier": "A", "evidence_coverage": "75"}
        self.assertFalse(eligible_for_enrichment(row, {"resolution_status": "Accepted", "eligible": False}))
        self.assertTrue(eligible_for_enrichment(row, {"resolution_status": "Accepted", "eligible": True}))


if __name__ == "__main__":
    unittest.main()
