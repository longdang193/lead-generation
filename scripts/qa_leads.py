from __future__ import annotations

import argparse
import csv
import json
import hashlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import load_workbook

from runtime_config import RuntimeConfig, provider_limitation
from lead_contract import ACTIONABILITY, BUYING_SIGNALS, SEARCH_STATUSES, SALES_PRIORITIES, actionability_for, is_generic_mailbox, is_plausible_full_name, parse_evidence_urls, sales_priority_for


def rows(ws):
    values = list(ws.values)
    return [dict(zip(values[0], row)) for row in values[1:] if any(value not in (None, "") for value in row)] if values else []


def contact_email_status_summary(contacts: list[dict[str, object]]) -> dict[str, int]:
    return {
        status: sum(
            1
            for row in contacts
            if row.get("contact_email") not in (None, "", "Unknown") and row.get("verification_status") == status
        )
        for status in ("Published", "Verified", "Unverified")
        if any(
            row.get("contact_email") not in (None, "", "Unknown") and row.get("verification_status") == status
            for row in contacts
        )
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_http_url(value: object) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, default=Path("evidence/run_manifest_2026-11-09.json"))
    args = parser.parse_args()
    wb = load_workbook(args.workbook, read_only=True, data_only=False)
    qualification = rows(wb["02_Qualification"])
    priority = rows(wb["03_Priority_Leads"])
    contacts = rows(wb["04_Contacts"])
    errors: list[str] = []
    if not args.run_manifest.exists():
        errors.append("run manifest missing")
    else:
        try:
            manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
            expected = manifest.get("outputs", {}).get("workbook", {}).get("sha256")
            if expected != file_sha256(args.workbook):
                errors.append("workbook hash does not match run manifest")
            if not manifest.get("run_id") or not manifest.get("generated_at") or not manifest.get("config_version"):
                errors.append("run manifest lacks run identity or configuration version")
        except (OSError, ValueError, KeyError):
            errors.append("run manifest is unreadable")
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        properties = schema.get("properties", {})
    except (OSError, ValueError):
        properties = {}
        errors.append("schema is unreadable")
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
        for field, allowed in (("buying_signal", BUYING_SIGNALS), ("signal_search_status", SEARCH_STATUSES), ("actionability", ACTIONABILITY), ("sales_priority", SALES_PRIORITIES)):
            if row.get(field) not in allowed:
                errors.append(f"invalid {field}: {row.get('company_id')}")
        if row.get("signal_search_status") == "Searched" and row.get("buying_signal") == "Unknown":
            errors.append(f"completed search left buying signal Unknown: {row.get('company_id')}")
        try:
            coverage = float(row.get("evidence_coverage")) if row.get("evidence_coverage") not in (None, "", "Unknown") else None
        except ValueError:
            coverage = None
        expected_actionability = actionability_for(row.get("lead_tier", ""), coverage, row.get("buying_signal", "Unknown"))
        if row.get("actionability") != expected_actionability:
            errors.append(f"actionability mismatch: {row.get('company_id')}")
        if row.get("sales_priority") != sales_priority_for(expected_actionability, row.get("lead_tier", "")):
            errors.append(f"sales priority mismatch: {row.get('company_id')}")
        for field in ("service_fit", "residential_weg", "berlin_relevance"):
            if row.get(field) not in (None, "", "Unknown"):
                urls = parse_evidence_urls(row.get("evidence_urls"))
                if not urls or not all(valid_http_url(url) for url in urls):
                    errors.append(f"{field} claim lacks valid evidence URL: {row.get('company_id')}")
        if row.get("lead_tier") == "A" and row.get("sales_priority") == "Pursue" and row.get("actionability") != "Ready":
            errors.append(f"Pursue row is not Ready: {row.get('company_id')}")
    for row in contacts:
        if row.get("contact_email") not in (None, "", "Unknown"):
            if not valid_http_url(row.get("email_source")) or row.get("verification_status") in (None, "", "Unknown") or row.get("last_verified") in (None, "", "Unknown"):
                errors.append(f"contact email lacks provenance: {row.get('company_id')}")
            if row.get("verification_status") == "Verified" and is_generic_mailbox(row.get("contact_email")):
                errors.append(f"generic mailbox marked Verified: {row.get('company_id')}")
        if row.get("contact_name") not in (None, "", "Unknown") and not is_plausible_full_name(row.get("contact_name")):
            errors.append(f"contact name is not a plausible full name: {row.get('company_id')}")
    qualification_ids = {row.get("company_id") for row in qualification}
    priority_ids = [row.get("company_id") for row in priority]
    if any(company_id not in qualification_ids for company_id in priority_ids):
        errors.append("priority contains company IDs absent from qualification")
    if len(priority_ids) != len(set(priority_ids)):
        errors.append("priority contains duplicate company IDs")
    sample = priority[:10] + [row for row in qualification if row not in priority][:1]
    args.sample_output.parent.mkdir(parents=True, exist_ok=True)
    with args.sample_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(sample[0]) if sample else ["company_id"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sample)
    tier_counts = Counter(row.get("lead_tier") for row in qualification)
    report = ["# Lead QA Report", "", f"- Qualification rows: {len(qualification)}", f"- Priority rows: {len(priority)}", f"- Contact rows: {len(contacts)}", f"- Tier distribution: {dict(tier_counts)}", f"- Contact email status: {contact_email_status_summary(contacts)}", f"- Errors: {len(errors)}", "", "## Limitations", f"- {provider_limitation(RuntimeConfig.from_env())}", "- Website fetch failures and unresolved claims remain explicit as Unknown in the capture and scoring outputs."]
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
