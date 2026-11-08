from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from lead_contract import candidate_claim_id, candidate_sha256


def load_jsonl(path: Path | None) -> list[dict[str, object]]:
    if path is None or not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_claim(company_id: str, company_name: str, domain: str, run_id: str, claim: dict[str, object]) -> dict[str, object]:
    record = {
        "record_type": "EvidenceClaim",
        "candidate_claim_id": candidate_claim_id({"company_id": company_id, **claim}),
        "company_id": company_id,
        "claim_type": claim["claim_type"],
        "claim_value": claim["claim_value"],
        "unit": claim.get("unit"),
        "scope": claim.get("scope"),
        "source_url": claim["source_url"],
        "source_domain": domain,
        "source_kind": claim.get("source_kind", "official_site"),
        "evidence_excerpt": claim["evidence_excerpt"],
        "retrieved_at": stamp(),
        "published_at": claim.get("published_at"),
        "as_of_date": claim.get("as_of_date"),
        "account_relationship": "direct",
        "confidence": "high",
        "research_run_id": f"{run_id}:{claim.get('lane', '')}:{company_id}".rstrip(":"),
        "candidate_status": "Candidate",
        "person_name": claim.get("person_name"),
        "role": claim.get("role"),
        "company_affiliation": claim.get("company_affiliation") or company_name,
        "email": claim.get("email"),
        "verifier_run_id": None,
        "verified_at": None,
    }
    record["candidate_sha256"] = candidate_sha256(record)
    return record


def run(args: argparse.Namespace) -> int:
    root = args.repo_root.resolve()
    website = {str(row.get("company_id")): row for row in load_jsonl(args.website_evidence) if args.website_evidence}
    contacts = {str(row.get("company_id")): row for row in load_csv(args.contacts_input) if args.contacts_input}
    companies = {str(row.get("company_id")): row for row in load_csv(args.companies_input) if args.companies_input}
    company = companies.get(args.company_id, {})
    domain = str(args.trusted_domain or company.get("domain") or "")
    company_name = str(args.company_name or company.get("company_name") or args.company_id)
    claims: list[dict[str, object]] = []
    source_url = str(company.get("source_url") or f"https://{domain}/")
    if args.lane == "portfolio":
        record = website.get(args.company_id, {})
        for item in record.get("claims", []) if isinstance(record.get("claims"), list) else []:
            if item.get("field") not in {"service_fit", "residential_weg", "berlin_relevance"} or item.get("value") in (None, "Unknown"):
                continue
            claims.append(make_claim(args.company_id, company_name, domain, args.run_id, {"lane": args.lane, "claim_type": item["field"], "claim_value": item["value"], "source_url": item.get("evidence_url") or source_url, "evidence_excerpt": item.get("evidence_excerpt") or "Official company evidence."}))
        if record.get("portfolio_size") not in (None, "", "Unknown"):
            claims.append(make_claim(args.company_id, company_name, domain, args.run_id, {"lane": args.lane, "claim_type": "portfolio_size", "claim_value": record["portfolio_size"], "unit": "units", "scope": "managed residential portfolio", "as_of_date": str(record.get("retrieved_at") or stamp())[:10], "source_url": source_url, "evidence_excerpt": str(record.get("text_excerpt") or "Portfolio size reported on the official company page.")}))
    elif args.lane == "contacts":
        contact = contacts.get(args.company_id, {})
        if contact.get("contact_name") not in (None, "", "Unknown"):
            claims.append(make_claim(args.company_id, company_name, domain, args.run_id, {"lane": args.lane, "claim_type": "contact", "claim_value": contact["contact_name"], "person_name": contact["contact_name"], "role": contact.get("contact_role") or "Unknown", "company_affiliation": company_name, "email": contact.get("contact_email"), "source_url": contact.get("email_source") or source_url, "evidence_excerpt": f"{contact['contact_name']} — {contact.get('contact_role') or 'company contact'}"}))
    elif args.lane == "signals":
        events = json.loads(args.events_input.read_text(encoding="utf-8")) if args.events_input and args.events_input.exists() else []
        links = load_csv(args.event_links_input) if args.event_links_input else []
        event_by_id = {str(item.get("event_id")): item for item in events if isinstance(item, dict)}
        for link in links:
            if link.get("company_id") != args.company_id or link.get("match_confidence") != "Verified":
                continue
            event = event_by_id.get(str(link.get("event_id")), {})
            event_id = str(event.get("event_id") or link.get("event_id"))
            published = str(event.get("publication_date") or event.get("published_at") or "")[:10]
            claims.extend([
                make_claim(args.company_id, company_name, domain, args.run_id, {"lane": args.lane, "claim_type": "buying_signal", "claim_value": "Strong", "source_url": event.get("source_url") or source_url, "evidence_excerpt": str(event.get("title") or "Verified company buying signal."), "published_at": published}),
                make_claim(args.company_id, company_name, domain, args.run_id, {"lane": args.lane, "claim_type": "event", "claim_value": {"event_id": event_id, "publication_date": published, "deadline": event.get("deadline")}, "source_url": event.get("source_url") or source_url, "evidence_excerpt": str(event.get("title") or "Verified company buying signal."), "published_at": published}),
            ])
    research_run = {"record_type": "ResearchRun", "run_id": f"{args.run_id}:{args.lane}:{args.company_id}", "campaign_id": args.campaign_id, "company_id": args.company_id, "company_name": company_name, "trusted_domain": domain, "location": args.location, "research_type": args.lane, "source": args.profile, "scope": f"{args.lane}:{args.company_id}", "status": "Completed", "started_at": stamp(), "completed_at": stamp(), "result_count": len(claims), "truncated": False, "provider_status": "Available", "adapter_capability": "replay", "scope_version": args.scope_version or "native-v1", "scope_hash": args.scope_hash or "0" * 64, "attempts": [{"attempt_id": f"{args.run_id}:{args.lane}:{args.company_id}:1", "query_or_source": source_url, "status": "Completed", "truncated": False}]}
    args.output.write_text(json.dumps({"adapter_capability": "replay", "research_run": research_run, "claims": claims}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--campaign-id", default="legacy")
    parser.add_argument("--lane", required=True)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--company-name", default="")
    parser.add_argument("--trusted-domain", default="")
    parser.add_argument("--location", default="Unknown")
    parser.add_argument("--scope-version", default="")
    parser.add_argument("--scope-hash", default="")
    parser.add_argument("--website-evidence", type=Path)
    parser.add_argument("--contacts-input", type=Path)
    parser.add_argument("--companies-input", type=Path)
    parser.add_argument("--events-input", type=Path)
    parser.add_argument("--event-links-input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
