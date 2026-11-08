from __future__ import annotations

import argparse
import csv
from collections import Counter
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from runtime_config import RuntimeConfig
from lead_contract import contact_claim_valid, is_generic_mailbox, is_plausible_full_name, is_valid_business_email, priority_rank, signal_rank, tier_rank
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
        company_host = (urlparse(response.url).hostname or "").lower().removeprefix("www.")
        email = next((item for item in emails if is_valid_business_email(item, company_host)), "")
        role_match = re.search(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß'’-]+(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß'’-]+){1,2})\s*[,|-]\s*(Geschäftsführer(?:in)?|Inhaber(?:in)?|Leitung|Geschäftsleitung)\b", text)
        if not role_match:
            role_match = re.search(r"\b(Geschäftsführer(?:in)?|Inhaber(?:in)?|Leitung|Geschäftsleitung)\s*[:,-]\s*([A-ZÄÖÜ][\wÄÖÜäöüß'’-]+(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß'’-]+){1,2})\b", text)
        if not role_match:
            return "", email, response.url
        person = role_match.group(1) if role_match.lastindex == 2 and is_plausible_full_name(role_match.group(1)) else role_match.group(2)
        role = role_match.group(2) if role_match.lastindex == 2 and is_plausible_full_name(role_match.group(1)) else role_match.group(1)
        return person if is_plausible_full_name(person) else "", email, response.url
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
    email_status = "Verified" if status.lower() == "valid" else "Unverified"
    sources = item.get("sources") if isinstance(item.get("sources"), list) else []
    source_url = sources[0].get("uri") if sources and isinstance(sources[0], dict) else ""
    full_name = " ".join(part for part in (str(item.get("first_name") or ""), str(item.get("last_name") or "")) if part).strip()
    if not is_plausible_full_name(full_name) or not is_valid_business_email(item.get("value"), domain):
        return "", "", "", ""
    return full_name, str(item.get("value")), source_url, email_status


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
    def sort_key(row: dict[str, str]) -> tuple[int, int, float, float, float, int, str]:
        fit = float(row["structural_lead_fit"]) if row.get("structural_lead_fit") not in (None, "", "Unknown") else -1
        coverage = float(row["evidence_coverage"]) if row.get("evidence_coverage") not in (None, "", "Unknown") else -1
        portfolio = float(row["portfolio_potential"]) if row.get("portfolio_potential") not in (None, "", "Unknown") else -1
        return priority_rank(row.get("sales_priority")), tier_rank(row.get("lead_tier")), -coverage, -fit, -portfolio, -signal_rank(row.get("buying_signal")), row.get("company_id", "")
    shortlist = sorted(scores, key=sort_key)[: args.max_priority_accounts]
    priority_rows = []
    contacts = []
    evidence = []
    for row in shortlist:
        person, email, evidence_url = fetch_contacts(row.get("source_url", ""), config)
        role_evidence = "Official role evidence" if person else ""
        if not is_plausible_full_name(person):
            person = ""
        if email and not is_valid_business_email(email, row.get("domain", "")):
            email = ""
        email_status = "Published" if email else "Not found"
        hunter_person, hunter_email, hunter_source, hunter_status = fetch_hunter_contact(row.get("domain", ""), config)
        if hunter_email and not email:
            email = hunter_email
            evidence_url = hunter_source or evidence_url or row.get("source_url", "")
            email_status = "Unverified" if not person else hunter_status
        if email and is_generic_mailbox(email) and email_status == "Verified":
            email_status = "Published"
        contact_evidence = {
            "person_name": person,
            "role": role_evidence,
            "company_affiliation": row.get("company_name", ""),
            "source_url": evidence_url,
            "evidence_excerpt": f"{person}, {role_evidence}" if person and role_evidence else "",
            "email": email,
        }
        person_verified = contact_claim_valid(contact_evidence, row.get("domain", ""))[0]
        if not person_verified:
            person = ""
        contact_role = role_evidence if person_verified else ("Published business mailbox" if email and is_generic_mailbox(email) else "Potential contact" if email else "Unknown")
        priority_rows.append({**row, "priority_reason": "Deterministic sales priority, tier, coverage, fit, portfolio, signal, and company-ID order", "key_evidence": row.get("evidence_urls", ""), "research_gap": "Named contact unavailable" if not person else "Personal email unavailable", "next_action": "Review official contact page and validate outreach owner"})
        contacts.append({"company_id": row.get("company_id", ""), "company_name": row.get("company_name", ""), "contact_name": person or "Unknown", "contact_role": contact_role, "relevance": "Shortlisted account", "contact_email": email or "Unknown", "email_source": evidence_url or row.get("source_url", ""), "verification_status": email_status, "person_verified": "Verified" if person_verified else "Unverified", "company_affiliation_verified": "Verified" if person_verified else "Unverified", "role_verified": "Verified" if person_verified else "Unverified", "email_owner_match": "Verified" if person_verified and email and not is_generic_mailbox(email) else "Unverified", "linkedin_url": "Unknown", "last_verified": str(date.today()) if email else "Unknown"})
        evidence.append({"company_id": row.get("company_id", ""), "contact_name": person or "Unknown", "email": email or "Unknown", "source_url": evidence_url or row.get("source_url", ""), "verification_status": email_status, "last_verified": str(date.today()) if email else "Unknown"})
    for path, rows, fallback in [(args.priority_output, priority_rows, ["company_id", "lead_tier"]), (args.contacts_output, contacts, ["company_id", "contact_email"]), (args.evidence_output, evidence, ["company_id", "source_url"])]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            fields = list(rows[0]) if rows else fallback
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    status_counts = Counter(row["verification_status"] for row in contacts if row["contact_email"] != "Unknown")
    print(f"priority={len(priority_rows)} contacts={len(contacts)} email_rows={sum(status_counts.values())} published={status_counts.get('Published', 0)} verified={status_counts.get('Verified', 0)} unverified={status_counts.get('Unverified', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
