from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


BUYING_SIGNALS = ("Strong", "Medium", "Weak", "None found", "Unknown")
SEARCH_STATUSES = ("Searched", "Not searched", "Unavailable", "Unknown")
RESEARCH_STATUSES = ("Not searched", "Completed", "Partial", "Unavailable", "Needs review")
CLAIM_STATUSES = ("Candidate", "Verified", "Rejected", "Needs review")
ACTIONABILITY = ("Ready", "Research", "Monitor", "Unknown")
SALES_PRIORITIES = ("Pursue", "Research", "Defer")
TIME_SENSITIVE_CLAIMS = {"buying_signal", "event"}
QUANTITATIVE_CLAIMS = {"portfolio_size", "portfolio_value"}


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


def email_owner_matches_person(email: object, person_name: object) -> bool:
    if not email or not person_name or "@" not in str(email) or not is_plausible_full_name(person_name):
        return False
    local = re.sub(r"[^a-z0-9]", "", str(email).split("@", 1)[0].casefold())
    words = [re.sub(r"[^a-z0-9]", "", word.casefold()) for word in re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'’-]+", str(person_name))]
    return bool(words and len(words[-1]) >= 3 and words[-1] in local)


def is_plausible_full_name(value: object) -> bool:
    words = re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'’-]+", str(value or ""))
    rejected = {"haben", "unseren", "immobilienfonds", "cookie", "kontakt", "zusammenarbeit", "mit", "verwalten", "immobilienverwaltung", "hausverwaltung", "immobilien", "immobilie", "atriensis", "erarbeiten", "klare", "prozesse", "jahre", "erfahrung", "erfahrungen", "service", "management", "unternehmen", "team", "familie", "ansprechpartner", "verwaltung", "geschäftsführung", "leitung", "schadensmeldungen", "mitgliedschaften"}
    return len(words) in {2, 3} and all(len(word) >= 2 and (word[0].isupper() or word.isupper()) for word in words) and not any(word.lower() in rejected for word in words)


def contact_claim_valid(contact: dict[str, object], company_domain: object = "") -> tuple[bool, list[str]]:
    missing: list[str] = []
    for field in ("person_name", "role", "company_affiliation", "source_url", "evidence_excerpt"):
        if contact.get(field) in (None, "", "Unknown"):
            missing.append(field)
    if not is_plausible_full_name(contact.get("person_name")):
        missing.append("person_name_plausibility")
    if not is_public_http_url(contact.get("source_url")):
        missing.append("source_url_http")
    excerpt = str(contact.get("evidence_excerpt") or "").casefold()
    name = str(contact.get("person_name") or "").casefold()
    if name and name not in excerpt:
        missing.append("person_name_not_in_excerpt")
    if company_domain and contact.get("email") not in (None, "", "Unknown") and not is_valid_business_email(contact.get("email"), company_domain):
        missing.append("email_company_domain")
    if is_generic_mailbox(contact.get("email")):
        missing.append("generic_mailbox_is_not_personal")
    return not missing, missing


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


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def candidate_claim_id(claim: dict[str, object]) -> str:
    values = []
    for key in ("company_id", "claim_type", "claim_value", "source_url"):
        value = claim.get(key, "")
        values.append(canonical_json(value) if isinstance(value, (dict, list)) else str(value))
    payload = "|".join(values)
    return "claim-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def candidate_sha256(claim: dict[str, object]) -> str:
    immutable = {key: value for key, value in claim.items() if key != "candidate_sha256"}
    return hashlib.sha256(canonical_json(immutable).encode("utf-8")).hexdigest()


def claim_requirements_met(claim: dict[str, object]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for field in ("company_id", "claim_type", "claim_value", "source_url", "source_kind", "evidence_excerpt", "retrieved_at", "research_run_id"):
        if claim.get(field) in (None, "", []):
            missing.append(field)
    if claim.get("claim_type") in TIME_SENSITIVE_CLAIMS and claim.get("published_at") in (None, "", "Unknown"):
        missing.append("published_at")
    if claim.get("claim_type") in QUANTITATIVE_CLAIMS:
        for field in ("unit", "scope", "as_of_date"):
            if claim.get(field) in (None, "", "Unknown"):
                missing.append(field)
    if claim.get("claim_type") == "contact":
        for field in ("person_name", "role", "company_affiliation"):
            if claim.get(field) in (None, "", "Unknown"):
                missing.append(field)
    if not is_public_http_url(claim.get("source_url")):
        missing.append("source_url_http")
    return not missing, missing


def verifier_decision_valid(decision: dict[str, object], claim: dict[str, object]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    allowed_fields = {"record_type", "candidate_claim_id", "candidate_sha256", "decision", "reason_codes", "verifier_id", "verifier_run_id", "assurance_level", "verified_at"}
    unexpected = sorted(set(decision) - allowed_fields)
    if unexpected:
        errors.append("decision_mutates_candidate")
    if decision.get("candidate_claim_id") != claim.get("candidate_claim_id"):
        errors.append("candidate_claim_id_mismatch")
    if decision.get("candidate_sha256") != candidate_sha256(claim):
        errors.append("candidate_sha256_mismatch")
    if decision.get("decision") not in {"Verified", "Rejected", "Needs review"}:
        errors.append("invalid_decision")
    for field in ("reason_codes", "verifier_id", "verifier_run_id", "verified_at"):
        if decision.get(field) in (None, "", []):
            errors.append(field)
    if any(field in decision for field in ("claim_value", "source_url", "evidence_excerpt")):
        errors.append("decision_mutates_candidate")
    return not errors, errors


def none_found_allowed(research_run: dict[str, object], verified_claims: list[dict[str, object]]) -> bool:
    company_id = str(research_run.get("company_id") or "")
    scope = str(research_run.get("scope") or "")
    if not company_id or not scope or company_id not in scope:
        return False
    if research_run.get("status") != "Completed":
        return False
    if research_run.get("provider_status") != "Available":
        return False
    if research_run.get("truncated") is True:
        return False
    attempts = research_run.get("attempts") or []
    if not attempts or any(attempt.get("status") != "Completed" or attempt.get("truncated") for attempt in attempts if isinstance(attempt, dict)):
        return False
    return not verified_claims


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


def update_run_manifest(
    path: Path,
    *,
    inputs: dict[str, Path] | None = None,
    supporting_inputs: dict[str, Path] | None = None,
    outputs: dict[str, Path] | None = None,
) -> None:
    from run_manifest import repository_root, update

    root = repository_root(path.parent)
    manifest = __import__("json").loads(path.read_text(encoding="utf-8"))
    if not manifest.get("run_id") or not manifest.get("head_sha"):
        return
    existing_inputs = {name: item for name, item in (inputs or {}).items() if item.exists()}
    existing_supporting = {name: item for name, item in (supporting_inputs or {}).items() if item.exists()}
    existing_outputs = {name: item for name, item in (outputs or {}).items() if item.exists()}
    update(path, root, inputs=existing_inputs, supporting_inputs=existing_supporting, outputs=existing_outputs)


def run_scope_matches(value: object, run_id: str) -> bool:
    text = str(value or "")
    return text == run_id or text.startswith(f"{run_id}:")


def is_public_http_url(value: object) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
