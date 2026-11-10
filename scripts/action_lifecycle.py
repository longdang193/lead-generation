"""Authoritative, replayable lifecycle for native actions."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from action_receipts import append_receipt, canonical_json, replay_run
from capability_registry import authorize_capability
from run_manifest import load
from typed_contracts import ActionReceipt, LifecycleEvent, NativeActionRequest, WorkerResult


_THREAD_LOCK = threading.RLock()


def _safe_run_id(run_id: str) -> str:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a non-empty path-safe identifier")
    return run_id


def lifecycle_path(root: Path, run_id: str) -> Path:
    return root / "evidence" / "action_lifecycle" / f"{_safe_run_id(run_id)}.jsonl"


def lifecycle_snapshot_path(root: Path, run_id: str) -> Path:
    return lifecycle_path(root, run_id).with_suffix(".snapshot.json")


def _lock_path(root: Path, run_id: str) -> Path:
    return lifecycle_path(root, run_id).with_suffix(".lock")


@contextmanager
def _run_lock(root: Path, run_id: str) -> Iterator[None]:
    path = _lock_path(root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _THREAD_LOCK:
        with path.open("a+b") as handle:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                handle.write(b"0")
                handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _dump(event: LifecycleEvent) -> dict[str, Any]:
    return event.model_dump(mode="json", exclude_none=True)


def _read(path: Path) -> list[LifecycleEvent]:
    if not path.exists():
        return []
    events: list[LifecycleEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid lifecycle JSON at line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"lifecycle event at line {line_number} is not an object")
        events.append(LifecycleEvent.model_validate(value))
    return events


def _last_event_digest(path: Path) -> str | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - 8192))
        lines = handle.read().splitlines()
    if not lines:
        return None
    return hashlib.sha256(lines[-1]).hexdigest()


def _load_snapshot(root: Path, run_id: str) -> list[LifecycleEvent] | None:
    journal = lifecycle_path(root, run_id)
    snapshot_path = lifecycle_snapshot_path(root, run_id)
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
            return None
        if snapshot.get("journal_byte_offset") != journal.stat().st_size:
            return None
        events = snapshot.get("events")
        if not isinstance(events, list) or snapshot.get("event_count") != len(events):
            return None
        if snapshot.get("last_event_digest") != _last_event_digest(journal):
            return None
        return [LifecycleEvent.model_validate(value) for value in events]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _write_snapshot(root: Path, run_id: str, events: list[LifecycleEvent]) -> None:
    journal = lifecycle_path(root, run_id)
    snapshot_path = lifecycle_snapshot_path(root, run_id)
    payload = {
        "schema_version": 1,
        "journal_byte_offset": journal.stat().st_size,
        "event_count": len(events),
        "last_event_digest": _last_event_digest(journal),
        "events": [_dump(event) for event in events],
    }
    temporary = snapshot_path.with_name(snapshot_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(payload))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, snapshot_path)


def _state_events(root: Path, run_id: str) -> list[LifecycleEvent]:
    snapshot = _load_snapshot(root, run_id)
    return snapshot if snapshot is not None else _read(lifecycle_path(root, run_id))


def read_lifecycle(root: Path, run_id: str) -> list[LifecycleEvent]:
    return _read(lifecycle_path(root, run_id))


def _append_locked(root: Path, event: LifecycleEvent) -> None:
    events = _state_events(root, event.run_id)
    path = lifecycle_path(root, event.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(_dump(event)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    events.append(event)
    try:
        _write_snapshot(root, event.run_id, events)
    except OSError:
        pass


def _request_event(request: NativeActionRequest) -> LifecycleEvent:
    return LifecycleEvent(
        **request.model_dump(exclude_none=True),
        event_type="admitted",
        created_at=datetime.now(timezone.utc),
    )


def _manifest_budget(manifest_path: Path, run_id: str) -> int:
    manifest = load(manifest_path)
    if str(manifest.get("run_id") or "") != run_id:
        raise ValueError("run_id does not match manifest")
    sealed = manifest.get("execution_authorization")
    raw = sealed.get("budget_limit") if isinstance(sealed, dict) else manifest.get("budget_limit")
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ValueError("manifest budget_limit must be a nonnegative integer")
    return raw


def _validate_manifest_authorization(root: Path, manifest: dict[str, Any], request: NativeActionRequest) -> None:
    provenance = request.provenance
    capability = provenance.get("capability")
    provider = provenance.get("provider")
    if provider and not capability:
        raise ValueError("provider provenance requires capability provenance")
    if capability:
        authorize_capability(root, request.profile_name or "", capability, provider)
    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict):
        return
    accepted_company_ids = authorization.get("accepted_company_ids")
    if isinstance(accepted_company_ids, list) and request.company_id not in {str(value) for value in accepted_company_ids}:
        raise ValueError("company is outside the accepted company scope")
    allowed_action_types = authorization.get("allowed_action_types")
    if isinstance(allowed_action_types, list) and allowed_action_types and request.action_type not in {str(value) for value in allowed_action_types}:
        raise ValueError("action type is outside the admitted scope")
    scope_prefixes = authorization.get("scope_prefixes")
    if isinstance(scope_prefixes, dict):
        expected_prefix = scope_prefixes.get(request.action_type)
        if expected_prefix is not None:
            expected_scope = f"{expected_prefix}{request.company_id}"
            if request.scope != expected_scope:
                raise ValueError("request scope does not match manifest authorization")
    for request_key in ("contract_version", "strategy_version"):
        expected = authorization.get(request_key)
        if expected is not None and getattr(request, request_key) != str(expected):
            raise ValueError(f"request {request_key} does not match manifest authorization")
    profile_versions = authorization.get("profile_versions")
    if isinstance(profile_versions, dict):
        expected = profile_versions.get(request.action_type)
        if expected is not None and request.profile_version != str(expected):
            raise ValueError("request profile_version does not match manifest authorization")
    for request_key, manifest_key in (("campaign_id", "campaign_id"), ("campaign_version", "campaign_version"), ("scope_version", "scope_version")):
        expected = authorization.get(manifest_key)
        if expected is not None and provenance.get(request_key) != str(expected):
            raise ValueError(f"request {request_key} does not match manifest authorization")


def canonical_request_hash(request: NativeActionRequest | dict[str, object]) -> str:
    if isinstance(request, NativeActionRequest):
        validated = request
    else:
        payload = dict(request)
        payload.pop("request_hash", None)
        payload["request_hash"] = "0" * 64
        validated = NativeActionRequest.model_validate(payload)
    payload = validated.model_dump(exclude={"request_hash"}, exclude_none=True)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def admit_action(root: Path, request: NativeActionRequest | dict[str, object], manifest_path: Path) -> NativeActionRequest:
    validated = request if isinstance(request, NativeActionRequest) else NativeActionRequest.model_validate(request)
    if validated.request_hash != canonical_request_hash(validated):
        raise ValueError("request hash mismatch")
    with _run_lock(root, validated.run_id):
        manifest = load(manifest_path)
        if str(manifest.get("run_id") or "") != validated.run_id:
            raise ValueError("run_id does not match manifest")
        _validate_manifest_authorization(root, manifest, validated)
        events = _state_events(root, validated.run_id)
        admissions = [event for event in events if event.event_type == "admitted"]
        if validated.parent_action_id is not None:
            parent_settled = any(
                event.event_type == "settled"
                and event.action_id == validated.parent_action_id
                and event.company_id == validated.company_id
                for event in events
            )
            if not parent_settled:
                raise ValueError("parent action must be a settled action for the same company")
        for event in admissions:
            if event.action_id == validated.action_id and event.attempt_id == validated.attempt_id:
                expected = {
                    "parent_action_id": event.parent_action_id,
                    "company_id": event.company_id,
                    "action_type": event.action_type,
                    "scope": event.scope,
                    "contract_version": event.contract_version,
                    "strategy_version": event.strategy_version,
                    "profile_version": event.profile_version,
                    "idempotency_key": event.idempotency_key,
                    "request_hash": event.request_hash,
                    "budget_units": event.budget_units,
                    "provenance": event.provenance,
                }
                actual = validated.model_dump(exclude_none=True)
                if any(expected[key] != actual.get(key) for key in expected):
                    raise ValueError("conflicting duplicate action admission")
                return validated
            if event.idempotency_key == validated.idempotency_key:
                raise ValueError("conflicting duplicate action idempotency key")
        reserved = sum(event.budget_units for event in admissions)
        limit = _manifest_budget(manifest_path, validated.run_id)
        if reserved + validated.budget_units > limit:
            raise ValueError("action budget exhausted")
        _append_locked(root, _request_event(validated))
    return validated


def _artifact_path(root: Path, result: WorkerResult) -> tuple[str, str] | None:
    if result.artifact is None:
        return None
    path = Path(result.artifact.path)
    path = path if path.is_absolute() else root / path
    path = path.resolve()
    try:
        relative = path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("worker artifact path escapes repository root") from exc
    if not path.exists() or not path.is_file():
        raise ValueError("worker artifact is missing")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != result.artifact.sha256:
        raise ValueError("worker artifact hash is invalid or stale")
    return relative, actual


def _canonical_result_hash(result: WorkerResult) -> str:
    payload = canonical_json(result.result)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _raw_result_hash(raw_result: object) -> str:
    return hashlib.sha256(canonical_json(raw_result).encode("utf-8")).hexdigest()


def _validate_coverage_delta(admission: LifecycleEvent, terminal_status: str, coverage_delta: dict[str, Any]) -> None:
    if terminal_status not in {"Completed", "Partial"} and coverage_delta:
        raise ValueError("non-successful action cannot report coverage")
    if any(name != admission.action_type for name in coverage_delta):
        raise ValueError("coverage key does not match admitted action type")
    for name, value in coverage_delta.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"coverage value is invalid: {name}")


def validate_result(root: Path, result: WorkerResult | dict[str, object]) -> WorkerResult:
    validated = result if isinstance(result, WorkerResult) else WorkerResult.model_validate(result)
    if validated.validation_errors:
        raise ValueError("worker result validation failed: " + "; ".join(validated.validation_errors))
    if validated.result_hash != _canonical_result_hash(validated):
        raise ValueError("result hash mismatch")
    artifact = _artifact_path(root, validated)
    with _run_lock(root, validated.run_id):
        events = _state_events(root, validated.run_id)
        admission = next((event for event in events if event.event_type == "admitted" and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        if admission is None:
            raise ValueError("action is not admitted")
        if admission.company_id != validated.company_id:
            raise ValueError("result company does not match admission")
        existing = next((prior for prior in events if prior.event_type == "result_validated" and prior.action_id == validated.action_id and prior.attempt_id == validated.attempt_id), None)
        if existing is not None:
            if any((
                existing.company_id != validated.company_id,
                existing.result_hash != validated.result_hash,
                existing.terminal_status != validated.status,
                existing.provenance != validated.provenance,
                existing.artifact_path != (artifact[0] if artifact else None),
                existing.artifact_hash != (artifact[1] if artifact else None),
            )):
                raise ValueError("conflicting duplicate result validation")
            return validated
        if any(prior.event_type == "result_rejected" and prior.action_id == validated.action_id and prior.attempt_id == validated.attempt_id for prior in events):
            raise ValueError("conflicting result rejection")
        event = LifecycleEvent(
            run_id=validated.run_id,
            action_id=validated.action_id,
            attempt_id=validated.attempt_id,
            event_type="result_validated",
            company_id=validated.company_id,
            action_type=admission.action_type,
            scope=admission.scope,
            idempotency_key=admission.idempotency_key,
            contract_version=admission.contract_version,
            strategy_version=admission.strategy_version,
            profile_version=admission.profile_version,
            profile_name=admission.profile_name,
            skills=admission.skills,
            parent_action_id=admission.parent_action_id,
            request_hash=admission.request_hash,
            budget_units=admission.budget_units,
            result_hash=validated.result_hash,
            artifact_path=artifact[0] if artifact else None,
            artifact_hash=artifact[1] if artifact else None,
            terminal_status=validated.status,
            provenance=validated.provenance,
            created_at=datetime.now(timezone.utc),
        )
        _append_locked(root, event)
    return validated


def reject_result(
    root: Path,
    request: NativeActionRequest | dict[str, object],
    validation_errors: list[str],
    *,
    raw_result: object = None,
    artifact_hash: str | None = None,
    provenance: dict[str, str] | None = None,
) -> LifecycleEvent:
    admitted = request if isinstance(request, NativeActionRequest) else NativeActionRequest.model_validate(request)
    errors = [str(error) for error in validation_errors if str(error)]
    if not errors:
        raise ValueError("rejected result requires validation errors")
    result_hash = _raw_result_hash(raw_result if raw_result is not None else {"validation_errors": errors})
    event_provenance = dict(provenance or {})
    with _run_lock(root, admitted.run_id):
        events = _state_events(root, admitted.run_id)
        admission = next((event for event in events if event.event_type == "admitted" and event.action_id == admitted.action_id and event.attempt_id == admitted.attempt_id), None)
        if admission is None:
            raise ValueError("action is not admitted")
        if any(prior.event_type == "result_validated" and prior.action_id == admitted.action_id and prior.attempt_id == admitted.attempt_id for prior in events):
            raise ValueError("conflicting result validation")
        existing = next((prior for prior in events if prior.event_type == "result_rejected" and prior.action_id == admitted.action_id and prior.attempt_id == admitted.attempt_id), None)
        if existing is not None:
            if any((
                existing.result_hash != result_hash,
                existing.artifact_hash != artifact_hash,
                existing.validation_errors != errors,
                existing.provenance != event_provenance,
            )):
                raise ValueError("conflicting duplicate result rejection")
            return existing
        event = LifecycleEvent(
            run_id=admitted.run_id,
            action_id=admitted.action_id,
            attempt_id=admitted.attempt_id,
            parent_action_id=admitted.parent_action_id,
            event_type="result_rejected",
            company_id=admission.company_id,
            action_type=admission.action_type,
            scope=admission.scope,
            idempotency_key=admission.idempotency_key,
            contract_version=admission.contract_version,
            strategy_version=admission.strategy_version,
            profile_version=admission.profile_version,
            profile_name=admission.profile_name,
            skills=admission.skills,
            request_hash=admission.request_hash,
            budget_units=admission.budget_units,
            result_hash=result_hash,
            artifact_hash=artifact_hash,
            terminal_status="Rejected",
            coverage_delta={},
            validation_errors=errors,
            provenance=event_provenance,
            created_at=datetime.now(timezone.utc),
        )
        _append_locked(root, event)
        return event


def settle_action(root: Path, receipt: ActionReceipt | dict[str, object]) -> ActionReceipt:
    if isinstance(receipt, dict) and "budget_units" in receipt:
        budget_units = receipt["budget_units"]
        receipt = {key: value for key, value in receipt.items() if key != "budget_units"}
        receipt.setdefault("budget_requested", budget_units)
    validated = receipt if isinstance(receipt, ActionReceipt) else ActionReceipt.model_validate(receipt)
    with _run_lock(root, validated.run_id):
        events = _state_events(root, validated.run_id)
        admission = next((event for event in events if event.event_type == "admitted" and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        result = next((event for event in events if event.event_type in {"result_validated", "result_rejected"} and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        if admission is None:
            raise ValueError("action is not admitted")
        if result is None:
            raise ValueError("action result is not validated")
        identity_fields = {
            "company_id": admission.company_id,
            "action_type": admission.action_type,
            "scope": admission.scope,
            "idempotency_key": admission.idempotency_key,
            "request_hash": admission.request_hash,
            "contract_version": admission.contract_version,
            "strategy_version": admission.strategy_version,
            "profile_version": admission.profile_version,
            "profile_name": admission.profile_name,
            "skills": admission.skills,
        }
        for field, expected in identity_fields.items():
            if getattr(validated, field) != expected:
                raise ValueError(f"receipt {field} does not match admission")
        if validated.result_hash != result.result_hash:
            raise ValueError("receipt result hash does not match validated result")
        if validated.artifact_hash != result.artifact_hash:
            raise ValueError("receipt artifact hash does not match validated result")
        if validated.terminal_status != result.terminal_status:
            raise ValueError("receipt terminal status does not match validated result")
        if validated.terminal_status == "Rejected":
            if result.event_type != "result_rejected":
                raise ValueError("rejected receipt requires a durable result rejection")
            if validated.validation_errors != result.validation_errors:
                raise ValueError("receipt validation errors do not match rejected result")
            if validated.coverage_delta:
                raise ValueError("rejected receipt cannot report coverage")
        _validate_coverage_delta(admission, validated.terminal_status, validated.coverage_delta)
        if validated.budget_requested != admission.budget_units:
            raise ValueError("receipt budget does not match admission")
        if validated.budget_settled > validated.budget_requested:
            raise ValueError("settled budget exceeds requested budget")
        event = LifecycleEvent(
            run_id=validated.run_id,
            action_id=validated.action_id,
            attempt_id=validated.attempt_id,
            event_type="settled",
            company_id=validated.company_id,
            action_type=validated.action_type,
            scope=validated.scope,
            idempotency_key=validated.idempotency_key,
            contract_version=admission.contract_version,
            strategy_version=admission.strategy_version,
            profile_version=admission.profile_version,
            parent_action_id=admission.parent_action_id,
            profile_name=admission.profile_name,
            skills=admission.skills,
            request_hash=validated.request_hash,
            budget_units=validated.budget_requested,
            result_hash=validated.result_hash,
            terminal_status=validated.terminal_status,
            budget_settled=validated.budget_settled,
            coverage_delta=validated.coverage_delta,
            stop_decision=validated.stop_decision.model_dump(mode="json") if validated.stop_decision else None,
            provenance=validated.provenance,
            created_at=validated.created_at,
        )
        existing = [prior for prior in events if prior.event_type == "settled" and prior.action_id == validated.action_id and prior.attempt_id == validated.attempt_id]
        for prior in existing:
            if _dump(prior) != _dump(event):
                raise ValueError("conflicting duplicate settlement")
            append_receipt(root, validated)
            return validated
        _append_locked(root, event)
    append_receipt(root, validated)
    return validated


def replay_lifecycle(root: Path, run_id: str, *, prefer_snapshot: bool = False) -> dict[str, Any]:
    events = _state_events(root, run_id) if prefer_snapshot else read_lifecycle(root, run_id)
    if not events:
        legacy = replay_run(root, run_id)
        if legacy["action_count"]:
            return {**legacy, "budget_reserved": legacy["budget_requested"], "legacy_receipt_adapter": True}
    by_action: dict[tuple[str, str], dict[str, LifecycleEvent]] = {}
    for event in events:
        key = (event.action_id, event.attempt_id)
        states = by_action.setdefault(key, {})
        if event.event_type in states and _dump(states[event.event_type]) != _dump(event):
            raise ValueError(f"conflicting lifecycle transition: {event.action_id}/{event.attempt_id}/{event.event_type}")
        states[event.event_type] = event
    actions: list[dict[str, Any]] = []
    reserved = settled = 0
    coverage: dict[str, int] = {}
    for key, states in sorted(by_action.items()):
        admitted = states.get("admitted")
        result = states.get("result_validated") or states.get("result_rejected")
        settlement = states.get("settled")
        if admitted is None:
            raise ValueError(f"lifecycle transition missing admission: {key[0]}/{key[1]}")
        reserved += admitted.budget_units
        if settlement is not None:
            if result is None:
                raise ValueError(f"settlement missing result validation or rejection: {key[0]}/{key[1]}")
            settled += settlement.budget_settled
            if settlement.terminal_status not in {"Completed", "Partial"}:
                if settlement.coverage_delta:
                    raise ValueError(f"non-successful settlement reports coverage: {key[0]}/{key[1]}")
            else:
                for name, value in settlement.coverage_delta.items():
                    if isinstance(value, bool):
                        coverage[name] = coverage.get(name, 0) + int(value)
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        coverage[name] = coverage.get(name, 0) + value
            status = settlement.terminal_status
        else:
            status = result.terminal_status if result is not None else "Admitted"
        actions.append({
            "action_id": key[0],
            "attempt_id": key[1],
            "parent_action_id": admitted.parent_action_id,
            "company_id": admitted.company_id,
            "action_type": admitted.action_type,
            "scope": admitted.scope,
            "profile_name": admitted.profile_name,
            "skills": admitted.skills,
            "status": status,
            "settled": settlement is not None,
            "stop_decision": settlement.stop_decision if settlement is not None else None,
        })
    return {
        "action_count": len(actions),
        "actions": actions,
        "budget_reserved": reserved,
        "budget_settled": settled,
        "coverage": dict(sorted(coverage.items())),
    }

