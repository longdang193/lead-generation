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


def is_placeholder_email(value: object) -> bool:
    if not value or "@" not in str(value):
        return True
    address = str(value).strip().lower()
    local, host = address.split("@", 1)
    return host in {"example.com", "example.org", "example.net", "mail.com", "domain.com", "test.com"} or local in {
        "max.musterman", "max.mustermann", "mustermann", "test", "user", "benutzer", "privacy"
    }


def is_valid_business_email(value: object, company_domain: object = "") -> bool:
    if is_placeholder_email(value):
        return False
    address = str(value).strip().lower()
    host = address.rsplit("@", 1)[-1]
    company_host = str(company_domain or "").lower().removeprefix("www.").strip()
    if not company_host:
        return False
    return host == company_host or host.endswith("." + company_host)


def is_plausible_full_name(value: object) -> bool:
    words = re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'’-]+", str(value or ""))
    rejected = {"haben", "unseren", "immobilienfonds", "cookie", "kontakt", "zusammenarbeit", "mit", "verwalten", "immobilienverwaltung", "hausverwaltung", "immobilien", "immobilie", "atriensis", "erarbeiten", "klare", "prozesse", "jahre", "erfahrung", "erfahrungen", "service", "management", "unternehmen", "team", "familie", "ansprechpartner", "verwaltung", "geschäftsführung", "leitung"}
    return len(words) in {2, 3} and all(len(word) >= 2 and (word[0].isupper() or word.isupper()) for word in words) and not any(word.lower() in rejected for word in words)


def is_plausible_company_name(value: object) -> bool:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    normalized = text.casefold()
    if not text or len(text.split()) < 2:
        return False
    generic_titles = {
        "über uns", "about us", "kontakt", "contact", "impressum", "startseite",
        "home", "leistungen", "services", "team", "referenzen", "portfolio",
        "immobilien", "hausverwaltung", "immobilienverwaltung",
    }
    if normalized in generic_titles:
        return False
    identity_markers = r"\b(?:gmbh|ag|kg|ohg|gbr|e\.k\.?|ug|hausverwaltung|immobilien|verwaltung|property|real estate)\b"
    generic_tokens = {"klare", "prozesse", "gute", "lösungen", "ihre", "partner", "für", "uns", "sie"}
    return bool(re.search(identity_markers, text, re.I)) or not all(token.casefold() in generic_tokens for token in text.split())


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


def update_run_manifest(path: Path, *, inputs: dict[str, Path] | None = None, outputs: dict[str, Path] | None = None) -> None:
    manifest = __import__("json").loads(path.read_text(encoding="utf-8"))
    root = Path.cwd().resolve()

    def portable_path(item: Path) -> str:
        resolved = item.resolve()
        try:
            return resolved.relative_to(root).as_posix()
        except ValueError:
            return resolved.as_posix()

    for section, values in (("supporting_inputs", inputs or {}), ("outputs", outputs or {})):
        bucket = manifest.setdefault(section, {})
        for name, item in values.items():
            if item.exists():
                bucket[name] = {"path": portable_path(item), "sha256": file_sha256(item)}
    path.write_text(__import__("json").dumps(manifest, indent=2), encoding="utf-8")


def is_public_http_url(value: object) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
