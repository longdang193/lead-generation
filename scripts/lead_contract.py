from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


BUYING_SIGNALS = ("Strong", "Medium", "Weak", "None found", "Unknown")
SEARCH_STATUSES = ("Searched", "Not searched", "Unavailable", "Unknown")
ACTIONABILITY = ("Ready", "Research", "Monitor", "Unknown")
SALES_PRIORITIES = ("Pursue", "Research", "Defer")


def is_unknown(value: object) -> bool:
    return value in (None, "", "Unknown")


def parse_evidence_urls(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    return [item.strip() for item in re.split(r"\s*[|,]\s*", str(value)) if item.strip()]


def is_generic_mailbox(value: object) -> bool:
    if not value or "@" not in str(value):
        return False
    local = str(value).split("@", 1)[0].lower()
    return local in {"info", "kontakt", "contact", "office", "hello", "support", "service", "mail", "verwaltung", "buchhaltung"}


def is_plausible_full_name(value: object) -> bool:
    words = re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'’-]+", str(value or ""))
    return len(words) >= 2 and all(len(word) >= 2 for word in words[:2]) and not any(
        token in str(value).lower() for token in ("haben", "unseren", "immobilienfonds", "cookie", "kontakt")
    )


def signal_rank(value: object) -> int:
    return {"Strong": 4, "Medium": 3, "Weak": 2, "None found": 1, "Unknown": 0}.get(str(value), 0)


def priority_rank(value: object) -> int:
    return {"Pursue": 0, "Research": 1, "Defer": 2}.get(str(value), 3)


def tier_rank(value: object) -> int:
    return {"A": 0, "B": 1, "C": 2, "Research": 3}.get(str(value), 4)


def actionability_for(tier: str, coverage: float | None, signal: str) -> str:
    if coverage is None or tier not in {"A", "B"} or coverage < 50:
        return "Unknown"
    if tier == "A" and coverage >= 75 and signal in {"Strong", "Medium"}:
        return "Ready"
    if signal == "Unknown":
        return "Research"
    if signal in {"Weak", "None found"}:
        return "Monitor"
    return "Research"


def sales_priority_for(actionability: str, tier: str) -> str:
    if actionability == "Ready":
        return "Pursue"
    if actionability in {"Research", "Monitor"} and tier in {"A", "B"}:
        return "Research"
    return "Defer"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_public_http_url(value: object) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
