from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

from runtime_config import RuntimeConfig, provider_limitation


def rows(ws):
    values = list(ws.values)
    return [dict(zip(values[0], row)) for row in values[1:] if any(value not in (None, "") for value in row)] if values else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-output", type=Path, required=True)
    args = parser.parse_args()
    wb = load_workbook(args.workbook, read_only=True, data_only=False)
    qualification = rows(wb["02_Qualification"])
    priority = rows(wb["03_Priority_Leads"])
    contacts = rows(wb["04_Contacts"])
    errors: list[str] = []
    company_ids = [row.get("company_id") for row in qualification]
    duplicates = [item for item, count in Counter(company_ids).items() if item and count > 1]
    if duplicates:
        errors.append(f"duplicate company IDs: {duplicates[:5]}")
    for row in qualification:
        fit = row.get("structural_lead_fit")
        if fit not in (None, "", "Unknown") and not 0 <= float(fit) <= 100:
            errors.append(f"score out of range: {row.get('company_id')}")
        if row.get("lead_tier") not in {"A", "B", "C", "Research"}:
            errors.append(f"invalid tier: {row.get('company_id')}")
        if row.get("lead_tier") == "A" and float(row.get("evidence_coverage") or 0) < 75:
            errors.append(f"A tier below coverage gate: {row.get('company_id')}")
    for row in contacts:
        if row.get("contact_email") not in (None, "", "Unknown"):
            if not row.get("email_source") or row.get("verification_status") in (None, "", "Unknown") or row.get("last_verified") in (None, "", "Unknown"):
                errors.append(f"contact email lacks provenance: {row.get('company_id')}")
    sample = priority[:10] + [row for row in qualification if row not in priority][:1]
    args.sample_output.parent.mkdir(parents=True, exist_ok=True)
    with args.sample_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(sample[0]) if sample else ["company_id"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sample)
    tier_counts = Counter(row.get("lead_tier") for row in qualification)
    report = ["# Lead QA Report", "", f"- Qualification rows: {len(qualification)}", f"- Priority rows: {len(priority)}", f"- Contact rows: {len(contacts)}", f"- Tier distribution: {dict(tier_counts)}", f"- Errors: {len(errors)}", "", "## Limitations", f"- {provider_limitation(RuntimeConfig.from_env())}", "- Website fetch failures and unresolved claims remain explicit as Unknown in the capture and scoring outputs."]
    if errors:
        report.extend(["", "## Errors", *[f"- {error}" for error in errors]])
    else:
        report.extend(["", "All deterministic QA checks passed."])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("qa_errors=%d" % len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
