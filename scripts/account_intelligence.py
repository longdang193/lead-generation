"""Deterministic account-intelligence projections."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from score_leads import calculate_fit
from typed_contracts import (
    AccountHypothesis,
    AccountIndicator,
    AccountThesis,
    AssuranceLevel,
    CoverageManifest,
    EvidenceClaim,
    MaterialAssertion,
    OfferProfile,
    SemanticReview,
    normalize_native_claim,
)


_ALLOWED_STATUSES = {"Candidate", "Rejected", "Unresolved", "Verified", "Supported"}


def _claim_model(value: EvidenceClaim | dict[str, Any]) -> EvidenceClaim:
    if isinstance(value, EvidenceClaim):
        return value
    return normalize_native_claim(value)


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


def _is_verified_support(status: str, claim: EvidenceClaim) -> bool:
    return status in {"Verified", "Supported"} and claim.assurance_level == AssuranceLevel.source


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
        verified_support = _is_verified_support(status, claim)
        value_dict = value if isinstance(value, dict) else {}
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
            "corroborating_source_families": [source_family] if verified_support else [],
            "corroborating_fingerprints": [fingerprint] if verified_support else [],
            "corroboration_count": 1 if verified_support else 0,
            "rejected_count": 1 if status == "Rejected" else 0,
            "unresolved_count": 1 if status == "Unresolved" else 0,
            "contradictory_count": 1 if value_dict.get("contradictory") is True else 0,
        }
        if key not in timeline:
            timeline[key] = record
            continue
        prior = timeline[key]
        for field, value_to_add in (("claim_ids", claim.claim_id), ("source_urls", source_url), ("statuses", status), ("assurance_levels", claim.assurance_level.value), ("source_families", source_family), ("evidence_fingerprints", fingerprint)):
            if value_to_add not in prior[field]:
                prior[field].append(value_to_add)
        if verified_support:
            if source_family not in prior["corroborating_source_families"]:
                prior["corroborating_source_families"].append(source_family)
            if fingerprint not in prior["corroborating_fingerprints"]:
                prior["corroborating_fingerprints"].append(fingerprint)
        prior["rejected_count"] += int(status == "Rejected")
        prior["unresolved_count"] += int(status == "Unresolved")
        prior["contradictory_count"] += int(value_dict.get("contradictory") is True)
        prior["status"] = _derived_event_status(set(prior["statuses"]))
        prior["corroboration_count"] = min(len(set(prior["corroborating_source_families"])), len(set(prior["corroborating_fingerprints"])))
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


def validate_semantic_review(review: SemanticReview | dict[str, Any], claims: Iterable[EvidenceClaim | dict[str, Any]], *, offer_profile: OfferProfile | dict[str, Any] | None = None, material_assertions: Iterable[MaterialAssertion | dict[str, Any]] = ()) -> SemanticReview:
    validated = review if isinstance(review, SemanticReview) else SemanticReview.model_validate(review)
    by_id = {claim.claim_id: claim for claim in (_claim_model(item) for item in claims)}
    missing = sorted(set(validated.reviewed_claim_ids) - set(by_id))
    if missing:
        raise ValueError(f"semantic review references missing claim IDs: {', '.join(missing)}")
    if any(by_id[claim_id].company_id != validated.company_id for claim_id in validated.reviewed_claim_ids):
        raise ValueError("semantic review references claims from another company")
    if offer_profile is not None:
        profile = offer_profile if isinstance(offer_profile, OfferProfile) else OfferProfile.model_validate(offer_profile)
        if (validated.offer_id, validated.offer_version) != (profile.offer_id, profile.offer_version):
            raise ValueError("semantic review offer context does not match offer profile")
    assertions = [item if isinstance(item, MaterialAssertion) else MaterialAssertion.model_validate(item) for item in material_assertions]
    if assertions:
        matches = [item for item in assertions if item.assertion_id == validated.assertion_id and item.company_id == validated.company_id and (item.offer_id, item.offer_version) == (validated.offer_id, validated.offer_version)]
        if len(matches) != 1:
            raise ValueError("semantic review must reference exactly one material assertion")
        assertion = matches[0]
        if validated.assertion_hash != assertion.content_hash:
            raise ValueError("semantic review assertion hash does not match immutable assertion content")
        if not set(validated.reviewed_claim_ids).issubset(set(assertion.supporting_claim_ids) | set(assertion.counterevidence_claim_ids)):
            raise ValueError("semantic review claims exceed the material assertion claim set")
    return validated


def validate_coverage_manifest(manifest: CoverageManifest | dict[str, Any]) -> CoverageManifest:
    return manifest if isinstance(manifest, CoverageManifest) else CoverageManifest.model_validate(manifest)


def account_signal_state(
    matched_events: Iterable[dict[str, Any]],
    manifest: CoverageManifest | dict[str, Any] | None,
) -> str:
    events = list(matched_events)
    if events:
        return "Verified trigger"
    if manifest is None:
        return "Research incomplete"
    coverage = validate_coverage_manifest(manifest)
    if all(state in {"unavailable", "invalid"} for state in coverage.provider_states.values()) and coverage.provider_states:
        return "Unavailable"
    return "No trigger found" if coverage.permits_no_trigger() else "Research incomplete"


def validate_account_thesis(
    thesis: AccountThesis | dict[str, Any],
    claims: Iterable[EvidenceClaim | dict[str, Any]],
    *,
    enforce_structural_fit: bool = False,
    semantic_reviews: Iterable[SemanticReview | dict[str, Any]] = (),
    offer_profile: OfferProfile | dict[str, Any] | None = None,
) -> AccountThesis:
    validated = thesis if isinstance(thesis, AccountThesis) else AccountThesis.model_validate(thesis)
    claim_list = [_claim_model(item) for item in claims]
    profile = offer_profile if isinstance(offer_profile, OfferProfile) else OfferProfile.model_validate(offer_profile) if offer_profile is not None else None
    if profile is not None and (validated.offer_id, validated.offer_version) != (profile.offer_id, profile.offer_version):
        raise ValueError("thesis offer context does not match offer profile")
    foreign_claims = sorted({claim.company_id for claim in claim_list if claim.company_id != validated.company_id})
    if foreign_claims:
        raise ValueError("thesis claims include another company: " + ", ".join(foreign_claims))
    hypotheses = []
    for hypothesis in validated.hypotheses:
        if hypothesis.company_id != validated.company_id:
            raise ValueError("thesis hypotheses must match the enclosing company")
        if (hypothesis.offer_id, hypothesis.offer_version) != (validated.offer_id, validated.offer_version):
            raise ValueError("hypothesis offer context does not match the enclosing thesis")
        hypotheses.append(validate_account_hypothesis(hypothesis, claim_list))
    claim_ids = {claim.claim_id for claim in claim_list}
    referenced = set(validated.strongest_claim_ids) | set(validated.counterevidence_claim_ids)
    missing = sorted(referenced - claim_ids)
    if missing:
        raise ValueError(f"thesis references missing claim IDs: {', '.join(missing)}")
    if any(claim.company_id != validated.company_id for claim in claim_list if claim.claim_id in referenced):
        raise ValueError("thesis references claims from another company")
    if set(validated.strongest_claim_ids) & set(validated.counterevidence_claim_ids):
        raise ValueError("a thesis claim cannot be both strongest evidence and counterevidence")
    reviews = [validate_semantic_review(item, claim_list, offer_profile=profile) for item in semantic_reviews]
    assertions = [item if isinstance(item, MaterialAssertion) else MaterialAssertion.model_validate(item) for item in validated.material_assertions]
    reviews = [validate_semantic_review(item, claim_list, offer_profile=profile, material_assertions=assertions) for item in reviews]
    reviews_by_id = {key: review for review in reviews for key in {review.assertion_id, review.semantic_review_id or ""} if key}
    missing_reviews = sorted(set(validated.semantic_review_ids) - set(reviews_by_id))
    if missing_reviews:
        raise ValueError(f"thesis references missing semantic review IDs: {', '.join(missing_reviews)}")
    selected_reviews = [reviews_by_id[review_id] for review_id in validated.semantic_review_ids]
    if any(review.decision != "approved" for review in selected_reviews):
        raise ValueError("thesis requires approved semantic reviews for every material assertion")
    if any(
        review.company_id != validated.company_id
        or (review.offer_id, review.offer_version) != (validated.offer_id, validated.offer_version)
        for review in selected_reviews
    ):
        raise ValueError("thesis semantic reviews must match the enclosing company and offer")
    if assertions:
        assertion_ids = {item.assertion_id for item in assertions}
        if not assertion_ids.issubset({review.assertion_id for review in selected_reviews}):
            raise ValueError("every material assertion requires a matching semantic review")
        assertion_claims = {claim_id for item in assertions for claim_id in item.supporting_claim_ids + item.counterevidence_claim_ids}
        if not assertion_claims.issubset(claim_ids | set(validated.counterevidence_claim_ids)):
            raise ValueError("material assertions reference claims outside the thesis")
    reviewed_claim_ids = {claim_id for review in selected_reviews for claim_id in review.reviewed_claim_ids}
    unsupported_claims = sorted((set(validated.strongest_claim_ids) | set(validated.counterevidence_claim_ids)) - reviewed_claim_ids)
    if unsupported_claims:
        raise ValueError("thesis material claims lack semantic review support: " + ", ".join(unsupported_claims))
    reviews_by_criterion = {
        review.offer_criterion: review
        for review in reviews
        if review.company_id == validated.company_id
        and (review.offer_id, review.offer_version) == (validated.offer_id, validated.offer_version)
        and review.decision == "approved"
    }
    for indicator in validated.indicators:
        if indicator.company_id != validated.company_id or (indicator.offer_id, indicator.offer_version) != (validated.offer_id, validated.offer_version):
            raise ValueError("indicator context does not match the enclosing thesis")
        missing_indicator_claims = sorted(set(indicator.supporting_claim_ids) - claim_ids)
        if missing_indicator_claims:
            raise ValueError(f"indicator references missing claim IDs: {', '.join(missing_indicator_claims)}")
        review = reviews_by_criterion.get(indicator.offer_criterion)
        if review is None or not set(indicator.supporting_claim_ids).issubset(review.reviewed_claim_ids):
            raise ValueError("indicator lacks an approved semantic review for its offer criterion")
    if enforce_structural_fit:
        deterministic_fit = calculate_structural_fit(claim_list)
        if abs(validated.structural_fit - deterministic_fit) > 0.01:
            raise ValueError(f"structural_fit does not match deterministic fact score: expected {deterministic_fit}, observed {validated.structural_fit}")
    return validated.model_copy(update={"hypotheses": hypotheses, "material_assertions": assertions})


def calculate_structural_fit(claims: Iterable[EvidenceClaim | dict[str, Any]]) -> float:
    """Calculate a fact-only fit score; hypotheses are intentionally ignored."""

    record: dict[str, object] = {}
    for raw_claim in claims:
        claim = _claim_model(raw_claim)
        status = claim.candidate_status or "Unresolved"
        if claim.assurance_level != AssuranceLevel.source or status not in {"Verified", "Supported"}:
            continue
        if claim.claim_type in {"service_fit", "residential_weg", "berlin_relevance"}:
            value = claim.value.get("value") if isinstance(claim.value, dict) and "value" in claim.value else claim.value
            record[claim.claim_type] = value
        elif claim.claim_type == "portfolio_size":
            value = claim.value.get("value") if isinstance(claim.value, dict) and "value" in claim.value else claim.value
            record["portfolio_size"] = value
    fit, _ = calculate_fit(record)
    return round(fit or 0.0, 2)


def project_account_intelligence(
    claims: Iterable[EvidenceClaim | dict[str, Any]],
    thesis: AccountThesis | dict[str, Any],
    timeline_path: Path | None = None,
    *,
    semantic_reviews: Iterable[SemanticReview | dict[str, Any]] = (),
    offer_profile: OfferProfile | dict[str, Any] | None = None,
) -> dict[str, Any]:
    claim_list = list(claims)
    review_list = list(semantic_reviews)
    validated_thesis = validate_account_thesis(
        thesis,
        claim_list,
        enforce_structural_fit=True,
        semantic_reviews=review_list,
        offer_profile=offer_profile,
    )
    validated_reviews = [validate_semantic_review(item, claim_list, offer_profile=offer_profile) for item in review_list]
    timeline = build_account_timeline(claim_list)
    result = {
        "company_id": validated_thesis.company_id,
        "offer_id": validated_thesis.offer_id,
        "offer_version": validated_thesis.offer_version,
        "claims": [_claim_model(item).model_dump(mode="json") for item in claim_list],
        "timeline": timeline,
        "thesis": validated_thesis.model_dump(mode="json"),
        "semantic_reviews": [review.model_dump(mode="json") for review in validated_reviews],
        "structural_fit_fact_score": calculate_structural_fit(claim_list),
        "dossier_version": "1",
        "run_id": next((claim.research_run_id for claim in (_claim_model(item) for item in claim_list) if claim.research_run_id), None),
    }
    result["dossier_hash"] = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()
    if timeline_path is not None:
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with timeline_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in timeline:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")
    return result
