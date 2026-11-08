from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule

from runtime_config import RuntimeConfig, provider_limitation
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_sheet(ws, rows: list[dict[str, str]], widths: dict[str, int] | None = None):
    if not rows:
        rows = [{"Status": "No records"}]
    headers = list(rows[0])
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header, "") for header in headers])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    fill = PatternFill("solid", fgColor="1F4E78")
    for cell in ws[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for idx, header in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = (widths or {}).get(header, min(max(len(header) + 2, 12), 34))
    for col in range(1, ws.max_column + 1):
        if "url" in str(ws.cell(1, col).value).lower() or "source" in str(ws.cell(1, col).value).lower():
            for row in range(2, ws.max_row + 1):
                value = ws.cell(row, col).value
                if isinstance(value, str) and value.startswith("http"):
                    ws.cell(row, col).hyperlink = value
                    ws.cell(row, col).style = "Hyperlink"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--priority", type=Path, required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-report", type=Path, required=True)
    args = parser.parse_args()
    companies = read_csv(args.companies)
    scores = read_csv(args.scores)
    priority = read_csv(args.priority)
    contacts = read_csv(args.contacts)
    sources = read_csv(args.sources)
    wb = Workbook()
    ws = wb.active
    ws.title = "01_All_Leads"
    write_sheet(ws, companies)
    ws = wb.create_sheet("02_Qualification")
    write_sheet(ws, scores)
    for row in range(2, ws.max_row + 1):
        score_cell = ws.cell(row, 11)
        if isinstance(score_cell.value, (int, float)):
            score_cell.number_format = "0.00"
    if ws.max_row > 2:
        ws.conditional_formatting.add(f"K2:K{ws.max_row}", ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))
    ws = wb.create_sheet("03_Priority_Leads")
    write_sheet(ws, priority)
    ws = wb.create_sheet("04_Contacts")
    write_sheet(ws, contacts)
    methodology = [
        {"Topic": "Objective", "Definition": "Evidence-backed Berlin-relevant Hausverwaltung lead generation MVP."},
        {"Topic": "Structural Lead Fit", "Definition": "Observed-weight score excluding Buying Signal and Actionability."},
        {"Topic": "Weights", "Definition": "Service/ICP 35%; residential/WEG 30%; portfolio 25%; geography 10%."},
        {"Topic": "Evidence Coverage", "Definition": "Observed declared structural weight divided by 100."},
        {"Topic": "Unknown handling", "Definition": "Unknown stays Unknown and is excluded from observed-weight score numerator and denominator."},
        {"Topic": "A tier", "Definition": "Structural fit >= 70 and evidence coverage >= 75%."},
        {"Topic": "Source policy", "Definition": "VDIV directory for discovery; official websites for qualification; public contact pages for contacts."},
        {"Topic": "Buying signals", "Definition": "Separate event dataset; no account signal without verified company-event match."},
        {"Topic": "Limitations", "Definition": provider_limitation(RuntimeConfig.from_env())},
        {"Topic": "Retrieval", "Definition": "Public VDIV page and official company websites retrieved during 2026-11-07/08 execution."},
    ]
    ws = wb.create_sheet("05_Methodology_Sources")
    write_sheet(ws, methodology, {"Topic": 24, "Definition": 110})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    report = {"sheets": wb.sheetnames, "counts": {"companies": len(companies), "scores": len(scores), "priority": len(priority), "contacts": len(contacts), "sources": len(sources)}}
    args.build_report.parent.mkdir(parents=True, exist_ok=True)
    args.build_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
