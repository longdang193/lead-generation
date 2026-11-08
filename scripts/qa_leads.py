from __future__ import annotations

import argparse
import csv
import json
import hashlib
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from openpyxl import load_workbook

from runtime_config import RuntimeConfig, provider_limitation
from lead_contract import ACTIONABILITY, BUYING_SIGNALS, SEARCH_STATUSES, SALES_PRIORITIES, actionability_for, is_generic_mailbox, is_placeholder_email, is_plausible_company_name, is_plausible_full_name, parse_evidence_urls, sales_priority_for, is_valid_business_email, file_sha256, update_run_manifest
from score_leads import calculate_fit
from validate_deliverables import resolve_manifest_path, verify_manifest_bucket


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


def numeric(value: object) -> float | None:
    if value in (None, "", "Unknown"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


NULLABLE_UNKNOWN_FIELDS = {"legal_name", "domain", "address", "postal_code", "city", "region", "actor_id", "actor_run_id", "source_record_id", "contact_email", "email_source", "linkedin_url", "last_verified"}
SURFACE_REQUIRED = {
    "companies": ["company_id", "company_name", "source_url", "retrieved_at", "evidence_level"],
    "qualification": ["company_id", "company_name", "source_url", "retrieved_at", "service_fit", "residential_weg", "berlin_relevance", "structural_lead_fit", "evidence_coverage", "buying_signal", "signal_search_status", "actionability", "sales_priority", "lead_tier", "evidence_urls"],
    "priority": ["company_id", "company_name", "source_url", "retrieved_at", "service_fit", "residential_weg", "berlin_relevance", "structural_lead_fit", "evidence_coverage", "buying_signal", "signal_search_status", "actionability", "sales_priority", "lead_tier", "evidence_urls"],
    "contacts": ["company_id", "contact_name", "contact_role", "contact_email", "email_source", "verification_status", "last_verified"],
}


def schema_value(field: str, value: object) -> object:
    if field == "evidence_urls":
        return parse_evidence_urls(value)
    if field in NULLABLE_UNKNOWN_FIELDS and value == "Unknown":
        return None
    return value


def format_valid(value: object, format_name: str) -> bool:
    text = str(value)
    if format_name == "uri":
        return valid_http_url(value)
    if format_name == "email":
        return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text))
    if format_name == "date":
        try:
            from datetime import date
            date.fromisoformat(text)
            return True
        except ValueError:
            return False
    if format_name == "date-time":
        try:
            from datetime import datetime
            datetime.fromisoformat(text.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    return True


def type_valid(value: object, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    for item in expected_types:
        if item == "null" and value is None:
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "object" and isinstance(value, dict):
            return True
    return False


def append_schema_errors(errors: list[str], row: dict[str, object], schema: dict[str, object], required: list[str], surface: str) -> None:
    properties = schema.get("properties", {})
    normalized = {field: schema_value(field, value) for field, value in row.items()}
    for field in required:
        if field not in normalized or normalized.get(field) == "":
            errors.append(f"{surface} missing required field {field}: {row.get('company_id')}")
    for field, definition in properties.items():
        if field not in normalized or not isinstance(definition, dict):
            continue
        value = normalized[field]
        if value is None and "null" in (definition.get("type") if isinstance(definition.get("type"), list) else [definition.get("type")]):
            continue
        if "enum" in definition and value not in definition["enum"]:
            errors.append(f"{surface} schema enum violation {field}: {row.get('company_id')}")
            continue
        if "type" in definition and not type_valid(value, definition["type"]):
            errors.append(f"{surface} schema type violation {field}: {row.get('company_id')}")
            continue
        if isinstance(value, str) and "minLength" in definition and len(value) < definition["minLength"]:
            errors.append(f"{surface} schema minLength violation {field}: {row.get('company_id')}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in definition and value < definition["minimum"]:
                errors.append(f"{surface} schema minimum violation {field}: {row.get('company_id')}")
            if "maximum" in definition and value > definition["maximum"]:
                errors.append(f"{surface} schema maximum violation {field}: {row.get('company_id')}")
        if "format" in definition and value is not None and not format_valid(value, definition["format"]):
            errors.append(f"{surface} schema format violation {field}: {row.get('company_id')}")
        if definition.get("type") == "array" and isinstance(value, list):
            item_definition = definition.get("items", {})
            for item in value:
                if not type_valid(item, item_definition.get("type", "string")) or (item_definition.get("format") and not format_valid(item, item_definition["format"])):
                    errors.append(f"{surface} schema array item violation {field}: {row.get('company_id')}")
                    break
    for clause in schema.get("allOf", []):
        condition = clause.get("if", {}) if isinstance(clause, dict) else {}
        condition_properties = condition.get("properties", {}) if isinstance(condition, dict) else {}
        if not condition_properties or not all(field in normalized for field in condition_properties):
            continue
        matches = True
        for field, rule in condition_properties.items():
            value = normalized.get(field)
            if "type" in rule and not type_valid(value, rule["type"]):
                matches = False
            if "const" in rule and value != rule["const"]:
                matches = False
            if "not" in rule and isinstance(rule["not"], dict) and "const" in rule["not"] and value == rule["not"]["const"]:
                matches = False
        if matches:
            for field in clause.get("then", {}).get("required", []):
                if normalized.get(field) in (None, ""):
                    errors.append(f"{surface} conditional required field {field}: {row.get('company_id')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--website-evidence", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()
    wb = load_workbook(args.workbook, read_only=True, data_only=False)
    companies = rows(wb["01_All_Leads"])
    qualification = rows(wb["02_Qualification"])
    priority = rows(wb["03_Priority_Leads"])
    contacts = rows(wb["04_Contacts"])
    wb.close()
    errors: list[str] = []
    manifest_data: dict[str, object] | None = None
    if args.run_manifest and not args.run_manifest.exists():
        errors.append("run manifest missing")
    elif args.run_manifest:
        try:
            manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
            manifest_data = manifest
            expected = manifest.get("outputs", {}).get("workbook", {}).get("sha256")
            if expected != file_sha256(args.workbook):
                errors.append("workbook hash does not match run manifest")
            if not manifest.get("run_id") or not manifest.get("generated_at") or not manifest.get("config_version"):
                errors.append("run manifest lacks run identity or configuration version")
            for key in ("workbook", "build_report"):
                if key not in manifest.get("outputs", {}):
                    errors.append(f"run manifest missing {key} output")
            for key in ("companies", "scores", "priority", "contacts", "sources"):
                if key not in manifest.get("inputs", {}):
                    errors.append(f"run manifest missing {key} input")
            for key in ("schema", "website_evidence", "source_register", "entity_resolution", "buying_signal_audit", "buying_events", "scoring_audit", "contact_sources"):
                if key not in manifest.get("supporting_inputs", {}):
                    errors.append(f"run manifest missing {key} supporting input")
            verify_manifest_bucket(errors, args.run_manifest, "outputs", manifest.get("outputs", {}))
            verify_manifest_bucket(errors, args.run_manifest, "inputs", manifest.get("inputs", {}))
            verify_manifest_bucket(errors, args.run_manifest, "supporting_inputs", manifest.get("supporting_inputs", {}))
        except (OSError, ValueError, KeyError):
            errors.append("run manifest is unreadable")
    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        properties = schema.get("properties", {})
        required = schema.get("required", [])
    except (OSError, ValueError):
        properties = {}
        required = []
        errors.append("schema is unreadable")
    if not args.evidence_dir.is_dir():
        errors.append("evidence directory is missing")
    evidence_root = args.evidence_dir.parent
    website_evidence_path = None
    manifest_website_evidence_path = None
    if isinstance(manifest_data, dict) and args.run_manifest:
        supporting = manifest_data.get("supporting_inputs", {})
        record = supporting.get("website_evidence") if isinstance(supporting, dict) else None
        raw_path = record.get("path") if isinstance(record, dict) else None
        if isinstance(raw_path, str) and raw_path:
            manifest_website_evidence_path = resolve_manifest_path(args.run_manifest, raw_path)
            if args.website_evidence is not None and args.website_evidence.resolve() != manifest_website_evidence_path:
                errors.append("website evidence override does not match run manifest binding")
            website_evidence_path = manifest_website_evidence_path
    if website_evidence_path is None:
        website_evidence_path = args.website_evidence
    if website_evidence_path is None:
        website_evidence_path = evidence_root / ".missing-website-evidence"
    website_claims: dict[str, dict[str, dict[str, object]]] = {}
    if website_evidence_path.exists():
        for line in website_evidence_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                errors.append("website evidence contains invalid JSON")
                continue
            website_claims[record.get("company_id", "")] = {str(claim.get("field")): claim for claim in record.get("claims", []) if isinstance(claim, dict)}
    else:
        errors.append("website evidence artifact is missing")
    company_ids = [row.get("company_id") for row in qualification]
    manifest_scope = set()
    delivery_policy = "strict"
    if isinstance(manifest_data, dict):
        manifest_scope = {str(value) for value in manifest_data.get("accepted_company_ids", []) if str(value)}
        delivery_policy = str(manifest_data.get("delivery_policy") or "strict")
    duplicates = [item for item, count in Counter(company_ids).items() if item and count > 1]
    if duplicates:
        errors.append(f"duplicate company IDs: {duplicates[:5]}")
    for row in companies:
        append_schema_errors(errors, row, schema, SURFACE_REQUIRED["companies"], "companies")
    for row in qualification:
        append_schema_errors(errors, row, schema, SURFACE_REQUIRED["qualification"], "qualification")
    for row in priority:
        append_schema_errors(errors, row, schema, SURFACE_REQUIRED["priority"], "priority")
    for row in contacts:
        append_schema_errors(errors, row, schema, SURFACE_REQUIRED["contacts"], "contacts")
    company_by_id = {row.get("company_id"): row for row in companies}
    for row in qualification:
        company = company_by_id.get(row.get("company_id"), {})
        if company.get("resolution_status") != "Accepted":
            errors.append(f"qualification includes unresolved company: {row.get('company_id')}")
        if not is_plausible_company_name(company.get("company_name")):
            errors.append(f"accepted company identity is not plausible: {row.get('company_id')}")
        fit = row.get("structural_lead_fit")
        fit_value = numeric(fit)
        if fit not in (None, "", "Unknown") and fit_value is None:
            errors.append(f"score is not numeric: {row.get('company_id')}")
        if fit_value is not None and not 0 <= fit_value <= 100:
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
        expected_fit, expected_coverage = calculate_fit(row)
        if numeric(row.get("evidence_coverage")) != expected_coverage:
            errors.append(f"evidence coverage mismatch: {row.get('company_id')}")
        if expected_fit is None and fit_value is not None or expected_fit is not None and (fit_value is None or abs(fit_value - expected_fit) > 0.01):
            errors.append(f"structural score mismatch: {row.get('company_id')}")
        expected_tier = "Research" if expected_fit is None or expected_coverage < 50 or row.get("berlin_relevance") != "Confirmed" else "A" if expected_fit >= 70 and expected_coverage >= 75 else "B" if expected_fit >= 55 else "C"
        if row.get("lead_tier") != expected_tier:
            errors.append(f"lead tier mismatch: {row.get('company_id')}")
        for field in ("service_fit", "residential_weg", "berlin_relevance"):
            if row.get(field) not in (None, "", "Unknown"):
                urls = parse_evidence_urls(row.get("evidence_urls"))
                if not urls or not all(valid_http_url(url) for url in urls):
                    errors.append(f"{field} claim lacks valid evidence URL: {row.get('company_id')}")
                claim = website_claims.get(row.get("company_id", ""), {}).get(field)
                if not claim or not valid_http_url(claim.get("evidence_url")) or not claim.get("evidence_excerpt") or claim.get("confidence") in (None, "", "None"):
                    errors.append(f"{field} claim lacks page-local evidence: {row.get('company_id')}")
                if field == "berlin_relevance" and claim and not re.search(r"\bberlin\b", str(claim.get("evidence_excerpt") or ""), re.I):
                    errors.append(f"Berlin claim excerpt does not prove Berlin: {row.get('company_id')}")
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
        if row.get("contact_email") not in (None, "", "Unknown"):
            if is_placeholder_email(row.get("contact_email")):
                errors.append(f"placeholder contact email: {row.get('company_id')}")
            email_host = urlparse(str(row.get("email_source") or "")).hostname or ""
            if row.get("verification_status") == "Verified" and not is_valid_business_email(row.get("contact_email"), email_host):
                errors.append(f"verified contact email is not company-domain bound: {row.get('company_id')}")
            if row.get("verification_status") == "Verified" and row.get("contact_name") in (None, "", "Unknown"):
                errors.append(f"verified contact lacks named owner: {row.get('company_id')}")
    qualification_ids = {row.get("company_id") for row in qualification}
    priority_ids = [row.get("company_id") for row in priority]
    if any(company_id not in qualification_ids for company_id in priority_ids):
        errors.append("priority contains company IDs absent from qualification")
    if len(priority_ids) != len(set(priority_ids)):
        errors.append("priority contains duplicate company IDs")
    if manifest_scope:
        if not set(priority_ids).issubset(manifest_scope):
            errors.append("priority contains company IDs outside the admitted manifest scope")
        if delivery_policy == "strict" and set(priority_ids) != manifest_scope:
            errors.append("strict priority scope does not exactly match the admitted manifest scope")
    domains = [str(row.get("domain") or "").lower() for row in qualification if row.get("domain") not in (None, "", "Unknown")]
    duplicate_domains = [item for item, count in Counter(domains).items() if count > 1]
    if duplicate_domains:
        errors.append(f"duplicate accepted domains: {duplicate_domains[:5]}")
    for row in priority:
        if delivery_policy == "strict" and row.get("berlin_relevance") != "Confirmed":
            errors.append(f"priority row lacks confirmed Berlin eligibility: {row.get('company_id')}")
    sample = priority[:10] + [row for row in qualification if row not in priority][:1]
    args.sample_output.parent.mkdir(parents=True, exist_ok=True)
    with args.sample_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(dict.fromkeys(key for row in sample for key in row)) if sample else ["company_id"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
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
    if args.run_manifest and args.run_manifest.exists():
        update_run_manifest(args.run_manifest, supporting_inputs={"schema": args.schema, "website_evidence": website_evidence_path}, outputs={"qa_report": args.report, "qa_sample": args.sample_output})
    print("qa_errors=%d" % len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
