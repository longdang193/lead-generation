from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from runtime_config import RuntimeConfig
from provider_clients import ProviderError, ted_search


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return str(value[0]) if value else ""
    if isinstance(value, dict):
        for key in ("eng", "deu", "mul"):
            if value.get(key):
                return text_value(value[key])
        for item in value.values():
            if item:
                return text_value(item)
    return ""


def normalize_name(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def account_research_state(*, configured: bool, successful_terms: int, required_terms: int, event_count: int, truncated: bool = False) -> tuple[str, str]:
    if successful_terms == required_terms and configured and not truncated:
        return "Completed", "Candidate" if event_count else "None found"
    if successful_terms == 0 or not configured:
        return "Unavailable", "Unknown"
    return "Partial", "Unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--ted-output", type=Path, required=True)
    parser.add_argument("--links-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--run-id", default="signal-research")
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    with args.companies.open(encoding="utf-8-sig", newline="") as handle:
        companies = list(csv.DictReader(handle))
    events: list[dict[str, object]] = []
    links: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    terms = ["Zählertausch", "Fernablesung", "Heizkostenabrechnung", "Wärmezähler"]
    known: dict[str, list[dict[str, str]]] = {}
    for row in companies:
        key = normalize_name(row.get("company_name", ""))
        if key:
            known.setdefault(key, []).append(row)
    seen: set[str] = set()
    successful_terms = 0
    truncated_search = False
    if config.ted_api_base_url:
        for term in terms:
            try:
                notices = ted_search(config.ted_api_base_url, term, timeout=config.request_timeout_seconds, limit=50)
                if len(notices) >= 50:
                    truncated_search = True
                term_count = 0
                for notice in notices:
                    publication_number = text_value(notice.get("publication-number")) or text_value(notice.get("id"))
                    event_id = f"TED:{publication_number}" if publication_number else f"TED:{term}:{term_count}"
                    if event_id in seen:
                        continue
                    seen.add(event_id)
                    buyer = text_value(notice.get("buyer-name"))
                    title = text_value(notice.get("notice-title"))
                    links_value = notice.get("links") if isinstance(notice.get("links"), dict) else {}
                    html_links = links_value.get("html", {}) if isinstance(links_value, dict) else {}
                    source_url = text_value(html_links.get("deu")) or text_value(html_links.get("eng"))
                    event = {
                        "event_id": event_id,
                        "source_type": "TED",
                        "event_type": term,
                        "buyer": buyer or "Unknown",
                        "title": title or "Unknown",
                        "publication_date": notice.get("publication-date") or "Unknown",
                        "deadline": notice.get("deadline") or "Unknown",
                        "scope": text_value(notice.get("buyer-country")) or "Unknown",
                        "source_url": source_url or "Unknown",
                        "retrieved_at": stamp(),
                    }
                    events.append(event)
                    buyer_key = normalize_name(buyer)
                    matches = known.get(buyer_key, []) if buyer_key else []
                    if len(matches) == 1 and source_url:
                        links.append({"event_id": event_id, "company_id": matches[0]["company_id"], "match_method": "exact normalized buyer name with source URL", "match_confidence": "Verified", "source_url": source_url})
                    elif len(matches) > 1:
                        audit.append({"search_term": term, "search_status": "Searched", "event_count": "0", "reason": f"ambiguous buyer match for {buyer}; retained for review", "retrieved_at": stamp()})
                    term_count += 1
                audit.append({"search_term": term, "search_status": "Searched", "event_count": str(term_count), "reason": "TED search completed; only exact buyer-name links are verified", "retrieved_at": stamp()})
                successful_terms += 1
            except ProviderError as exc:
                audit.append({"search_term": term, "search_status": "Unavailable", "event_count": "0", "reason": str(exc), "retrieved_at": stamp()})
    else:
        audit = [{"search_term": term, "search_status": "Unavailable", "event_count": "0", "reason": "TED_API_BASE_URL not configured", "retrieved_at": stamp()} for term in terms]
    links_by_company: dict[str, list[dict[str, str]]] = {}
    for link in links:
        links_by_company.setdefault(link["company_id"], []).append(link)
    for company in companies:
        company_id = str(company.get("company_id") or "")
        research_status, signal_state = account_research_state(
            configured=bool(config.ted_api_base_url),
            successful_terms=successful_terms,
            required_terms=len(terms),
            event_count=len(links_by_company.get(company_id, [])),
            truncated=truncated_search,
        )
        audit.append({
            "company_id": company_id,
            "research_run_id": args.run_id,
            "research_status": research_status,
            "search_status": "Searched" if research_status == "Completed" else "Unavailable" if research_status == "Unavailable" else "Unknown",
            "signal_state": signal_state,
            "event_count": str(len(links_by_company.get(company_id, []))),
            "reason": "account-scoped exact buyer match" if links_by_company.get(company_id) else "all required searches completed with no verified account match" if research_status == "Completed" else "provider search incomplete or capped; no negative conclusion",
            "retrieved_at": stamp(),
        })
    args.ted_output.parent.mkdir(parents=True, exist_ok=True)
    if not config.ted_api_base_url or successful_terms == 0:
        payload = {"items": [], "status": "Unavailable", "reason": "TED search did not complete successfully"}
    elif successful_terms < len(terms):
        payload = {"items": events, "status": "Partial", "reason": "One or more TED searches were unavailable"}
    else:
        payload = {"items": events, "status": "Searched"}
    args.ted_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.links_output.parent.mkdir(parents=True, exist_ok=True)
    with args.links_output.open("w", encoding="utf-8", newline="") as handle:
        fields = ["event_id", "company_id", "match_method", "match_confidence", "source_url"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(links)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.audit_output.open("w", encoding="utf-8", newline="") as handle:
        fields = ["company_id", "research_run_id", "search_term", "research_status", "search_status", "signal_state", "event_count", "reason", "retrieved_at"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in audit)
    print(json.dumps({"companies": len(companies), "events": len(events), "links": len(links), "ted_configured": bool(config.ted_api_base_url)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
