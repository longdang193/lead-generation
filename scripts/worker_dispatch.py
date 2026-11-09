from __future__ import annotations

import json
import hashlib
import os
import signal
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import jsonschema

from dispatch_contracts import validate_lane_output
from action_lifecycle import admit_action as admit_lifecycle_action, canonical_request_hash, read_lifecycle, reject_result, replay_lifecycle, settle_action, validate_result as validate_lifecycle_result
from action_receipts import canonical_json
from lead_contract import candidate_claim_id, candidate_sha256, claim_requirements_met
from typed_contracts import ActionReceipt, NativeActionRequest, WorkerResult


TERMINAL = {"succeeded", "failed", "cancelled", "timed_out"}
RESEARCH_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))
RESEARCH_VALIDATOR = jsonschema.Draft202012Validator(RESEARCH_SCHEMA)


def _fingerprint(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _execution_fingerprints(item: dict[str, object], run_id: str, lane: str) -> dict[str, str]:
    identity_fields = (
        "campaign_id", "company_id", "scope", "scope_version", "scope_hash",
        "trusted_domain", "location", "adapter", "adapter_capability",
        "profile", "worker_profile", "provider", "provider_status",
        "input_fingerprint", "claims_path", "executable", "adapter_args",
        "head_sha", "campaign_sha256", "input_hashes", "verifier_profile",
    )
    identity = {field: item.get(field) for field in identity_fields if field in item}
    identity.update({"run_id": run_id, "lane": lane})
    return {
        "execution": _fingerprint(identity),
        "adapter": _fingerprint({"adapter": item.get("adapter") or item.get("adapter_capability"), "profile": item.get("profile") or item.get("worker_profile")}),
        "provider": _fingerprint({"provider": item.get("provider"), "provider_status": item.get("provider_status")}),
        "input": _fingerprint({key: item.get(key) for key in ("campaign_id", "company_id", "trusted_domain", "location", "scope", "scope_version", "scope_hash", "input_fingerprint", "claims_path") if key in item}),
    }


@dataclass(frozen=True)
class NativeExecutorConfig:
    executable: str
    profile: str
    timeout_seconds: int = 120
    max_retries: int = 1
    max_workers: int = 3
    adapter_args: tuple[str, ...] = ()
    timeout_retries: int = 1


class DispatchBudget:
    def __init__(self, deadline_seconds: int, max_attempts: int, reserved_attempts: int = 0) -> None:
        if deadline_seconds <= 0 or max_attempts <= 0:
            raise ValueError("dispatch budget must be positive")
        if reserved_attempts < 0 or reserved_attempts > max_attempts:
            raise ValueError("reserved dispatch attempts must be between zero and the total budget")
        self.deadline = time.monotonic() + deadline_seconds
        self.max_attempts = max_attempts
        self.remaining_attempts = max_attempts
        self.reserved_attempts = reserved_attempts
        self.attempted_attempts = 0
        self.retried_attempts = 0
        self.timed_out_attempts = 0
        self.reused_terminal_outputs = 0
        self.reserve_backfill_attempts = 0
        self._lock = threading.Lock()

    def remaining_seconds(self) -> float:
        return max(0.0, self.deadline - time.monotonic())

    def reserve_attempt(self) -> bool:
        with self._lock:
            if self.remaining_attempts <= self.reserved_attempts or self.remaining_seconds() <= 0:
                return False
            self.remaining_attempts -= 1
            self.attempted_attempts += 1
            return True

    def release_attempt(self) -> None:
        with self._lock:
            self.remaining_attempts += 1
            self.attempted_attempts = max(0, self.attempted_attempts - 1)

    def record_retry(self) -> None:
        with self._lock:
            self.retried_attempts += 1

    def record_timeout(self) -> None:
        with self._lock:
            self.timed_out_attempts += 1

    def record_reuse(self) -> None:
        with self._lock:
            self.reused_terminal_outputs += 1

    def release_reserved_attempts(self) -> None:
        with self._lock:
            self.reserve_backfill_attempts += self.reserved_attempts
            self.reserved_attempts = 0

    def reconciliation(self) -> dict[str, object]:
        with self._lock:
            return {
                "attempted": self.attempted_attempts,
                "retried": self.retried_attempts,
                "timed_out": self.timed_out_attempts,
                "verifier_reserved": self.reserved_attempts,
                "reserve_backfill": self.reserve_backfill_attempts,
                "reused": self.reused_terminal_outputs,
                "remaining": max(0, self.remaining_attempts - self.reserved_attempts),
                "remaining_seconds": self.remaining_seconds(),
            }


def admit_research_action(request: NativeActionRequest | dict[str, object], budget: DispatchBudget | None = None, root: Path | None = None, manifest_path: Path | None = None) -> NativeActionRequest:
    """Validate a native action and optionally reserve one shared attempt."""

    admitted = request if isinstance(request, NativeActionRequest) else NativeActionRequest.model_validate(request)
    reserved = False
    if budget is not None and admitted.budget_units:
        if not budget.reserve_attempt():
            raise ValueError("shared dispatch budget exhausted")
        reserved = True
    try:
        if root is not None and manifest_path is not None:
            admitted = admit_lifecycle_action(root, admitted, manifest_path)
    except Exception:
        if reserved:
            budget.release_attempt()
        raise
    return admitted


def record_worker_result(result: WorkerResult | dict[str, object], root: Path | None = None) -> WorkerResult:
    if root is not None:
        return validate_lifecycle_result(root, result)
    return result if isinstance(result, WorkerResult) else WorkerResult.model_validate(result)

def settle_action_receipt(root: Path, receipt: ActionReceipt | dict[str, object]) -> ActionReceipt:
    return settle_action(root, receipt)


def _lifecycle_request(root: Path, manifest_path: Path, item: dict[str, object], run_id: str, lane: str, attempt: int) -> NativeActionRequest:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    authorization = manifest.get("authorization") if isinstance(manifest.get("authorization"), dict) else {}
    profile_versions = authorization.get("profile_versions") if isinstance(authorization.get("profile_versions"), dict) else {}
    action_id = f"{lane}:{item['company_id']}"
    request: dict[str, object] = {
        "run_id": run_id,
        "action_id": action_id,
        "attempt_id": f"{action_id}:attempt-{attempt}",
        "company_id": str(item["company_id"]),
        "action_type": lane,
        "scope": str(item.get("scope") or f"{lane}:{item['company_id']}"),
        "contract_version": str(authorization.get("contract_version") or "1"),
        "strategy_version": str(authorization.get("strategy_version") or "1"),
        "profile_version": str(profile_versions.get(lane) or f"{lane}-v1"),
        "idempotency_key": f"{action_id}/attempt-{attempt}",
        "budget_units": 1,
        "provenance": {
            "campaign_id": str(authorization.get("campaign_id") or item.get("campaign_id") or "legacy"),
            "campaign_version": str(authorization.get("campaign_version") or item.get("campaign_version") or "legacy"),
            "scope_version": str(authorization.get("scope_version") or item.get("scope_version") or "native-v1"),
        },
    }
    request["request_hash"] = canonical_request_hash(request)
    return NativeActionRequest.model_validate(request)


def _settle_lifecycle_attempt(root: Path, request: NativeActionRequest, *, status: str, result_payload: dict[str, object], artifact: dict[str, str] | None = None, validation_errors: list[str] | None = None) -> None:
    result_hash = hashlib.sha256(canonical_json(result_payload).encode("utf-8")).hexdigest()
    if status == "Rejected":
        rejected = reject_result(root, request, validation_errors or ["worker result rejected"], raw_result=result_payload, artifact_hash=(artifact or {}).get("sha256"), provenance={"source": "native_dispatch"})
        result_hash = rejected.result_hash
    else:
        worker_result = WorkerResult(
            run_id=request.run_id,
            action_id=request.action_id,
            attempt_id=request.attempt_id,
            company_id=request.company_id,
            status=status,
            result=result_payload,
            artifact=artifact,
            result_hash=result_hash,
            provenance={"source": "native_dispatch"},
        )
        validated = validate_lifecycle_result(root, worker_result)
        result_hash = validated.result_hash
    settle_action(root, {
        **request.model_dump(),
        "result_hash": result_hash,
        "artifact_hash": (artifact or {}).get("sha256"),
        "terminal_status": status,
        "validation_errors": validation_errors or [],
        "budget_requested": request.budget_units,
        "budget_settled": request.budget_units,
        "coverage_delta": {},
        "provenance": {"source": "native_dispatch"},
        "created_at": datetime.now(timezone.utc),
    })

def _terminal(status: str) -> str:
    if status not in TERMINAL:
        raise ValueError(f"invalid terminal worker status: {status}")
    return status


def _terminal_evidence_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta.json")


def _write_terminal_evidence(path: Path, item: dict[str, object], run_id: str, lane: str) -> None:
    output_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence: dict[str, object] = {
        "run_id": run_id,
        "lane": lane,
        "company_id": item["company_id"],
        "output_sha256": output_sha256,
        "payload_sha256": output_sha256,
        "fingerprints": _execution_fingerprints(item, run_id, lane),
    }
    claims_path = item.get("claims_path")
    if lane == "verifier" and claims_path:
        claims_file = Path(str(claims_path))
        if claims_file.exists():
            evidence["claims_input_sha256"] = hashlib.sha256(claims_file.read_bytes()).hexdigest()
    _terminal_evidence_path(path).write_text(json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8")


def _valid_terminal_evidence(path: Path, item: dict[str, object], run_id: str, lane: str) -> bool:
    try:
        evidence = json.loads(_terminal_evidence_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(evidence, dict):
        return False
    expected = {"run_id": run_id, "lane": lane, "company_id": item["company_id"]}
    if any(evidence.get(field) != value for field, value in expected.items()):
        return False
    if evidence.get("fingerprints") != _execution_fingerprints(item, run_id, lane):
        return False
    output_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if evidence.get("payload_sha256") != output_sha256:
        return False
    if lane == "verifier":
        claims_path = Path(str(item.get("claims_path") or ""))
        if not claims_path.exists() or evidence.get("claims_input_sha256") != hashlib.sha256(claims_path.read_bytes()).hexdigest():
            return False
    return evidence.get("output_sha256") == output_sha256


def _valid_terminal_output(path: Path, item: dict[str, object], run_id: str, lane: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    return _valid_worker_payload(payload, item, run_id, lane) and _valid_terminal_evidence(path, item, run_id, lane)


def _valid_worker_payload(payload: dict[str, object], item: dict[str, object], run_id: str, lane: str) -> bool:
    if lane == "verifier":
        return _valid_verifier_payload(payload, item, run_id)
    research_run = payload.get("research_run", payload)
    if not isinstance(research_run, dict):
        return False
    try:
        RESEARCH_VALIDATOR.validate(research_run)
    except jsonschema.ValidationError:
        return False
    expected = {
        "run_id": f"{run_id}:{lane}:{item['company_id']}",
        "campaign_id": item.get("campaign_id", "legacy"),
        "company_id": item["company_id"],
        "scope": item.get("scope"),
        "scope_version": item.get("scope_version"),
        "scope_hash": item.get("scope_hash"),
    }
    claims = payload.get("claims", [])
    if not all(research_run.get(field) == value for field, value in expected.items()):
        return False
    if research_run.get("record_type") != "ResearchRun" or research_run.get("status") != "Completed":
        return False
    if research_run.get("provider_status") != "Available" or not isinstance(research_run.get("attempts"), list) or not research_run.get("attempts"):
        return False
    if not isinstance(claims, list):
        return False
    for claim in claims:
        if not isinstance(claim, dict) or not claim_requirements_met(claim)[0] or claim.get("candidate_claim_id") != candidate_claim_id(claim) or claim.get("candidate_sha256") != candidate_sha256(claim):
            return False
    return True


def _valid_verifier_payload(payload: dict[str, object], item: dict[str, object], run_id: str) -> bool:
    expected = {
        "run_id": run_id,
        "lane": "verifier",
        "campaign_id": item.get("campaign_id", "legacy"),
        "company_id": item["company_id"],
        "scope": item.get("scope"),
        "scope_version": item.get("scope_version"),
        "scope_hash": item.get("scope_hash"),
    }
    if any(payload.get(field) != value for field, value in expected.items()):
        return False
    decisions = payload.get("decisions")
    claims_path = Path(str(item.get("claims_path") or ""))
    if not isinstance(decisions, list) or any(not isinstance(decision, dict) for decision in decisions) or not claims_path.exists():
        return False
    try:
        if payload.get("claims_input_sha256") != hashlib.sha256(claims_path.read_bytes()).hexdigest():
            return False
        expected_claims: dict[str, str] = {}
        for line in claims_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            claim = json.loads(line)
            if not isinstance(claim, dict):
                return False
            claim_id = str(claim.get("candidate_claim_id") or "")
            claim_hash = str(claim.get("candidate_sha256") or "")
            if not claim_id or not claim_hash or claim_id in expected_claims:
                return False
            expected_claims[claim_id] = claim_hash
        seen: set[str] = set()
        for decision in decisions:
            claim_id = str(decision.get("candidate_claim_id") or "")
            if claim_id in seen or claim_id not in expected_claims or str(decision.get("candidate_sha256") or "") != expected_claims[claim_id]:
                return False
            seen.add(claim_id)
        return seen == set(expected_claims)
    except (OSError, json.JSONDecodeError):
        return False


def _next_attempt_number(root: Path, run_id: str, action_id: str) -> int:
    try:
        actions = replay_lifecycle(root, run_id).get("actions", [])
    except (OSError, ValueError):
        return 1
    attempts = []
    for action in actions:
        if action.get("action_id") == action_id:
            raw = str(action.get("attempt_id") or "")
            try:
                attempts.append(int(raw.rsplit("-", 1)[1]))
            except (IndexError, ValueError):
                continue
    return max(attempts, default=0) + 1


def _reconcile_interrupted_attempts(root: Path, run_id: str, item: dict[str, object], lane: str) -> None:
    action_id = f"{lane}:{item['company_id']}"
    events = read_lifecycle(root, run_id)
    admitted = {
        event.attempt_id: event
        for event in events
        if event.event_type == "admitted" and event.action_id == action_id
    }
    for attempt_id, admission in admitted.items():
        attempt_events = [event for event in events if event.action_id == action_id and event.attempt_id == attempt_id]
        if any(event.event_type == "settled" for event in attempt_events):
            continue
        result_event = next((event for event in attempt_events if event.event_type in {"result_validated", "result_rejected"}), None)
        request = NativeActionRequest.model_validate({
            "run_id": admission.run_id,
            "action_id": admission.action_id,
            "attempt_id": admission.attempt_id,
            "company_id": admission.company_id,
            "action_type": admission.action_type,
            "scope": admission.scope,
            "contract_version": admission.contract_version,
            "strategy_version": admission.strategy_version,
            "profile_version": admission.profile_version,
            "idempotency_key": admission.idempotency_key,
            "request_hash": admission.request_hash,
            "budget_units": admission.budget_units,
            "provenance": admission.provenance,
        })
        if result_event is None:
            result_payload = {"failure_class": "interrupted_attempt"}
            result_hash = hashlib.sha256(canonical_json(result_payload).encode("utf-8")).hexdigest()
            validated = validate_lifecycle_result(root, WorkerResult(
                run_id=request.run_id,
                action_id=request.action_id,
                attempt_id=request.attempt_id,
                company_id=request.company_id,
                status="Unavailable",
                result=result_payload,
                result_hash=result_hash,
                provenance={"source": "native_dispatch", "reason": "interrupted_attempt"},
            ))
            result_event = None
            result_hash = validated.result_hash
            terminal_status = "Unavailable"
            artifact_hash = None
            validation_errors: list[str] = []
            coverage_delta: dict[str, object] = {}
            provenance = validated.provenance
        else:
            result_hash = result_event.result_hash
            terminal_status = result_event.terminal_status
            artifact_hash = result_event.artifact_hash
            validation_errors = result_event.validation_errors
            coverage_delta = result_event.coverage_delta if terminal_status in {"Completed", "Partial"} else {}
            provenance = result_event.provenance
        settle_action(root, {
            **request.model_dump(),
            "result_hash": result_hash,
            "artifact_hash": artifact_hash,
            "terminal_status": terminal_status,
            "validation_errors": validation_errors,
            "budget_requested": request.budget_units,
            "budget_settled": request.budget_units,
            "coverage_delta": coverage_delta,
            "provenance": provenance,
            "created_at": datetime.now(timezone.utc),
        })


def _has_completed_lifecycle(root: Path, run_id: str, item: dict[str, object], lane: str) -> bool:
    try:
        actions = replay_lifecycle(root, run_id).get("actions", [])
    except (OSError, ValueError):
        return False
    expected_action_id = f"{lane}:{item['company_id']}"
    expected_scope = str(item.get("scope") or expected_action_id)
    return any(
        action.get("action_id") == expected_action_id
        and action.get("company_id") == str(item["company_id"])
        and action.get("action_type") == lane
        and action.get("scope") == expected_scope
        and action.get("status") == "Completed"
        and action.get("settled") is True
        for action in actions
    )


def split_material_gap_queue(
    queue: Iterable[dict[str, object]],
    run_id: str,
    lane: str,
    output_dir: Path,
    config: NativeExecutorConfig | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pending: list[dict[str, object]] = []
    reused: list[dict[str, object]] = []
    for item in queue:
        company_id = str(item["company_id"])
        output_path = output_dir / f"{lane}-{company_id}.json"
        cache_item = dict(item)
        if config is not None:
            cache_item.update({"profile": config.profile, "executable": config.executable, "adapter_args": list(config.adapter_args)})
        if not output_path.exists() or not _valid_terminal_output(output_path, cache_item, run_id, lane):
            pending.append(item)
            continue
        reused.append({
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "status": "succeeded",
            "attempts": 0,
            "reused_terminal": True,
            "exit_code": 0,
            "duration_seconds": 0,
            "output_path": output_path.as_posix(),
            "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        })
    return pending, reused


def dispatch_native_lane(
    queue: Iterable[dict[str, object]],
    run_id: str,
    lane: str,
    output_dir: Path,
    config: NativeExecutorConfig,
    *,
    command_builder: Callable[[dict[str, object], Path, NativeExecutorConfig], list[str]] | None = None,
    budget: DispatchBudget | None = None,
    lifecycle_root: Path | None = None,
    manifest_path: Path | None = None,
) -> list[dict[str, object]]:
    """Run one bounded native lane with explicit worker terminal states.

    The worker receives JSON queue item, run ID, lane, profile, and output path
    arguments. It may only write beneath output_dir; the controller records exit
    code, attempts, timeout/cancellation, and output hash for reconciliation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    def run_one(item: dict[str, object]) -> dict[str, object]:
        company_id = str(item["company_id"])
        item_output = output_dir / f"{lane}-{company_id}.json"
        cache_item = dict(item)
        cache_item.update({"profile": config.profile, "executable": config.executable, "adapter_args": list(config.adapter_args)})
        if lifecycle_root is not None and manifest_path is not None:
            _reconcile_interrupted_attempts(lifecycle_root, run_id, item, lane)
        reusable = item_output.exists() and _valid_terminal_output(item_output, cache_item, run_id, lane)
        if reusable and lifecycle_root is not None and manifest_path is not None:
            reusable = _has_completed_lifecycle(lifecycle_root, run_id, item, lane)
        if reusable:
            if budget is not None:
                budget.record_reuse()
            return {
                "run_id": run_id,
                "lane": lane,
                "company_id": company_id,
                "status": "succeeded",
                "attempts": 0,
                "reused_terminal": True,
                "exit_code": 0,
                "duration_seconds": 0,
                "output_path": item_output.as_posix(),
                "output_sha256": hashlib.sha256(item_output.read_bytes()).hexdigest(),
                "capacity": budget.reconciliation() if budget is not None else None,
            }
        if item_output.exists():
            item_output.unlink()
        if _terminal_evidence_path(item_output).exists():
            _terminal_evidence_path(item_output).unlink()
        attempts = 0
        status = "failed"
        terminal_failure_class: str | None = None
        exit_code: int | None = None
        started = time.time()
        attempt_history: list[dict[str, object]] = []
        attempt_offset = _next_attempt_number(lifecycle_root, run_id, f"{lane}:{company_id}") - 1 if lifecycle_root is not None and manifest_path is not None else 0
        for attempts in range(1, config.max_retries + 2):
            attempt_number = attempt_offset + attempts
            lifecycle_request = _lifecycle_request(lifecycle_root, manifest_path, item, run_id, lane, attempt_number) if lifecycle_root is not None and manifest_path is not None else None
            try:
                if lifecycle_request is not None:
                    admit_research_action(lifecycle_request, budget=budget, root=lifecycle_root, manifest_path=manifest_path)
                elif budget is not None and not budget.reserve_attempt():
                    raise ValueError("shared dispatch budget exhausted")
            except ValueError as exc:
                attempts -= 1
                terminal_failure_class = "budget_exhausted"
                attempt_history.append({"attempt": attempts + 1, "status": "budget_exhausted", "error": str(exc)})
                break
            if budget is not None and attempts > 1:
                budget.record_retry()
            attempt_output = output_dir / f".{lane}-{company_id}-attempt-{attempt_number}.json"
            if attempt_output.exists():
                attempt_output.unlink()
            attempt_command = command_builder(item, attempt_output, config) if command_builder else [
                config.executable,
                "--profile", config.profile,
                "--run-id", run_id,
                "--lane", lane,
                "--company-id", company_id,
                "--output", str(attempt_output),
            ]
            try:
                timeout_seconds = config.timeout_seconds
                if budget is not None:
                    remaining_seconds = budget.remaining_seconds()
                    if remaining_seconds <= 0:
                        status = "timed_out"
                        terminal_failure_class = "budget_exhausted"
                        if lifecycle_request is not None:
                            _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Unavailable", result_payload={"attempt": attempt_number, "failure_class": "deadline_expired"}, validation_errors=["deadline expired before worker launch"])
                        attempt_history.append({"attempt": attempt_number, "status": "budget_exhausted"})
                        break
                    timeout_seconds = min(timeout_seconds, max(0.1, remaining_seconds))
                completed = subprocess.run(attempt_command, check=False, timeout=timeout_seconds, cwd=output_dir.parent.parent.parent)
                exit_code = completed.returncode
                payload_valid = False
                if exit_code == 0 and attempt_output.exists():
                    try:
                        payload = json.loads(attempt_output.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        payload = None
                    payload_valid = isinstance(payload, dict) and _valid_worker_payload(payload, cache_item, run_id, lane)
                if payload_valid:
                    os.replace(attempt_output, item_output)
                    _write_terminal_evidence(item_output, cache_item, run_id, lane)
                    status = "succeeded"
                    if lifecycle_request is not None:
                        output_hash = hashlib.sha256(item_output.read_bytes()).hexdigest()
                        relative_output = item_output.resolve().relative_to(lifecycle_root.resolve()).as_posix()
                        _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Completed", result_payload={"output_path": relative_output, "output_sha256": output_hash}, artifact={"path": relative_output, "sha256": output_hash, "kind": "worker"})
                    attempt_history.append({"attempt": attempt_number, "status": status})
                    break
                if exit_code == 0 and attempt_output.exists() and not payload_valid:
                    if lifecycle_request is not None:
                        _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Rejected", result_payload={"output_path": str(attempt_output), "failure_class": "invalid_worker_output"}, validation_errors=["worker output does not satisfy the lane contract"])
                    status = "failed"
                    terminal_failure_class = "invalid_worker_output"
                    attempt_history.append({"attempt": attempt_number, "status": status, "failure_class": terminal_failure_class})
                    break
                status = "failed"
                if lifecycle_request is not None:
                    _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Failed", result_payload={"attempt": attempt_number, "exit_code": exit_code, "failure_class": item.get("failure_class") or "worker_failure"})
                attempt_history.append({"attempt": attempt_number, "status": status, "exit_code": exit_code})
                if item.get("failure_class") == "deterministic" or exit_code in {2, 64, 78}:
                    break
                continue
            except subprocess.TimeoutExpired:
                status = "timed_out"
                if budget is not None:
                    budget.record_timeout()
                if lifecycle_request is not None:
                    _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Unavailable", result_payload={"attempt": attempt_number, "failure_class": "timeout"})
                attempt_history.append({"attempt": attempt_number, "status": status})
                if attempts <= min(config.timeout_retries, config.max_retries):
                    continue
                break
            except KeyboardInterrupt:
                status = "cancelled"
                raise
            except OSError as exc:
                status = "failed"
                if lifecycle_request is not None:
                    _settle_lifecycle_attempt(lifecycle_root, lifecycle_request, status="Failed", result_payload={"attempt": attempt_number, "failure_class": "launch_error", "error": str(exc)})
                attempt_history.append({"attempt": attempt_number, "status": status, "failure_class": "deterministic"})
                break
            finally:
                if attempt_output.exists():
                    attempt_output.unlink()
        record: dict[str, object] = {
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "status": _terminal(status),
            "attempts": attempts,
            "exit_code": exit_code,
            "duration_seconds": round(time.time() - started, 3),
            "output_path": item_output.as_posix(),
            "failure_class": str(terminal_failure_class or item.get("failure_class") or ("timeout" if status == "timed_out" else "transient" if status == "failed" and attempts > 1 else "deterministic" if status == "failed" else "none")),
            "attempt_history": attempt_history,
        }
        if item_output.exists():
            record["output_sha256"] = hashlib.sha256(item_output.read_bytes()).hexdigest()
        if budget is not None:
            record["capacity"] = budget.reconciliation()
        return record

    items = list(queue)
    if config.max_workers <= 1 or len(items) <= 1:
        return [run_one(item) for item in items]
    with ThreadPoolExecutor(max_workers=max(1, config.max_workers)) as executor:
        futures = [executor.submit(run_one, item) for item in items]
        return [future.result() for future in futures]


def dispatch_fixture_lanes(queues: dict[str, list[dict[str, object]]], run_id: str, output_dir: Path) -> dict[str, list[dict[str, object]]]:
    """Deterministic local executor used by tests and provider-free probes."""
    results: dict[str, list[dict[str, object]]] = {}
    for lane, queue in queues.items():
        lane_dir = output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        lane_results: list[dict[str, object]] = []
        for item in reversed(queue):
            company_id = str(item["company_id"])
            research_run = {
                "record_type": "ResearchRun",
                "run_id": f"{run_id}:{lane}:{company_id}",
                "company_id": company_id,
                "research_type": lane,
                "source": "fixture",
                "campaign_id": item.get("campaign_id", "legacy"),
                "company_name": item.get("company_name", ""),
                "trusted_domain": item.get("trusted_domain", ""),
                "location": item.get("location", "Unknown"),
                "scope": item.get("scope", f"{lane}:{company_id}"),
                "status": "Completed",
                "started_at": "2026-11-08T00:00:00+00:00",
                "completed_at": "2026-11-08T00:00:01+00:00",
                "result_count": 0,
                "truncated": False,
                "provider_status": "Available",
                "adapter_capability": "replay",
                "scope_version": item.get("scope_version", "fixture-v1"),
                "scope_hash": item.get("scope_hash", "0" * 64),
                "attempts": [{"attempt_id": f"{run_id}:{lane}:{company_id}:1", "query_or_source": "fixture", "status": "Completed", "truncated": False}],
            }
            domain = str(item.get("trusted_domain") or "example.invalid")
            source_url = f"https://{domain}/"
            claims: list[dict[str, object]] = []
            if lane == "portfolio":
                claims.extend([
                    {"claim_type": "service_fit", "claim_value": "Confirmed", "source_url": source_url + "services", "source_kind": "official", "evidence_excerpt": "Hausverwaltung und Immobilienverwaltung für Wohnobjekte in Berlin.", "published_at": None},
                    {"claim_type": "residential_weg", "claim_value": "Confirmed", "source_url": source_url + "services", "source_kind": "official", "evidence_excerpt": "Verwaltung von Wohnungseigentümergemeinschaften und Wohnimmobilien.", "published_at": None},
                    {"claim_type": "berlin_relevance", "claim_value": "Confirmed", "source_url": source_url, "source_kind": "official", "evidence_excerpt": "Hausverwaltung für Eigentümer in Berlin.", "published_at": None},
                    {"claim_type": "portfolio_size", "claim_value": 1000, "unit": "units", "scope": "managed residential portfolio", "as_of_date": "2026-10-01", "source_url": source_url + "portfolio", "source_kind": "official", "evidence_excerpt": "The company manages approximately 1,000 residential units in Berlin.", "published_at": None},
                ])
            elif lane == "signals":
                claims.extend([
                    {"claim_type": "buying_signal", "claim_value": "Strong", "source_url": source_url + "news", "source_kind": "official", "evidence_excerpt": "A current Berlin procurement notice names the company as an active participant.", "published_at": "2026-10-01"},
                    {"claim_type": "event", "claim_value": {"event_id": f"event-{company_id}", "publication_date": "2026-10-01", "deadline": "2026-12-01"}, "source_url": source_url + "news", "source_kind": "official", "evidence_excerpt": "A current Berlin procurement notice names the company as an active participant.", "published_at": "2026-10-01"},
                ])
            elif lane == "contacts":
                claims.append({"claim_type": "contact", "claim_value": "Anna Schmidt", "person_name": "Anna Schmidt", "role": "Geschäftsführung", "company_affiliation": str(item.get("company_name") or ""), "email": f"anna.schmidt@{domain}", "source_url": source_url + "contact", "source_kind": "official", "evidence_excerpt": "Anna Schmidt — Geschäftsführung", "published_at": None})
            normalized_claims: list[dict[str, object]] = []
            for claim in claims:
                normalized = {
                    "record_type": "EvidenceClaim",
                    "candidate_claim_id": candidate_claim_id({"company_id": company_id, **claim}),
                    "company_id": company_id,
                    "claim_type": claim["claim_type"],
                    "claim_value": claim["claim_value"],
                    "unit": claim.get("unit"),
                    "scope": claim.get("scope"),
                    "source_url": claim["source_url"],
                    "source_domain": domain,
                    "source_kind": claim["source_kind"],
                    "evidence_excerpt": claim["evidence_excerpt"],
                    "retrieved_at": "2026-11-08T00:00:00+00:00",
                    "published_at": claim.get("published_at"),
                    "as_of_date": claim.get("as_of_date"),
                    "account_relationship": "direct",
                    "confidence": "high",
                    "research_run_id": research_run["run_id"],
                    "candidate_status": "Candidate",
                    "person_name": claim.get("person_name"),
                    "role": claim.get("role"),
                    "company_affiliation": claim.get("company_affiliation"),
                    "email": claim.get("email"),
                    "verifier_run_id": None,
                    "verified_at": None,
                }
                normalized["candidate_sha256"] = candidate_sha256(normalized)
                normalized_claims.append(normalized)
            path = lane_dir / f"{company_id}.json"
            path.write_text(json.dumps({"research_run": research_run, "claims": normalized_claims}, sort_keys=True) + "\n", encoding="utf-8")
            lane_results.append({
                "run_id": run_id,
                "lane": lane,
                "company_id": company_id,
                "status": "succeeded",
                "research_run_id": research_run["run_id"],
                "output_path": path.as_posix(),
                "output_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
                "attempts": 1,
            })
        results[lane] = lane_results
    return results


def reconcile_lane_outputs(records: list[dict[str, object]], queue: list[dict[str, object]], run_id: str, lane: str, *, allow_partial: bool = False) -> None:
    validate_lane_output(records, queue, run_id, lane)
    if not allow_partial and any(str(record.get("status")) != "succeeded" for record in records):
        raise ValueError(f"lane {lane} has unsuccessful terminal output")
    expected = {str(item["company_id"]): item for item in queue}
    for record in records:
        if allow_partial and str(record.get("status")) != "succeeded":
            continue
        output_path = Path(str(record.get("output_path") or ""))
        if not output_path.exists():
            raise ValueError(f"lane output is missing: {output_path}")
        actual_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        if record.get("output_sha256") != actual_hash:
            raise ValueError(f"lane output hash mismatch: {output_path}")
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"lane output is not valid JSON: {output_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"lane output must be a JSON object: {output_path}")
        item = expected[str(record["company_id"])]
        if lane == "verifier":
            expected_metadata = {
                "run_id": run_id,
                "lane": lane,
                "campaign_id": item.get("campaign_id", "legacy"),
                "company_id": item["company_id"],
                "scope": item.get("scope"),
                "scope_version": item.get("scope_version"),
                "scope_hash": item.get("scope_hash"),
            }
            for field, expected_value in expected_metadata.items():
                if payload.get(field) != expected_value:
                    raise ValueError(f"verifier output scope mismatch for {output_path}: {field}")
            decisions = payload.get("decisions", [])
            if not isinstance(decisions, list) or any(not isinstance(decision, dict) for decision in decisions):
                raise ValueError(f"verifier output decisions are not objects: {output_path}")
            claims_path = Path(str(item.get("claims_path") or ""))
            if not claims_path.exists():
                raise ValueError(f"verifier claims input is missing: {claims_path}")
            claims_hash = hashlib.sha256(claims_path.read_bytes()).hexdigest()
            if payload.get("claims_input_sha256") != claims_hash:
                raise ValueError(f"verifier claims input hash mismatch: {claims_path}")
            expected_claims: dict[str, str] = {}
            for line in claims_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                claim = json.loads(line)
                if not isinstance(claim, dict):
                    raise ValueError(f"verifier claims input is not an object: {claims_path}")
                claim_id = str(claim.get("candidate_claim_id") or "")
                claim_hash = str(claim.get("candidate_sha256") or "")
                if not claim_id or not claim_hash or claim_id in expected_claims:
                    raise ValueError(f"verifier claims input has invalid or duplicate claim: {claims_path}")
                expected_claims[claim_id] = claim_hash
            seen_decisions: set[str] = set()
            for decision in decisions:
                claim_id = str(decision.get("candidate_claim_id") or "")
                if claim_id in seen_decisions:
                    raise ValueError(f"verifier output has duplicate decision: {claim_id}")
                if claim_id not in expected_claims:
                    raise ValueError(f"verifier output contains foreign decision: {claim_id}")
                if str(decision.get("candidate_sha256") or "") != expected_claims[claim_id]:
                    raise ValueError(f"verifier output hash mismatch: {claim_id}")
                seen_decisions.add(claim_id)
            missing_decisions = sorted(set(expected_claims) - seen_decisions)
            if missing_decisions:
                raise ValueError(f"verifier output missing decisions: {', '.join(missing_decisions)}")
            continue
        research_run = payload.get("research_run", payload)
        if not isinstance(research_run, dict):
            raise ValueError(f"worker output lacks research_run: {output_path}")
        try:
            RESEARCH_VALIDATOR.validate(research_run)
        except jsonschema.ValidationError as exc:
            raise ValueError(f"worker research_run schema invalid: {output_path}: {exc.message}") from exc
        expected_values = {
            "run_id": f"{run_id}:{lane}:{item['company_id']}",
            "campaign_id": item.get("campaign_id", "legacy"),
            "company_id": item["company_id"],
            "scope": item.get("scope"),
            "scope_version": item.get("scope_version"),
            "scope_hash": item.get("scope_hash"),
        }
        for field, expected_value in expected_values.items():
            if research_run.get(field) != expected_value:
                raise ValueError(f"worker output scope mismatch for {output_path}: {field}")
        claims = payload.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError(f"worker output claims are not objects: {output_path}")
        if any(not isinstance(claim, dict) for claim in claims) and not allow_partial:
            raise ValueError(f"worker output claims are not objects: {output_path}")
