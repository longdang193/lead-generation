"""Pydantic contracts for the Codex-native lead-generation boundaries.

These models validate messages exchanged between the parent agent, native
workers, deterministic repository tools, and the finalization barrier. They do
not implement orchestration or provider access.
"""

from __future__ import annotations

import re
import hashlib
import json
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

HASH64 = re.compile(r"^[0-9a-f]{64}$")


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AssuranceLevel(str, Enum):
    source = "source"
    structural = "structural"
    replay = "replay"
    unknown = "unknown"


class SourceKind(str, Enum):
    official = "official"
    official_site = "official_site"
    permitted_directory = "permitted_directory"
    procurement = "procurement"
    public_news = "public_news"
    ted = "ted"
    public_professional_profile = "public_professional_profile"
    fixture = "fixture"
    other = "other"


TERMINAL_STATUS_ALIASES = {
    "succeeded": "Completed",
    "completed": "Completed",
    "failed": "Failed",
    "cancelled": "Failed",
    "canceled": "Failed",
    "timed_out": "Unavailable",
    "partial": "Partial",
    "unavailable": "Unavailable",
    "rejected": "Rejected",
}


def normalize_terminal_status(value: object) -> str | None:
    text = str(value or "")
    if text in {"Completed", "Partial", "Unavailable", "Failed", "Rejected"}:
        return text
    return TERMINAL_STATUS_ALIASES.get(text.lower())

class ResearchStatus(str, Enum):
    not_searched = "Not searched"
    completed = "Completed"
    partial = "Partial"
    unavailable = "Unavailable"
    failed = "Failed"
    stopped = "Stopped"
    needs_review = "Needs review"


class DeliveryPolicy(str, Enum):
    personal = "personal"
    strict = "strict"


class OfferProfile(ContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    solution: str = Field(min_length=1)
    target_customer: str = Field(min_length=1)
    problems_solved: tuple[str, ...] = Field(min_length=1)
    value_propositions: tuple[str, ...] = Field(min_length=1)
    economic_buyer_roles: tuple[str, ...] = Field(min_length=1)
    relevant_triggers: tuple[str, ...] = Field(default_factory=tuple)
    disqualifiers: tuple[str, ...] = Field(default_factory=tuple)
    incumbent_or_competitor_signals: tuple[str, ...] = Field(default_factory=tuple)


class AccountIndicator(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    indicator_type: Literal["direct_intent", "trigger", "need_indicator", "change_readiness"]
    statement: str = Field(min_length=1)
    strength: float = Field(ge=0, le=100)
    recency: date | None = None
    confidence: Confidence
    supporting_claim_ids: list[str] = Field(min_length=1)
    counterevidence_claim_ids: list[str] = Field(default_factory=list)
    offer_criterion: str = Field(min_length=1)

    @model_validator(mode="after")
    def disjoint_evidence(self) -> "AccountIndicator":
        overlap = set(self.supporting_claim_ids) & set(self.counterevidence_claim_ids)
        if overlap:
            raise ValueError("an indicator claim cannot be both support and counterevidence")
        return self


class MaterialAssertion(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    assertion_id: str = Field(min_length=1)
    assertion_kind: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    content_hash: str | None = None
    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    offer_criterion: str = Field(min_length=1)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    counterevidence_claim_ids: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def bind_content(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        payload = {
            "assertion_id": values.get("assertion_id", ""),
            "assertion_kind": values.get("assertion_kind", ""),
            "statement": " ".join(str(values.get("statement", "")).split()),
            "company_id": values.get("company_id", ""),
            "offer_id": values.get("offer_id", ""),
            "offer_version": values.get("offer_version", ""),
            "offer_criterion": values.get("offer_criterion", ""),
            "supporting_claim_ids": sorted(values.get("supporting_claim_ids") or []),
            "counterevidence_claim_ids": sorted(values.get("counterevidence_claim_ids") or []),
            "uncertainty": sorted(values.get("uncertainty") or []),
        }
        expected = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if values.get("content_hash") is not None and values.get("content_hash") != expected:
            raise ValueError("material assertion content_hash does not match immutable assertion content")
        return {**values, "statement": payload["statement"], "content_hash": expected}


class SemanticReview(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    assertion_id: str = Field(min_length=1)
    semantic_review_id: str | None = None
    assertion_hash: str | None = None
    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    reviewed_claim_ids: list[str] = Field(min_length=1)
    offer_criterion: str = Field(min_length=1)
    entailment: Literal["supported", "unsupported", "unclear"]
    offer_relevance: Literal["relevant", "irrelevant", "unclear"]
    temporal_relevance: Literal["current", "stale", "unknown"]
    contradiction_result: Literal["none", "present", "unclear"]
    decision: Literal["approved", "rejected", "needs_review"]
    reason_codes: list[str] = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    receipt_id: str | None = None
    supersedes_review_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def bind_identity(cls, values: Any) -> Any:
        if not isinstance(values, dict) or values.get("semantic_review_id"):
            return values
        payload = {
            "assertion_id": values.get("assertion_id", ""),
            "assertion_hash": values.get("assertion_hash") or "",
            "reviewed_claim_ids": sorted(values.get("reviewed_claim_ids") or []),
            "offer_criterion": values.get("offer_criterion", ""),
            "decision": values.get("decision", ""),
            "reason_codes": sorted(values.get("reason_codes") or []),
            "reviewer_id": values.get("reviewer_id", ""),
            "receipt_id": values.get("receipt_id") or "",
        }
        review_id = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return {**values, "semantic_review_id": f"review-{review_id}"}

    @model_validator(mode="after")
    def enforce_approval_gate(self) -> "SemanticReview":
        approved = (
            self.entailment == "supported"
            and self.offer_relevance == "relevant"
            and self.temporal_relevance == "current"
            and self.contradiction_result == "none"
        )
        if self.decision == "approved" and not approved:
            raise ValueError("approved semantic review requires supported, relevant, current, contradiction-free evidence")
        return self


class CoverageManifest(ContractModel):
    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    required_checks: list[str] = Field(min_length=1)
    completed_checks: list[str] = Field(default_factory=list)
    provider_states: dict[str, Literal["available", "unavailable", "invalid", "unknown"]] = Field(default_factory=dict)
    truncated: bool = False
    unresolved_candidates: int = Field(default=0, ge=0)
    trigger_state: Literal["Verified trigger", "No trigger found", "Research incomplete", "Unavailable"] = "Research incomplete"
    research_policy_id: str | None = None
    research_policy_version: str | None = None
    research_policy_hash: str | None = None
    settled_receipt_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def completed_checks_are_declared(self) -> "CoverageManifest":
        undeclared = sorted(set(self.completed_checks) - set(self.required_checks))
        if undeclared:
            raise ValueError("completed checks must be declared: " + ", ".join(undeclared))
        if self.trigger_state == "No trigger found" and not self.permits_no_trigger():
            raise ValueError("No trigger found requires complete, clean coverage")
        return self

    def permits_no_trigger(self) -> bool:
        return (
            set(self.completed_checks) == set(self.required_checks)
            and not self.truncated
            and self.unresolved_candidates == 0
            and set(self.provider_states) >= set(self.required_checks)
            and all(self.provider_states.get(check) == "available" for check in self.required_checks)
            and (not self.research_policy_id or bool(self.research_policy_hash and self.settled_receipt_ids))
        )


class RankContribution(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    dimension: Literal["fit", "opportunity", "need", "change", "direct_intent", "access", "evidence_confidence"]
    value: float = Field(ge=0, le=100)
    weight: float = Field(ge=0)
    contribution: float
    supporting_claim_ids: list[str] = Field(default_factory=list)
    supporting_review_ids: list[str] = Field(default_factory=list)
    offer_criterion: str = Field(min_length=1)
    scoring_policy_id: str = "account-intelligence"
    scoring_policy_version: str = "1"
    scoring_policy_hash: str | None = None
    normalized_inputs: dict[str, Any] = Field(default_factory=dict)
    confidence_adjustment: float = 0.0


class RankAudit(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    priority_state: Literal[
        "Priority — verified trigger",
        "Priority — strong fit, no trigger",
        "Nurture",
        "Research required",
        "Disqualify",
    ]
    total_score: float = Field(ge=0)
    contributions: list[RankContribution] = Field(min_length=1)
    rationale_claim_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def contributions_sum_to_total(self) -> "RankAudit":
        total = round(sum(item.contribution for item in self.contributions), 6)
        if abs(total - self.total_score) > 0.01:
            raise ValueError(f"rank contributions do not sum to total_score: expected {total}, observed {self.total_score}")
        return self


class ArtifactRef(ContractModel):
    path: str = Field(min_length=1)
    sha256: str
    kind: str = Field(default="artifact", min_length=1)

    @field_validator("sha256")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if not HASH64.fullmatch(value):
            raise ValueError("sha256 must be a lowercase 64-character hexadecimal digest")
        return value


class Goal(ContractModel):
    goal_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    audience: str | None = None
    geography: str | None = None
    target_count: int = Field(default=0, ge=0)
    constraints: list[str] = Field(default_factory=list)
    delivery_policy: DeliveryPolicy = DeliveryPolicy.personal
    policy_version: str = Field(default="1", min_length=1)


class EvidenceClaim(ContractModel):
    claim_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    value: Any
    source_url: HttpUrl
    evidence_excerpt: str = Field(min_length=1)
    source_kind: SourceKind
    confidence: Confidence
    retrieved_at: datetime
    assurance_level: AssuranceLevel = AssuranceLevel.unknown
    scope: str = Field(default="account", min_length=1)
    published_at: date | None = None
    artifact: ArtifactRef | None = None
    source_domain: str | None = None
    unit: str | None = None
    as_of_date: date | None = None
    person_name: str | None = None
    role: str | None = None
    company_affiliation: str | None = None
    email: str | None = None
    record_type: str | None = None
    research_run_id: str | None = None
    candidate_sha256: str | None = None
    candidate_status: str | None = None
    verified_at: datetime | None = None
    verifier_run_id: str | None = None

    @field_validator("candidate_sha256")
    @classmethod
    def validate_candidate_hash(cls, value: str | None) -> str | None:
        if value is not None and not HASH64.fullmatch(value):
            raise ValueError("candidate_sha256 must be a lowercase 64-character hexadecimal digest")
        return value


def normalize_native_claim(record: dict[str, Any]) -> EvidenceClaim:
    """Convert the native worker wire record into the typed claim contract."""

    normalized = dict(record)
    normalized["claim_id"] = normalized.get("claim_id") or normalized.get("candidate_claim_id")
    normalized["value"] = normalized.get("value", normalized.get("claim_value"))
    if not normalized.get("scope"):
        normalized["scope"] = normalized.get("account_relationship") or "account"
    normalized.setdefault("assurance_level", "unknown")
    normalized.setdefault("candidate_status", "Candidate")
    normalized.setdefault("confidence", "medium")
    if not normalized.get("retrieved_at"):
        normalized["retrieved_at"] = normalized.get("verified_at")
    for key in ("record_type", "candidate_claim_id", "claim_value", "account_relationship"):
        normalized.pop(key, None)
    return EvidenceClaim.model_validate(normalized)


class VerifierDecision(ContractModel):
    claim_id: str = Field(min_length=1)
    candidate_sha256: str | None = None
    decision: Literal["Verified", "Rejected", "Needs review"]
    reason_codes: list[str] = Field(min_length=1)
    verifier_id: str = Field(min_length=1)
    verifier_run_id: str | None = None
    verified_at: datetime
    assurance_level: AssuranceLevel = AssuranceLevel.source

    @field_validator("candidate_sha256")
    @classmethod
    def validate_candidate_hash(cls, value: str | None) -> str | None:
        if value is not None and not HASH64.fullmatch(value):
            raise ValueError("candidate_sha256 must be a lowercase 64-character hexadecimal digest")
        return value


def normalize_native_verifier_decision(record: dict[str, Any]) -> VerifierDecision:
    """Convert the native verifier wire record without losing candidate identity."""

    normalized = dict(record)
    normalized["claim_id"] = normalized.get("candidate_claim_id")
    for key in ("record_type", "candidate_claim_id"):
        normalized.pop(key, None)
    return VerifierDecision.model_validate(normalized)


class ResearchAttempt(ContractModel):
    attempt_id: str = Field(min_length=1)
    query_or_source: str = Field(min_length=1)
    status: Literal["Completed", "Partial", "Unavailable", "Needs review", "Failed", "Timed out", "Cancelled"]
    truncated: bool = False
    provider_status: Literal["Available", "Unavailable", "Invalid", "Unknown"] = "Available"


class ResearchRun(ContractModel):
    run_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    research_type: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    status: ResearchStatus
    started_at: datetime
    completed_at: datetime | None = None
    required_checks: list[str] = Field(default_factory=list)
    completed_checks: list[str] = Field(default_factory=list)
    stop_reason: str | None = None
    attempts: list[ResearchAttempt] = Field(default_factory=list)
    provider_status: Literal["Available", "Unavailable", "Invalid", "Unknown"] = "Available"
    coverage_status: Literal["complete", "partial", "unavailable", "unknown"] = "unknown"
    result_count: int = Field(default=0, ge=0)
    truncated: bool = False

    @field_validator("completed_at")
    @classmethod
    def completed_after_start(cls, value: datetime | None, info: Any) -> datetime | None:
        started = info.data.get("started_at")
        if value is not None and started is not None and value < started:
            raise ValueError("completed_at must not precede started_at")
        return value


def normalize_native_research_run(record: dict[str, Any]) -> ResearchRun:
    """Normalize native adapter status/attempt envelopes into the typed run model."""

    normalized = dict(record)
    attempts = []
    for raw_attempt in normalized.get("attempts") or []:
        if not isinstance(raw_attempt, dict):
            continue
        attempts.append({key: raw_attempt[key] for key in ("attempt_id", "query_or_source", "status", "truncated", "provider_status") if key in raw_attempt})
    normalized["attempts"] = attempts
    for key in ("record_type", "campaign_id", "company_name", "trusted_domain", "location", "source", "adapter_capability", "assurance_level", "scope_version", "scope_hash"):
        normalized.pop(key, None)
    return ResearchRun.model_validate(normalized)


class RunContext(ContractModel):
    run_id: str = Field(min_length=1)
    goal: Goal
    company_id: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    as_of_date: date
    budget_limit: int = Field(ge=0)


class NativeActionRequest(ContractModel):
    run_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    parent_action_id: str | None = None
    company_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_name: str | None = None
    skills: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(min_length=1)
    request_hash: str
    budget_units: int = Field(default=1, ge=0)
    provenance: dict[str, str] = Field(default_factory=dict)

    @field_validator("request_hash")
    @classmethod
    def validate_request_hash(cls, value: str) -> str:
        if not HASH64.fullmatch(value):
            raise ValueError("request_hash must be a lowercase 64-character hexadecimal digest")
        return value


class WorkerResult(ContractModel):
    run_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    status: Literal["Completed", "Partial", "Unavailable", "Failed"]
    result: dict[str, Any] = Field(default_factory=dict)
    artifact: ArtifactRef | None = None
    result_hash: str
    provenance: dict[str, str] = Field(default_factory=dict)
    validation_errors: list[str] = Field(default_factory=list)

    @field_validator("result_hash")
    @classmethod
    def validate_result_hash(cls, value: str) -> str:
        if not HASH64.fullmatch(value):
            raise ValueError("result_hash must be a lowercase 64-character hexadecimal digest")
        return value


class LifecycleEvent(ContractModel):
    run_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    parent_action_id: str | None = None
    event_type: Literal["admitted", "result_validated", "result_rejected", "settled"]
    company_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_name: str | None = None
    skills: list[str] = Field(default_factory=list)
    request_hash: str
    budget_units: int = Field(default=0, ge=0)
    result_hash: str | None = None
    artifact_path: str | None = None
    artifact_hash: str | None = None
    terminal_status: Literal["Completed", "Partial", "Unavailable", "Failed", "Rejected"] | None = None
    budget_settled: int = Field(default=0, ge=0)
    coverage_delta: dict[str, Any] = Field(default_factory=dict)
    stop_decision: dict[str, Any] | None = None
    validation_errors: list[str] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("request_hash", "result_hash", "artifact_hash")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value is not None and not HASH64.fullmatch(value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value


class StopDecision(ContractModel):
    run_id: str = Field(min_length=1)
    company_id: str = Field(min_length=1)
    decision: Literal["continue", "stop"]
    reason: str = Field(min_length=1)
    required_checks: list[str] = Field(default_factory=list)
    completed_checks: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)


class ActionReceipt(ContractModel):
    run_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    parent_action_id: str | None = None
    company_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    profile_name: str | None = None
    skills: list[str] = Field(default_factory=list)
    idempotency_key: str = Field(min_length=1)
    request_hash: str
    result_hash: str
    artifact_hash: str | None = None
    provenance: dict[str, str] = Field(default_factory=dict)
    terminal_status: Literal["Completed", "Partial", "Unavailable", "Failed", "Rejected"]
    validation_errors: list[str] = Field(default_factory=list)
    budget_requested: int = Field(default=0, ge=0)
    budget_settled: int = Field(default=0, ge=0)
    coverage_delta: dict[str, Any] = Field(default_factory=dict)
    stop_decision: StopDecision | None = None
    finalization_linkage: str | None = None
    created_at: datetime

    @field_validator("request_hash", "result_hash", "artifact_hash")
    @classmethod
    def validate_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not HASH64.fullmatch(value):
            raise ValueError("receipt hashes must be lowercase 64-character hexadecimal digests")
        return value

    @field_validator("budget_settled")
    @classmethod
    def settled_within_request(cls, value: int, info: Any) -> int:
        requested = info.data.get("budget_requested")
        if requested is not None and value > requested:
            raise ValueError("budget_settled cannot exceed budget_requested")
        return value


class AccountHypothesis(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    hypothesis_type: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    counterevidence_claim_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    speculative: bool = False
    validation_step: str | None = None
    decision_relevant_gap: str | None = None


class AccountThesis(ContractModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    company_id: str = Field(min_length=1)
    offer_id: str = Field(min_length=1)
    offer_version: str = Field(min_length=1)
    structural_fit: float = Field(ge=0, le=100)
    opportunity_potential: float | None = Field(default=None, ge=0, le=100)
    indicators: list[AccountIndicator] = Field(default_factory=list)
    material_assertions: list[MaterialAssertion] = Field(default_factory=list)
    hypotheses: list[AccountHypothesis] = Field(default_factory=list)
    direct_intent: str | None = None
    confidence: Confidence
    why_this_account: str = Field(min_length=1)
    why_now: str = Field(min_length=1)
    problem_hypothesis: str = Field(min_length=1)
    strongest_claim_ids: list[str] = Field(min_length=1)
    counterevidence_claim_ids: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    access_summary: str = Field(min_length=1)
    research_gaps: list[str] = Field(default_factory=list)
    research_gap_impact: str = Field(min_length=1)
    semantic_review_ids: list[str] = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class FinalizationRequest(ContractModel):
    run_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    delivery_policy: DeliveryPolicy
    required_checks: list[str] = Field(default_factory=list)
    completed_checks: list[str] = Field(default_factory=list)
    allow_partial: bool = False
    stop_decision: StopDecision | None = None
