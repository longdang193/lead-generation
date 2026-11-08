from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from runtime_config import RuntimeConfig
from provider_clients import ProviderError, hunter_domain_search


def fetch_contacts(url: str, config: RuntimeConfig) -> tuple[str, str, str]:
    if not url:
        return "", "", ""
    try:
        response = requests.get(url, timeout=config.request_timeout_seconds, headers={"User-Agent": "Mozilla/5.0 (compatible; lead-research/1.0)"})
        if not response.ok:
            return "", "", ""
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        emails = re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", response.text, flags=re.I)
        email = next((item for item in emails if not item.lower().endswith(("example.com", "example.org"))), "")
        role_match = re.search(r"([A-ZÄÖÜ][\wÄÖÜäöüß.-]+\s+[A-ZÄÖÜ][\wÄÖÜäöüß.-]+).{0,80}(Geschäftsführer|Inhaber|Leitung|Geschäftsleitung)", text, flags=re.I)
        if not role_match:
            role_match = re.search(r"(Geschäftsführer|Inhaber|Leitung|Geschäftsleitung).{0,80}([A-ZÄÖÜ][\wÄÖÜäöüß.-]+\s+[A-ZÄÖÜ][\wÄÖÜäöüß.-]+)", text, flags=re.I)
        person = (role_match.group(1) if role_match and "Geschäft" not in role_match.group(1) and "Leitung" not in role_match.group(1) else role_match.group(2)) if role_match else ""
        return person, email, response.url
    except requests.RequestException:
        return "", "", ""


def fetch_hunter_contact(domain: str, config: RuntimeConfig) -> tuple[str, str, str, str]:
    if not config.hunter_api_key or not domain:
        return "", "", "", ""
    try:
        data = hunter_domain_search(domain, config.hunter_api_key, timeout=config.request_timeout_seconds)
    except ProviderError:
        return "", "", "", ""
    emails = data.get("emails") if isinstance(data, dict) else []
    if not isinstance(emails, list):
        return "", "", "", ""
    candidates = [item for item in emails if item.get("value")]
    candidates.sort(key=lambda item: float(item.get("confidence") or 0), reverse=True)
    if not candidates:
        return "", "", "", ""
    item = candidates[0]
    verification = item.get("verification") if isinstance(item.get("verification"), dict) else {}
    status = str(verification.get("status") or "Unverified")
    email_status = "Verified" if status.lower() in {"valid", "accept_all"} else "Unverified"
    sources = item.get("sources") if isinstance(item.get("sources"), list) else []
    source_url = sources[0].get("uri") if sources and isinstance(sources[0], dict) else ""
    return str(item.get("first_name") or ""), str(item.get("value")), source_url, email_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--priority-output", type=Path, required=True)
    parser.add_argument("--contacts-output", type=Path, required=True)
    parser.add_argument("--evidence-output", type=Path, required=True)
    parser.add_argument("--max-priority-accounts", type=int, default=30)
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    with args.scores.open(encoding="utf-8-sig", newline="") as handle:
        scores = list(csv.DictReader(handle))
    def sort_key(row: dict[str, str]) -> tuple[int, float, float]:
        priority = 0 if row.get("sales_priority") == "Pursue" else 1
        fit = float(row["structural_lead_fit"]) if row.get("structural_lead_fit") not in (None, "", "Unknown") else -1
        coverage = float(row["evidence_coverage"]) if row.get("evidence_coverage") not in (None, "", "Unknown") else -1
        return priority, -fit, -coverage
    shortlist = sorted(scores, key=sort_key)[: args.max_priority_accounts]
    priority_rows = []
    contacts = []
    evidence = []
    for row in shortlist:
        person, email, evidence_url = fetch_contacts(row.get("source_url", ""), config)
        email_status = "Published" if email else "Not found"
        hunter_person, hunter_email, hunter_source, hunter_status = fetch_hunter_contact(row.get("domain", ""), config)
        if hunter_email and (not email or hunter_status == "Verified"):
            person = hunter_person or person
            email = hunter_email
            evidence_url = hunter_source or evidence_url or row.get("source_url", "")
            email_status = hunter_status
        priority_rows.append({**row, "priority_reason": "Highest structural fit and evidence coverage available", "key_evidence": row.get("evidence_urls", ""), "research_gap": "Named contact and buying signal unavailable" if not email else "Buying signal unavailable", "next_action": "Review official contact page and validate outreach owner"})
        contacts.append({"company_id": row.get("company_id", ""), "company_name": row.get("company_name", ""), "contact_name": person or "Unknown", "contact_role": "Unknown" if not person else "Publicly named management/contact", "relevance": "Shortlisted account", "contact_email": email or "Unknown", "email_source": evidence_url or row.get("source_url", ""), "verification_status": email_status, "linkedin_url": "Unknown", "last_verified": str(date.today()) if email else "Unknown"})
        evidence.append({"company_id": row.get("company_id", ""), "contact_name": person or "Unknown", "email": email or "Unknown", "source_url": evidence_url or row.get("source_url", ""), "verification_status": email_status, "last_verified": str(date.today()) if email else "Unknown"})
    for path, rows, fallback in [(args.priority_output, priority_rows, ["company_id", "lead_tier"]), (args.contacts_output, contacts, ["company_id", "contact_email"]), (args.evidence_output, evidence, ["company_id", "source_url"])]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            fields = list(rows[0]) if rows else fallback
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(f"priority={len(priority_rows)} contacts={len(contacts)} published_emails={sum(row['contact_email'] != 'Unknown' for row in contacts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
