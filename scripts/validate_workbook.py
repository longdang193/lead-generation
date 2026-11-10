from __future__ import annotations

import argparse
import csv
from pathlib import Path

from openpyxl import load_workbook


REQUIRED = ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args()
    wb = load_workbook(args.workbook, read_only=True, data_only=False)
    errors = []
    if wb.sheetnames[: len(REQUIRED)] != REQUIRED:
        errors.append(f"sheet names/order mismatch: {wb.sheetnames}")
    for name in REQUIRED:
        ws = wb[name]
        if ws.max_row < 1 or ws.max_column < 1:
            errors.append(f"empty sheet: {name}")
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        if not any(headers):
            errors.append(f"missing headers: {name}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"valid workbook: {args.workbook} ({len(REQUIRED)} sheets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
