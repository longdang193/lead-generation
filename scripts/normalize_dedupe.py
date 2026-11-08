from __future__ import annotations

import argparse
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    import tldextract
except ImportError:
    tldextract = None

try:
    from cleanco import basename
except ImportError:
    basename = None

try:
    from rapidfuzz.fuzz import ratio
except ImportError:
    from difflib import SequenceMatcher
    ratio = lambda a, b: SequenceMatcher(None, a, b).ratio() * 100


LEGAL_SUFFIXES = r"\b(gmbh|ug|ag|kg|ohg|gbr|e\.k\.|e\.v\.|mbh|limited|ltd)\b"


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else "https://" + value)
    host = parsed.hostname or ""
    if tldextract:
        ext = tldextract.extract(host)
        host = ".".join(part for part in [ext.domain, ext.suffix] if part)
    else:
        host = host.lower().removeprefix("www.")
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
    return host.lower()


def clean_name(value: str) -> str:
    value = re.sub(r"[^\w\s-]", " ", (value or "").lower(), flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    if basename:
        try:
            value = basename(value)
        except Exception:
            pass
    value = re.sub(LEGAL_SUFFIXES, " ", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def company_id(name: str, host: str, postcode: str) -> str:
    raw = "|".join([name, host, postcode]).encode("utf-8")
    return "DE-BER-" + hashlib.sha1(raw).hexdigest()[:12]


def is_url_like_name(value: str) -> bool:
    return bool(re.match(r"^(https?://|www\.)", value.strip(), re.I) or re.search(r"\.(de|com|eu|org)(/|$)", value.strip(), re.I))


def explicit_berlin_evidence(row: dict[str, str]) -> str:
    if row.get("city", "").strip().lower() == "berlin":
        return "Confirmed"
    if re.search(r"\bberlin\b", row.get("berlin_evidence", ""), re.I):
        return "Probable"
    return "Unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path, required=True)
    parser.add_argument("--evidence-output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    canonical: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        name = row.get("company_name", "").strip()
        norm = clean_name(name)
        host = domain(row.get("verified_company_domain") or row.get("source_url", ""))
        postcode_text = (row.get("postal_code", "") or "").strip()
        if not postcode_text:
            postcode = re.search(r"\b\d{5}\b", row.get("address", "") or "")
            postcode_text = postcode.group(0) if postcode else ""
        address_key = re.sub(r"\W+", " ", row.get("address", "").lower()).strip()
        key = (norm, postcode_text, address_key)
        requires_review = is_url_like_name(name) or row.get("identity_status") == "Review"
        if requires_review:
            review.append({"raw_source_record_id": row.get("source_record_id", ""), "candidate_company_id": "", "company_name": name, "reason": "identity or location requires fresh official-source resolution", "status": "Manual review"})
        existing = by_key.get(key)
        if existing and norm and (postcode_text or address_key):
            evidence.append({"raw_source_record_id": row.get("source_record_id", ""), "company_id": existing["company_id"], "resolution": "exact identity candidate retained", "reason": "same normalized name and corroborating location", "retrieved_at": stamp()})
            continue
        candidates = [item for item in canonical if postcode_text and item["postal_code"] == postcode_text and ratio(norm, item["normalized_name"]) >= 88]
        if candidates:
            review.append({"raw_source_record_id": row.get("source_record_id", ""), "candidate_company_id": candidates[0]["company_id"], "company_name": name, "reason": "fuzzy name and same postcode", "status": "Manual review"})
        identity_locator = postcode_text or address_key or row.get("city", "")
        if not identity_locator:
            identity_locator = row.get("source_record_id", "")
        cid = company_id(norm, host, identity_locator)
        item = {
            "company_id": cid,
            "company_name": name,
            "legal_name": name,
            "normalized_name": norm,
            "domain": host,
            "discovery_source_url": row.get("discovery_source_url", row.get("source_url", "")),
            "verified_company_domain": host,
            "address": row.get("address", ""),
            "postal_code": postcode_text,
            "city": row.get("city", ""),
            "region": row.get("region", ""),
            "contact": row.get("contact", ""),
            "email": row.get("email", ""),
            "resolution_status": "Review" if requires_review else "Accepted",
            "source_type": row.get("source_type", "Unknown"),
            "source_reuse_status": row.get("source_reuse_status", "Unknown"),
            "extraction_method": row.get("extraction_method", "Unknown"),
            "actor_id": row.get("actor_id", ""),
            "actor_run_id": row.get("actor_run_id", ""),
            "source_record_id": row.get("source_record_id", ""),
            "source_url": row.get("source_url", ""),
            "retrieved_at": row.get("retrieved_at", stamp()),
            "evidence_level": "Primary" if row.get("source_type") == "VDIV" else "Secondary",
            "berlin_relevance": explicit_berlin_evidence(row),
            "management_type": "Unknown",
            "residential_weg": "Unknown",
            "portfolio_size": "",
            "portfolio_size_status": "Unknown",
        }
        canonical.append(item)
        by_key[key] = item
        evidence.append({"raw_source_record_id": row.get("source_record_id", ""), "company_id": cid, "resolution": "new canonical row", "reason": "no safe auto-merge", "retrieved_at": stamp()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path, records in [(args.output, canonical), (args.review_output, review), (args.evidence_output, evidence)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = list(records[0]) if records else ["company_id", "company_name", "status"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    print(f"canonical={len(canonical)} review={len(review)} raw={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
