from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]


class Task1WorkbookTests(unittest.TestCase):
    def test_unevaluated_kpis_are_explicitly_unknown(self):
        source = json.loads((Path("C:/tmp/berlin_hausverwaltungen_task1_build.json")).read_text(encoding="utf-8"))
        row = dict(source["rows"][0])
        row["Portfolio Size"] = None
        row["Portfolio Potential"] = None
        row["Structural Lead Fit"] = None
        row["Evidence Coverage"] = None
        source["rows"] = [row]
        source["priority_rows"] = [dict(row)]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            input_path = temp / "input.json"
            output_path = temp / "output.xlsx"
            preview_dir = temp / "previews"
            input_path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    "node",
                    "scripts/build_task1_workbook.mjs",
                    str(input_path),
                    str(output_path),
                    str(preview_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            workbook = load_workbook(output_path, read_only=False, data_only=True)
            sheet = workbook["Berlin Hausverwaltungen"]
            headers = [cell.value for cell in sheet[4]]
            values = [cell.value for cell in sheet[5]]
            by_header = dict(zip(headers, values))
            for header in ("Portfolio Size", "Portfolio Potential", "Structural Lead Fit", "Evidence Coverage"):
                self.assertEqual(by_header[header], "Unknown")
            workbook.close()


if __name__ == "__main__":
    unittest.main()
