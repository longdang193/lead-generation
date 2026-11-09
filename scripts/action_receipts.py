"""Durable, append-only action receipt journal for native handoffs."""

from __future__ import annotations

import json
import threading
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from typed_contracts import ActionReceipt


_LOCK = threading.RLock()


def receipt_path(root: Path, run_id: str) -> Path:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a non-empty path-safe identifier")
    return root / "evidence" / "action_receipts" / f"{run_id}.jsonl"


def _record(receipt: ActionReceipt) -> dict[str, Any]:
    return receipt.model_dump(mode="json", exclude_none=True)


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid action receipt JSON at line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"action receipt at line {line_number} is not an object")
        records.append(_record(ActionReceipt.model_validate(value)))
    return records


def append_receipt(root: Path, receipt: ActionReceipt | dict[str, Any]) -> ActionReceipt:
    """Append one receipt, treating exact duplicates as idempotent success."""

    validated = receipt if isinstance(receipt, ActionReceipt) else ActionReceipt.model_validate(receipt)
    path = receipt_path(root, validated.run_id)
    incoming = _record(validated)
    key = (validated.action_id, validated.attempt_id)
    with _LOCK:
        existing = _read(path)
        for record in existing:
            if (record.get("action_id"), record.get("attempt_id")) != key:
                continue
            if canonical_json(record) != canonical_json(incoming):
                raise ValueError(f"conflicting duplicate action receipt: {key[0]}/{key[1]}")
            return validated
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(incoming) + "\n")
            handle.flush()
            import os

            os.fsync(handle.fileno())
    return validated


def read_receipts(root: Path, run_id: str) -> list[ActionReceipt]:
    return [ActionReceipt.model_validate(value) for value in _read(receipt_path(root, run_id))]


def replay_receipts(receipts: Iterable[ActionReceipt]) -> dict[str, Any]:
    """Reconstruct settled budget, coverage, and action history without reruns."""

    history: list[dict[str, Any]] = []
    coverage: dict[str, int] = defaultdict(int)
    settled = 0
    requested = 0
    for receipt in receipts:
        settled += receipt.budget_settled
        requested += receipt.budget_requested
        for key, value in receipt.coverage_delta.items():
            if isinstance(value, bool):
                coverage[key] += int(value)
            elif isinstance(value, int | float):
                coverage[key] += value
        history.append(
            {
                "action_id": receipt.action_id,
                "attempt_id": receipt.attempt_id,
                "company_id": receipt.company_id,
                "status": receipt.terminal_status,
            }
        )
    return {
        "action_count": len(history),
        "actions": history,
        "budget_requested": requested,
        "budget_settled": settled,
        "coverage": dict(sorted(coverage.items())),
    }


def replay_run(root: Path, run_id: str) -> dict[str, Any]:
    return replay_receipts(read_receipts(root, run_id))
