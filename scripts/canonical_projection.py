from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from account_intelligence import account_signal_state
from campaign_spec import qualification_eligibility
from lead_contract import run_scope_matches
from run_manifest import load as load_manifest, portable_path, update as update_manifest
from typed_contracts import CoverageManifest


ASSURANCE_ORDER = {"unknown": 0, "replay": 1, "structural": 2, "source": 3}
SCORE_FIELDS = {"service_fit", "residential_weg", "berlin_relevance", "management_type", "portfolio_size"}


def load_records(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return []
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        return value if isinstance(value, list) else [value]
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, object]], fallback: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else fallback
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _coverage_manifest_from_research_run(research_run: dict[str, object], company_id: str) -> CoverageManifest | None:
    raw = research_run.get("coverage_manifest")
    source = raw if isinstance(raw, dict) else research_run
    required_checks = source.get("required_checks")
    offer_id = str(source.get("offer_id") or research_run.get("offer_id") or "")
    offer_version = str(source.get("offer_version") or research_run.get("offer_version") or "")
    if not isinstance(required_checks, list) or not required_checks or not offer_id or not offer_version:
        return None
    completed_checks = source.get("completed_checks") if isinstance(source.get("completed_checks"), list) else []
    provider_states = source.get("provider_states") if isinstance(source.get("provider_states"), dict) else {}
    if not provider_states:
        provider_status = str(research_run.get("provider_status") or "").lower()
        fallback_state = "available" if provider_status == "available" else "unavailable" if provider_status == "unavailable" else "unknown"
        provider_states = {str(check): fallback_state for check in required_checks}
    normalized_states = {
        str(check): {"Available": "available", "Unavailable": "unavailable", "Invalid": "invalid", "Unknown": "unknown"}.get(str(state), str(state).lower())
        for check, state in provider_states.items()
    }
    coverage_status = str(source.get("coverage_status") or "unknown")
    permits_no_trigger = (
        set(str(check) for check in completed_checks) == set(str(check) for check in required_checks)
        and not bool(source.get("truncated", False))
        and int(source.get("unresolved_candidates", 0) or 0) == 0
        and set(normalized_states) >= set(str(check) for check in required_checks)
        and all(normalized_states.get(str(check)) == "available" for check in required_checks)
    )
    return CoverageManifest(
        company_id=company_id,
        offer_id=offer_id,
        offer_version=offer_version,
        required_checks=[str(check) for check in required_checks],
        completed_checks=[str(check) for check in completed_checks],
        provider_states=normalized_states,
        truncated=bool(source.get("truncated", False)),
        unresolved_candidates=int(source.get("unresolved_candidates", 0) or 0),
        trigger_state="No trigger found" if coverage_status == "complete" and permits_no_trigger else "Research incomplete",
    )


def _claim_value(claim: dict[str, object]) -> object:
    value = claim.get("claim_value")
    if isinstance(value, dict):
        return value.get("value", value.get("name", value))
    return value


def project_verified_evidence(
    promoted_path: Path,
    base_qualification_path: Path,
    base_scores_path: Path,
    base_contacts_path: Path,
    output_dir: Path,
    *,
    run_id: str,
    manifest_path: Path | None = None,
    root: Path | None = None,
    delivery_policy: str = "strict",
) -> dict[str, Path]:
    claims = sorted(load_records(promoted_path), key=lambda row: str(row.get("candidate_claim_id") or ""))
    by_company: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        if claim.get("candidate_status") not in {"Verified", "Supported"}:
            raise ValueError("canonical projection accepts only Verified or Supported claims")
        if not run_scope_matches(claim.get("verifier_run_id"), run_id):
            raise ValueError(f"claim is outside active run: {claim.get('candidate_claim_id')}")
        company_id = str(claim.get("company_id") or "")
        claim_type = str(claim.get("claim_type") or "")
        value = _claim_value(claim)
        if claim_type == "event" and isinstance(value, dict):
            stable_value = value.get("event_id") or claim.get("candidate_claim_id")
        elif claim_type == "contact":
            stable_value = (claim.get("person_name"), claim.get("email"), claim.get("source_url"))
        else:
            stable_value = claim.get("candidate_claim_id")
        key = (company_id, claim_type, json.dumps(stable_value, ensure_ascii=False, sort_keys=True, default=str))
        if not company_id or not claim_type:
            raise ValueError("verified claim lacks company_id or claim_type")
        if key in seen:
            raise ValueError(f"duplicate canonical claim: {key[0]}:{key[1]}")
        seen.add(key)
        by_company[company_id].append(claim)

    qualification = load_records(base_qualification_path)
    qualification = sorted(qualification, key=lambda row: str(row.get("company_id") or ""))
    for row in qualification:
        company_id = str(row.get("company_id") or "")
        row_claims = by_company.get(company_id, [])
        field_assurance = row.get("field_assurance") if isinstance(row.get("field_assurance"), dict) else {}
        field_assurance = {str(key): str(value) for key, value in field_assurance.items()}
        urls = [str(row.get("evidence_urls") or "")] if row.get("evidence_urls") else []
        for claim in row_claims:
            claim_type = str(claim["claim_type"])
            value = _claim_value(claim)
            assurance = str(claim.get("assurance_level") or "unknown")
            if claim_type in SCORE_FIELDS:
                current = field_assurance.get(claim_type, "unknown")
                if ASSURANCE_ORDER.get(assurance, 0) >= ASSURANCE_ORDER.get(current, 0):
                    row[claim_type] = value
                    if assurance != "replay":
                        field_assurance[claim_type] = assurance
            if claim.get("source_url"):
                urls.append(str(claim["source_url"]))
        if field_assurance:
            row["field_assurance"] = field_assurance
        if urls:
            row["evidence_urls"] = " | ".join(sorted(set(url for url in urls if url)))
        row["eligible"] = qualification_eligibility(row, delivery_policy, recompute=True)
        row["projection_run_id"] = run_id

    scores = sorted(load_records(base_scores_path), key=lambda row: str(row.get("company_id") or ""))
    events: list[dict[str, object]] = []
    event_links: list[dict[str, object]] = []
    signal_audit: list[dict[str, object]] = []
    research_registry: dict[str, object] = {}
    if manifest_path:
        manifest = load_manifest(manifest_path)
        raw_registry = manifest.get("research_runs", {})
        if isinstance(raw_registry, dict):
            research_registry = raw_registry

    assurance_order = {"unknown": 0, "replay": 1, "structural": 2, "source": 3}
    for row in qualification:
        company_id = str(row.get("company_id") or "")
        row_claims = by_company.get(company_id, [])
        company_runs = [value for value in research_registry.values() if isinstance(value, dict) and str(value.get("company_id") or "") == company_id]
        levels = [str(claim.get("assurance_level") or "unknown") for claim in row_claims]
        row["assurance_level"] = max(levels or ["unknown"], key=lambda value: assurance_order.get(value, 0))
        provider_states = {str(value.get("provider_status") or "Unknown") for value in company_runs}
        row["provider_status"] = "Unavailable" if "Unavailable" in provider_states else "Available" if company_runs and provider_states == {"Available"} else "Unknown"
        gaps: list[str] = []
        if not any(claim.get("claim_type") == "contact" for claim in row_claims):
            gaps.append("contact")
        signal_run = next((value for value in company_runs if str(value.get("research_type") or "") == "signals"), {})
        if not any(claim.get("claim_type") == "buying_signal" for claim in row_claims) and str(signal_run.get("status") or "") != "Completed":
            gaps.append("buying_signal")
        row["research_gap"] = "; ".join(gaps) if gaps else "None"

    def signal_research_run(company_id: str) -> dict[str, object]:
        for value in research_registry.values():
            if not isinstance(value, dict):
                continue
            if str(value.get("company_id") or "") == company_id and str(value.get("research_type") or "") == "signals":
                return value
        return {}

    for row in scores:
        company_id = str(row.get("company_id") or "")
        row_claims = by_company.get(company_id, [])
        signal_claims = [claim for claim in row_claims if claim.get("claim_type") in {"buying_signal", "event"}]
        research_run = signal_research_run(company_id)
        for claim in signal_claims:
            value = _claim_value(claim)
            if claim.get("claim_type") == "buying_signal":
                row["buying_signal"] = value
            if claim.get("claim_type") == "event":
                event = value if isinstance(value, dict) else {}
                event_id = event.get("event_id", claim.get("candidate_claim_id"))
                events.append({
                    "event_id": event_id,
                    "company_id": company_id,
                    "event_type": event.get("event_type") or event.get("type") or "Unknown",
                    "buyer": event.get("buyer") or "Unknown",
                    "title": event.get("title") or claim.get("evidence_excerpt") or "Unknown",
                    "publication_date": event.get("publication_date") or claim.get("published_at"),
                    "deadline": event.get("deadline"),
                    "source_url": claim.get("source_url", ""),
                    "assurance_level": str(claim.get("assurance_level") or "unknown"),
                    "verification_status": "Verified" if str(claim.get("assurance_level") or "") == "source" else "Supported" if str(claim.get("assurance_level") or "") == "structural" else "Unknown",
                })
                event_links.append({"event_id": event_id, "company_id": company_id, "match_confidence": {"source": "Verified", "structural": "Supported", "replay": "Replay", "unknown": "Unknown"}.get(str(claim.get("assurance_level") or "unknown"), "Unknown")})
        if signal_claims:
            row["buying_signal_evidence_urls"] = " | ".join(sorted({str(claim.get("source_url")) for claim in signal_claims if claim.get("source_url")}))
        signal_claim = next((claim for claim in signal_claims if claim.get("claim_type") == "buying_signal" and str(claim.get("assurance_level") or "") == "source"), None)
        source_event_claim = next((claim for claim in signal_claims if claim.get("claim_type") == "event" and str(claim.get("assurance_level") or "") == "source"), None)
        research_status = str(research_run.get("status") or "Needs review")
        coverage_manifest = _coverage_manifest_from_research_run(research_run, company_id)
        if signal_claim and source_event_claim:
            signal_value = str(_claim_value(signal_claim))
        elif coverage_manifest is not None:
            signal_value = account_signal_state([], coverage_manifest)
            if signal_value == "No trigger found":
                research_status = "Completed"
            elif signal_value == "Unavailable":
                research_status = "Unavailable"
            else:
                research_status = "Partial"
        else:
            signal_value = "Unknown" if research_status == "Unavailable" else "Research incomplete"
            if research_status not in {"Not searched", "Completed", "Partial", "Unavailable", "Needs review"}:
                research_status = "Needs review"
        search_status = {
            "Completed": "Searched",
            "Unavailable": "Unavailable",
            "Not searched": "Not searched",
            "Partial": "Unknown",
            "Needs review": "Unknown",
        }.get(research_status, "Unknown")
        if research_status == "Completed" and str(research_run.get("adapter_capability") or "") != "live_research":
            search_status = "Unknown"
        signal_audit.append({"company_id": company_id, "research_status": research_status, "signal_state": signal_value, "search_status": search_status, "coverage_status": "complete" if signal_value == "No trigger found" else "unavailable" if signal_value == "Unavailable" else "partial", "verified_claim_count": len(signal_claims), "run_id": run_id})
        row["buying_signal"] = signal_value
        row["projection_run_id"] = run_id

    contacts = sorted(load_records(base_contacts_path), key=lambda row: str(row.get("company_id") or ""))
    projected_contacts: list[dict[str, object]] = []
    rows_by_company: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in contacts:
        rows_by_company[str(row.get("company_id") or "")].append(row)
    contact_company_ids = sorted(set(rows_by_company) | {str(claim.get("company_id") or "") for claims_for_company in by_company.values() for claim in claims_for_company if claim.get("claim_type") == "contact"})
    for company_id in contact_company_ids:
        base_rows = rows_by_company.get(company_id, [{"company_id": company_id}])
        row = base_rows[0]
        contact_claims = [claim for claim in by_company.get(company_id, []) if claim.get("claim_type") == "contact"]
        if contact_claims:
            for claim in contact_claims:
                projected = dict(row)
                projected["contact_name"] = claim.get("person_name") or "Unknown"
                projected["contact_role"] = claim.get("role") or "Unknown"
                projected["contact_email"] = claim.get("email") or "Unknown"
                projected["email_source"] = claim.get("source_url") or "Unknown"
                assurance_level = str(claim.get("assurance_level") or "unknown")
                projected["verification_status"] = "Verified" if assurance_level == "source" else "Unverified" if assurance_level == "structural" else "Unknown"
                projected["assurance_level"] = assurance_level
                verified_at = str(claim.get("verified_at") or "Unknown")
                projected["last_verified"] = verified_at[:10] if verified_at not in ("", "Unknown") else verified_at
                projected["projection_run_id"] = run_id
                projected_contacts.append(projected)
        else:
            projected_contacts.extend(dict(base_row) for base_row in base_rows)
    contacts = projected_contacts
    contact_fields = ["company_id", "contact_name", "contact_role", "contact_email", "email_source", "verification_status", "assurance_level", "last_verified", "projection_run_id"]
    for contact in contacts:
        for field in contact_fields:
            contact.setdefault(field, "unknown" if field == "assurance_level" else "Unknown")

    outputs = {
        "qualification": output_dir / "qualification.jsonl",
        "scores": output_dir / "scores.csv",
        "contacts": output_dir / "contacts.csv",
        "events": output_dir / "events.json",
        "event_links": output_dir / "event_links.csv",
        "signal_audit": output_dir / "signal_audit.csv",
    }
    _write_jsonl(outputs["qualification"], qualification)
    _write_csv(outputs["scores"], scores, ["company_id", "buying_signal"])
    _write_csv(outputs["contacts"], contacts, contact_fields)
    outputs["events"].parent.mkdir(parents=True, exist_ok=True)
    outputs["events"].write_text(json.dumps(sorted(events, key=lambda row: (str(row["company_id"]), str(row["event_id"]))), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(outputs["event_links"], sorted(event_links, key=lambda row: (str(row["company_id"]), str(row["event_id"]))), ["event_id", "company_id", "match_confidence"])
    _write_csv(outputs["signal_audit"], signal_audit, ["company_id", "research_status", "signal_state", "search_status", "verified_claim_count", "run_id"])
    if manifest_path and root:
        update_manifest(manifest_path, root, outputs=outputs, registries={"projection": {"outputs": {name: {"path": portable_path(root, path), "format": path.suffix} for name, path in outputs.items()}, "run_id": run_id}}, barriers={"projection": True})
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promoted", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()
    outputs = project_verified_evidence(args.promoted, args.qualification, args.scores, args.contacts, args.output_dir, run_id=args.run_id, manifest_path=args.run_manifest, root=Path.cwd())
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
