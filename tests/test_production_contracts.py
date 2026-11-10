from __future__ import annotations

import sys
import unittest
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_manifest import _validate_finalization_artifacts, finalization_eligibility


class ProductionContractTests(unittest.TestCase):
    def test_production_finalization_requires_manifest_bound_dossier_and_ranking(self):
        eligible, errors = finalization_eligibility(
            {
                "account_intelligence_mode": "production",
                "outputs": {"workbook": {"path": "workbook.xlsx", "sha256": "0" * 64}},
                "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "complete"},
                "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 0, "delivered_count": 0, "shortfall": 0},
            },
            "strict",
        )
        self.assertFalse(eligible)
        self.assertTrue(any("dossier" in error for error in errors))
        self.assertTrue(any("ranking" in error for error in errors))

    def test_production_finalization_accepts_account_dossier_workbook_tabs(self):
        root = Path(__file__).resolve().parents[1]
        workbook_path = root / "tests" / ".tmp-production-contract.xlsx"
        workbook = Workbook()
        workbook.active.title = "01_All_Leads"
        for name in ("02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources", "06_Account_Dossiers", "07_Account_Theses", "08_Account_Timeline", "09_Evidence_Ledger", "10_Research_Gaps"):
            workbook.create_sheet(name)
        workbook.save(workbook_path)
        try:
            errors: list[str] = []
            _validate_finalization_artifacts(
                root,
                {"run_id": "run-1", "account_intelligence_mode": "production"},
                {"workbook": {"path": str(workbook_path)}},
                {"workbook": workbook_path},
                errors,
            )
            self.assertFalse(any("workbook tabs" in error for error in errors), errors)
        finally:
            workbook_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
