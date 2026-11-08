from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule

from runtime_config import RuntimeConfig, provider_limitation
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    numeric_fields = {"portfolio_size", "portfolio_potential", "structural_lead_fit", "evidence_coverage"}
    nullable_unknown_fields = {"contact_email", "email_source", "linkedin_url", "last_verified"}
    for row in rows:
        values = []
        for header in headers:
            value = row.get(header, "")
            if header in numeric_fields:
                if value in (None, "", "Unknown"):
                    value = None
                else:
                    try:
                        value = float(value)
                        if value.is_integer():
                            value = int(value)
                    except (TypeError, ValueError):
                        pass
            elif header in nullable_unknown_fields and value == "Unknown":
                value = None
            values.append(value)
        ws.append(values)
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
    parser.add_argument("--run-manifest", type=Path)
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
    inputs = {name: {"path": str(path), "sha256": file_sha256(path)} for name, path in {
        "companies": args.companies,
        "scores": args.scores,
        "priority": args.priority,
        "contacts": args.contacts,
        "sources": args.sources,
    }.items() if path.exists()}
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_seed = "|".join(item["sha256"] for item in inputs.values()) + generated_at
    run_id = "lead-" + hashlib.sha256(run_seed.encode("utf-8")).hexdigest()[:16]
    report["run_id"] = run_id
    args.build_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        git_revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        git_ref = subprocess.run(["git", "branch", "--show-current"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        git_revision = ""
        git_ref = ""
    supporting_candidates = {
        "schema": Path("config/lead_generation_schema.json"),
        "website_evidence": Path("data/intermediate/website_evidence_2026-11-08.jsonl"),
        "source_register": Path("evidence/source_register_2026-11-07.csv"),
        "entity_resolution": Path("evidence/entity_resolution_2026-11-07.csv"),
        "buying_signal_audit": Path("evidence/buying_signal_audit_2026-11-08.csv"),
        "buying_events": Path("data/raw/buying_events_2026-11-08.json"),
        "scoring_audit": Path("evidence/scoring_audit_2026-11-08.csv"),
        "contact_sources": Path("evidence/contact_sources_2026-11-08.csv"),
    }
    manifest = {
        "run_id": run_id,
        "generated_at": generated_at,
        "config_version": "lead-generation-contract-v2",
        "git_revision": git_revision,
        "git_ref": git_ref,
        "inputs": inputs,
        "supporting_inputs": {name: {"path": str(path).replace("\\", "/"), "sha256": file_sha256(path)} for name, path in supporting_candidates.items() if path.exists()},
        "outputs": {
            "workbook": {"path": str(args.output), "sha256": file_sha256(args.output)},
            "build_report": {"path": str(args.build_report), "sha256": file_sha256(args.build_report)},
        },
        "counts": report["counts"],
    }
    if args.run_manifest:
        args.run_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.run_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
