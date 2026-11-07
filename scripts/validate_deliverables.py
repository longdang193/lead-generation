from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--qa-report", type=Path, required=True)
    args = parser.parse_args()
    errors = []
    if not args.workbook.exists():
        errors.append("workbook missing")
    else:
        workbook = load_workbook(args.workbook, read_only=True)
        required = ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources"]
        if workbook.sheetnames != required:
            errors.append("workbook tabs mismatch")
    if not args.deck.exists():
        errors.append("deck missing")
    elif len(Presentation(args.deck).slides) != 5:
        errors.append("deck must contain exactly five slides")
    if not args.qa_report.exists() or "Errors: 0" not in args.qa_report.read_text(encoding="utf-8"):
        errors.append("QA report missing or reports errors")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("deliverables valid: workbook, five-slide deck, and QA report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
