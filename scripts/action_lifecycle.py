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
from run_manifest import load
from typed_contracts import ActionReceipt, LifecycleEvent, NativeActionRequest, WorkerResult


_THREAD_LOCK = threading.RLock()


def _safe_run_id(run_id: str) -> str:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a non-empty path-safe identifier")
    return run_id


def lifecycle_path(root: Path, run_id: str) -> Path:
    return root / "evidence" / "action_lifecycle" / f"{_safe_run_id(run_id)}.jsonl"


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


def read_lifecycle(root: Path, run_id: str) -> list[LifecycleEvent]:
    return _read(lifecycle_path(root, run_id))


def _append_locked(root: Path, event: LifecycleEvent) -> None:
    path = lifecycle_path(root, event.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(_dump(event)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


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
    raw = manifest.get("budget_limit")
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ValueError("manifest budget_limit must be a nonnegative integer")
    return raw


def admit_action(root: Path, request: NativeActionRequest | dict[str, object], manifest_path: Path) -> NativeActionRequest:
    validated = request if isinstance(request, NativeActionRequest) else NativeActionRequest.model_validate(request)
    with _run_lock(root, validated.run_id):
        events = _read(lifecycle_path(root, validated.run_id))
        admissions = [event for event in events if event.event_type == "admitted"]
        for event in admissions:
            if event.action_id == validated.action_id and event.attempt_id == validated.attempt_id:
                if event.idempotency_key != validated.idempotency_key or event.request_hash != validated.request_hash:
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


def _canonical_result_hash(result: WorkerResult) -> str:
    payload = canonical_json(result.result)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_result(root: Path, result: WorkerResult | dict[str, object]) -> WorkerResult:
    validated = result if isinstance(result, WorkerResult) else WorkerResult.model_validate(result)
    if validated.result_hash != _canonical_result_hash(validated):
        raise ValueError("result hash mismatch")
    with _run_lock(root, validated.run_id):
        events = _read(lifecycle_path(root, validated.run_id))
        admission = next((event for event in events if event.event_type == "admitted" and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        if admission is None:
            raise ValueError("action is not admitted")
        if admission.company_id != validated.company_id:
            raise ValueError("result company does not match admission")
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
            request_hash=admission.request_hash,
            budget_units=admission.budget_units,
            result_hash=validated.result_hash,
            terminal_status=validated.status,
            provenance=validated.provenance,
            created_at=datetime.now(timezone.utc),
        )
        existing = [prior for prior in events if prior.event_type == "result_validated" and prior.action_id == validated.action_id and prior.attempt_id == validated.attempt_id]
        for prior in existing:
            if _dump(prior) != _dump(event):
                raise ValueError("conflicting duplicate result validation")
            return validated
        _append_locked(root, event)
    return validated


def settle_action(root: Path, receipt: ActionReceipt | dict[str, object]) -> ActionReceipt:
    if isinstance(receipt, dict) and "budget_units" in receipt:
        budget_units = receipt["budget_units"]
        receipt = {key: value for key, value in receipt.items() if key != "budget_units"}
        receipt.setdefault("budget_requested", budget_units)
    validated = receipt if isinstance(receipt, ActionReceipt) else ActionReceipt.model_validate(receipt)
    with _run_lock(root, validated.run_id):
        events = _read(lifecycle_path(root, validated.run_id))
        admission = next((event for event in events if event.event_type == "admitted" and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        result = next((event for event in events if event.event_type == "result_validated" and event.action_id == validated.action_id and event.attempt_id == validated.attempt_id), None)
        if admission is None:
            raise ValueError("action is not admitted")
        if result is None:
            raise ValueError("action result is not validated")
        if validated.result_hash != result.result_hash:
            raise ValueError("receipt result hash does not match validated result")
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
            request_hash=validated.request_hash,
            budget_units=validated.budget_requested,
            result_hash=validated.result_hash,
            terminal_status=validated.terminal_status,
            budget_settled=validated.budget_settled,
            coverage_delta=validated.coverage_delta,
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


def replay_lifecycle(root: Path, run_id: str) -> dict[str, Any]:
    events = read_lifecycle(root, run_id)
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
        result = states.get("result_validated")
        settlement = states.get("settled")
        if admitted is None:
            raise ValueError(f"lifecycle transition missing admission: {key[0]}/{key[1]}")
        reserved += admitted.budget_units
        if settlement is not None:
            if result is None:
                raise ValueError(f"settlement missing validated result: {key[0]}/{key[1]}")
            settled += settlement.budget_settled
            for name, value in settlement.coverage_delta.items():
                if isinstance(value, bool):
                    coverage[name] = coverage.get(name, 0) + int(value)
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    coverage[name] = coverage.get(name, 0) + value
            status = settlement.terminal_status
        else:
            status = result.terminal_status if result is not None else "Admitted"
        actions.append({"action_id": key[0], "attempt_id": key[1], "company_id": admitted.company_id, "status": status})
    return {
        "action_count": len(actions),
        "actions": actions,
        "budget_reserved": reserved,
        "budget_settled": settled,
        "coverage": dict(sorted(coverage.items())),
    }







