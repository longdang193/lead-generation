from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


REQUIRED_FIELDS = (
    "campaign_id",
    "version",
    "target_count",
    "qualification",
    "input_bindings",
    "lanes",
    "adapter_policy",
)

DELIVERY_POLICIES = {"personal", "strict"}


def qualification_eligibility(row: Mapping[str, object], delivery_policy: str, *, recompute: bool = False) -> bool:
    if delivery_policy not in DELIVERY_POLICIES:
        raise ValueError(f"unknown delivery policy: {delivery_policy}")
    if not recompute and "eligible" in row:
        raw_eligible = row.get("eligible")
        if isinstance(raw_eligible, str):
            raw_eligible = raw_eligible.strip().lower() in {"1", "true", "yes", "accepted"}
        if not bool(raw_eligible):
            return False
    if str(row.get("resolution_status") or "").strip() != "Accepted":
        return False
    relevance = str(row.get("berlin_relevance") or "").strip()
    if relevance and relevance != "Confirmed" and not (delivery_policy == "personal" and relevance == "Probable"):
        return False
    if ("verified_company_domain" in row or "domain" in row) and not str(row.get("verified_company_domain") or row.get("domain") or "").strip():
        return False
    return True


def _resolve_under_root(root: Path, path: Path) -> Path:
    root = root.resolve()
    resolved = path if path.is_absolute() else root / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"campaign config must remain under repository root: {resolved}") from exc
    return resolved


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"campaign field must be a non-empty string: {field}")
    return value.strip()


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    version: str
    target_count: int
    qualification: dict[str, Any]
    input_bindings: dict[str, str]
    lanes: tuple[str, ...]
    adapter_policy: dict[str, Any]
    delivery_policy: str
    normalized: dict[str, Any]
    normalized_json: str
    sha256: str
    path: Path

    @property
    def relative_path(self) -> str:
        return self.path.as_posix()

    def manifest_record(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "version": self.version,
            "path": self.relative_path,
            "sha256": self.sha256,
            "normalized": self.normalized,
            "delivery_policy": self.delivery_policy,
        }


@dataclass(frozen=True)
class AdmittedWorkItem:
    run_id: str
    campaign_id: str
    company_id: str
    company_name: str
    trusted_domain: str
    location: str
    lane: str
    scope_version: str
    scope_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "campaign_id": self.campaign_id,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "trusted_domain": self.trusted_domain,
            "location": self.location,
            "lane": self.lane,
            "scope": f"{self.lane}:{self.company_id}",
            "scope_version": self.scope_version,
            "scope_hash": self.scope_hash,
        }


def admit_work_item(
    row: Mapping[str, object],
    run_id: str,
    campaign_id: str,
    lane: str,
    *,
    require_trusted_identity: bool = False,
    require_confirmed_location: bool = True,
    required_location_evidence: str | None = None,
) -> AdmittedWorkItem:
    company_id = str(row.get("company_id") or "").strip()
    if not company_id:
        raise ValueError("shortlist row lacks company_id")
    trusted_value = str(row.get("verified_company_domain") or "").strip()
    if require_trusted_identity and not trusted_value:
        raise ValueError(f"shortlist company lacks trusted domain: {company_id}")
    trusted_domain = trusted_value or str(row.get("domain") or "").strip()
    location = str(row.get("city") or "").strip()
    if require_trusted_identity and require_confirmed_location and not location:
        raise ValueError(f"shortlist company lacks confirmed city: {company_id}")
    if required_location_evidence and str(row.get("berlin_relevance") or "").strip() != required_location_evidence:
        raise ValueError(f"shortlist company lacks {required_location_evidence.lower()} location evidence: {company_id}")
    if not trusted_domain:
        raise ValueError(f"shortlist company lacks domain: {company_id}")
    if not location:
        location = "Unknown"
    trusted_domain = trusted_domain.lower().removeprefix("www.")
    scope_version = "admitted-work-item-v1"
    scope = {
        "run_id": str(run_id),
        "campaign_id": str(campaign_id),
        "company_id": company_id,
        "company_name": str(row.get("company_name") or "").strip(),
        "trusted_domain": trusted_domain,
        "location": location,
        "lane": str(lane),
        "scope_version": scope_version,
    }
    normalized = json.dumps(scope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return AdmittedWorkItem(**scope, scope_hash=hashlib.sha256(normalized.encode("utf-8")).hexdigest())


def load_campaign_spec(root: Path, path: Path) -> CampaignSpec:
    resolved = _resolve_under_root(root, path)
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"campaign config is not valid JSON: {resolved}") from exc
    if not isinstance(raw, dict):
        raise ValueError("campaign config must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"required campaign fields missing: {', '.join(missing)}")

    campaign_id = _require_text(raw["campaign_id"], "campaign_id")
    version = _require_text(raw["version"], "version")
    target_count = raw["target_count"]
    if not isinstance(target_count, int) or isinstance(target_count, bool) or target_count <= 0:
        raise ValueError("campaign target_count must be a positive integer")
    qualification = raw["qualification"]
    input_bindings = raw["input_bindings"]
    lanes = raw["lanes"]
    adapter_policy = raw["adapter_policy"]
    if not isinstance(qualification, dict):
        raise ValueError("campaign qualification must be an object")
    if not isinstance(input_bindings, dict) or not input_bindings:
        raise ValueError("campaign input_bindings must be a non-empty object")
    if any(not isinstance(key, str) or not isinstance(value, str) or not value.strip() for key, value in input_bindings.items()):
        raise ValueError("campaign input_bindings must map names to non-empty strings")
    if not isinstance(lanes, list) or not lanes or any(not isinstance(lane, str) or not lane.strip() for lane in lanes):
        raise ValueError("campaign lanes must be a non-empty list of strings")
    if len(set(lanes)) != len(lanes):
        raise ValueError("campaign lanes must be unique")
    if not isinstance(adapter_policy, dict):
        raise ValueError("campaign adapter_policy must be an object")
    delivery_policy = str(raw.get("delivery_policy") or "strict").strip().lower()
    if delivery_policy not in DELIVERY_POLICIES:
        raise ValueError(f"campaign delivery_policy must be one of: {', '.join(sorted(DELIVERY_POLICIES))}")

    normalized = _normalize(raw)
    normalized_json = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()
    return CampaignSpec(
        campaign_id=campaign_id,
        version=version,
        target_count=target_count,
        qualification=qualification,
        input_bindings={str(key): str(value) for key, value in input_bindings.items()},
        lanes=tuple(str(lane) for lane in lanes),
        adapter_policy=adapter_policy,
        delivery_policy=delivery_policy,
        normalized=normalized,
        normalized_json=normalized_json,
        sha256=digest,
        path=resolved.relative_to(root.resolve()),
    )
