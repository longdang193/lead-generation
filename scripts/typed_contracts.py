"""Pydantic contracts for the Codex-native lead-generation boundaries.

These models validate messages exchanged between the parent agent, native
workers, deterministic repository tools, and the finalization barrier. They do
not implement orchestration or provider access.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


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
    official_site = "official_site"
    permitted_directory = "permitted_directory"
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
    completed = "Completed"
    partial = "Partial"
    unavailable = "Unavailable"
    failed = "Failed"
    stopped = "Stopped"


class DeliveryPolicy(str, Enum):
    personal = "personal"
    strict = "strict"


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


class VerifierDecision(ContractModel):
    claim_id: str = Field(min_length=1)
    decision: Literal["Verified", "Rejected", "Needs review"]
    reason_codes: list[str] = Field(min_length=1)
    verifier_id: str = Field(min_length=1)
    verified_at: datetime
    assurance_level: AssuranceLevel = AssuranceLevel.source


class ResearchAttempt(ContractModel):
    attempt_id: str = Field(min_length=1)
    query_or_source: str = Field(min_length=1)
    status: Literal["Completed", "Failed", "Timed out", "Cancelled"]
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
    event_type: Literal["admitted", "result_validated", "settled"]
    company_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    request_hash: str
    budget_units: int = Field(default=0, ge=0)
    result_hash: str | None = None
    artifact_path: str | None = None
    artifact_hash: str | None = None
    terminal_status: Literal["Completed", "Partial", "Unavailable", "Failed", "Rejected"] | None = None
    budget_settled: int = Field(default=0, ge=0)
    coverage_delta: dict[str, Any] = Field(default_factory=dict)
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
    company_id: str = Field(min_length=1)
    hypothesis_type: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    counterevidence_claim_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    speculative: bool = False


class AccountThesis(ContractModel):
    company_id: str = Field(min_length=1)
    structural_fit: float = Field(ge=0, le=100)
    opportunity_potential: float | None = Field(default=None, ge=0, le=100)
    indicators: list[str] = Field(default_factory=list)
    hypotheses: list[AccountHypothesis] = Field(default_factory=list)
    direct_intent: str | None = None
    confidence: Confidence
    research_gaps: list[str] = Field(default_factory=list)
    recommended_action: str = Field(min_length=1)


class FinalizationRequest(ContractModel):
    run_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    delivery_policy: DeliveryPolicy
    required_checks: list[str] = Field(default_factory=list)
    completed_checks: list[str] = Field(default_factory=list)
    allow_partial: bool = False
    stop_decision: StopDecision | None = None
