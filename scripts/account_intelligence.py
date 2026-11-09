"""Deterministic account-intelligence projections."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from score_leads import calculate_fit
from typed_contracts import AccountHypothesis, AccountThesis, AssuranceLevel, EvidenceClaim, SourceKind


_ALLOWED_STATUSES = {"Candidate", "Rejected", "Unresolved", "Verified", "Supported"}


def _claim_model(value: EvidenceClaim | dict[str, Any]) -> EvidenceClaim:
    if isinstance(value, EvidenceClaim):
        return value
    normalized = dict(value)
    normalized["claim_id"] = normalized.get("claim_id") or normalized.get("candidate_claim_id")
    claim_value = normalized.get("value", normalized.get("claim_value"))
    if isinstance(claim_value, dict):
        claim_value = claim_value.get("value", claim_value.get("name", claim_value))
    normalized["value"] = claim_value
    normalized.setdefault("scope", normalized.get("account_relationship", "account"))
    source_kind = str(normalized.get("source_kind") or "other")
    if source_kind not in {item.value for item in SourceKind}:
        source_kind = "other"
    normalized["source_kind"] = source_kind
    normalized.setdefault("assurance_level", "unknown")
    normalized.setdefault("candidate_status", "Unresolved")
    normalized.setdefault("confidence", "medium")
    normalized.setdefault("retrieved_at", normalized.get("verified_at"))
    for legacy_key in ("candidate_claim_id", "claim_value", "account_relationship"):
        normalized.pop(legacy_key, None)
    return EvidenceClaim.model_validate(normalized)


def event_identity(company_id: str, event_id: str) -> str:
    if not company_id or not event_id:
        raise ValueError("company_id and event_id are required for event identity")
    return f"{company_id}:{event_id}"


def _claim_status(raw_claim: EvidenceClaim | dict[str, Any], claim: EvidenceClaim) -> str:
    raw_status = raw_claim.get("candidate_status") if isinstance(raw_claim, dict) else claim.candidate_status
    status = str(raw_status or "Unresolved")
    return status if status in _ALLOWED_STATUSES else "Unresolved"


def _source_family(claim: EvidenceClaim) -> str:
    source_domain = (claim.source_domain or "").strip().lower()
    if source_domain:
        return source_domain.removeprefix("www.")
    return (urlparse(str(claim.source_url)).hostname or "unknown").lower().removeprefix("www.")


def _evidence_fingerprint(claim: EvidenceClaim, event_id: str, event_type: str) -> str:
    value = claim.value if isinstance(claim.value, dict) else {"value": claim.value}
    payload = {
        "company_id": claim.company_id,
        "event_id": event_id,
        "event_type": event_type,
        "value": value,
        "excerpt": " ".join(claim.evidence_excerpt.split()).lower(),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _derived_event_status(statuses: set[str]) -> str:
    if statuses == {"Verified"}:
        return "Verified"
    if statuses and statuses <= {"Verified", "Supported"}:
        return "Supported"
    if statuses == {"Rejected"}:
        return "Rejected"
    if statuses == {"Candidate"}:
        return "Candidate"
    return "Unresolved"


def build_account_timeline(claims: Iterable[EvidenceClaim | dict[str, Any]]) -> list[dict[str, Any]]:
    """Project event claims while retaining every corroborating lineage record."""

    timeline: dict[str, dict[str, Any]] = {}
    for raw_claim in claims:
        claim = _claim_model(raw_claim)
        if claim.claim_type != "event":
            continue
        value = claim.value if isinstance(claim.value, dict) else {}
        event_id = str(value.get("event_id") or claim.claim_id)
        key = event_identity(claim.company_id, event_id)
        status = _claim_status(raw_claim, claim)
        event_type = str(value.get("event_type") or value.get("type") or "event")
        source_url = str(claim.source_url)
        source_family = _source_family(claim)
        fingerprint = _evidence_fingerprint(claim, event_id, event_type)
        record = {
            "event_identity": key,
            "event_id": event_id,
            "company_id": claim.company_id,
            "event_type": event_type,
            "event_date": value.get("event_date") or value.get("publication_date") or claim.published_at,
            "status": status,
            "claim_id": claim.claim_id,
            "claim_ids": [claim.claim_id],
            "source_url": source_url,
            "source_urls": [source_url],
            "evidence_excerpt": claim.evidence_excerpt,
            "assurance_level": claim.assurance_level.value,
            "assurance_levels": [claim.assurance_level.value],
            "statuses": [status],
            "source_families": [source_family],
            "evidence_fingerprints": [fingerprint],
            "corroboration_count": 1,
        }
        if key not in timeline:
            timeline[key] = record
            continue
        prior = timeline[key]
        for field, value_to_add in (("claim_ids", claim.claim_id), ("source_urls", source_url), ("statuses", status), ("assurance_levels", claim.assurance_level.value), ("source_families", source_family), ("evidence_fingerprints", fingerprint)):
            if value_to_add not in prior[field]:
                prior[field].append(value_to_add)
        prior["status"] = _derived_event_status(set(prior["statuses"]))
        prior["corroboration_count"] = len(prior["evidence_fingerprints"])
    return sorted(timeline.values(), key=lambda row: (row["company_id"], str(row.get("event_date") or ""), row["event_id"]))


def validate_account_hypothesis(hypothesis: AccountHypothesis | dict[str, Any], claims: Iterable[EvidenceClaim | dict[str, Any]]) -> AccountHypothesis:
    validated = hypothesis if isinstance(hypothesis, AccountHypothesis) else AccountHypothesis.model_validate(hypothesis)
    by_id = {claim.claim_id: claim for claim in (_claim_model(item) for item in claims)}
    referenced = set(validated.supporting_claim_ids) | set(validated.counterevidence_claim_ids)
    missing = sorted(referenced - set(by_id))
    if missing:
        raise ValueError(f"hypothesis references missing claim IDs: {', '.join(missing)}")
    wrong_company = sorted(claim_id for claim_id in referenced if by_id[claim_id].company_id != validated.company_id)
    if wrong_company:
        raise ValueError("hypothesis references claims from another company")
    overlap = set(validated.supporting_claim_ids) & set(validated.counterevidence_claim_ids)
    if overlap:
        raise ValueError("a claim cannot support and counterevidence the same hypothesis")
    if not validated.supporting_claim_ids and not validated.speculative:
        validated = validated.model_copy(update={"speculative": True})
    return validated


def validate_account_thesis(thesis: AccountThesis | dict[str, Any], claims: Iterable[EvidenceClaim | dict[str, Any]], *, enforce_structural_fit: bool = False) -> AccountThesis:
    validated = thesis if isinstance(thesis, AccountThesis) else AccountThesis.model_validate(thesis)
    claim_list = [_claim_model(item) for item in claims]
    foreign_claims = sorted({claim.company_id for claim in claim_list if claim.company_id != validated.company_id})
    if foreign_claims:
        raise ValueError("thesis claims include another company: " + ", ".join(foreign_claims))
    hypotheses = []
    for hypothesis in validated.hypotheses:
        if hypothesis.company_id != validated.company_id:
            raise ValueError("thesis hypotheses must match the enclosing company")
        hypotheses.append(validate_account_hypothesis(hypothesis, claim_list))
    if enforce_structural_fit:
        deterministic_fit = calculate_structural_fit(claim_list)
        if abs(validated.structural_fit - deterministic_fit) > 0.01:
            raise ValueError(f"structural_fit does not match deterministic fact score: expected {deterministic_fit}, observed {validated.structural_fit}")
    return validated.model_copy(update={"hypotheses": hypotheses})


def calculate_structural_fit(claims: Iterable[EvidenceClaim | dict[str, Any]]) -> float:
    """Calculate a fact-only fit score; hypotheses are intentionally ignored."""

    record: dict[str, object] = {}
    for raw_claim in claims:
        claim = _claim_model(raw_claim)
        status = claim.candidate_status or "Unresolved"
        if claim.assurance_level != AssuranceLevel.source or status not in {"Verified", "Supported"}:
            continue
        if claim.claim_type in {"service_fit", "residential_weg", "berlin_relevance"}:
            record[claim.claim_type] = claim.value
        elif claim.claim_type == "portfolio_size":
            record["portfolio_size"] = claim.value
    fit, _ = calculate_fit(record)
    return round(fit or 0.0, 2)


def project_account_intelligence(claims: Iterable[EvidenceClaim | dict[str, Any]], thesis: AccountThesis | dict[str, Any], timeline_path: Path | None = None) -> dict[str, Any]:
    claim_list = list(claims)
    validated_thesis = validate_account_thesis(thesis, claim_list, enforce_structural_fit=True)
    timeline = build_account_timeline(claim_list)
    result = {
        "company_id": validated_thesis.company_id,
        "timeline": timeline,
        "thesis": validated_thesis.model_dump(mode="json"),
        "structural_fit_fact_score": calculate_structural_fit(claim_list),
    }
    if timeline_path is not None:
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with timeline_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in timeline:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")
    return result
