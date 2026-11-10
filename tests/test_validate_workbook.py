from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]


class ValidateWorkbookTests(unittest.TestCase):
    def test_account_intelligence_tabs_are_allowed_after_core_tabs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "workbook.xlsx"
            workbook = Workbook()
            workbook.remove(workbook.active)
            for name in (
                "01_All_Leads",
                "02_Qualification",
                "03_Priority_Leads",
                "04_Contacts",
                "05_Methodology_Sources",
                "06_Account_Dossiers",
            ):
                sheet = workbook.create_sheet(name)
                sheet.append(["status"])
            workbook.save(workbook_path)

            result = subprocess.run(
                [sys.executable, "scripts/validate_workbook.py", "--workbook", str(workbook_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
