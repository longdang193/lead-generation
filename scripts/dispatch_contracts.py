"""Neutral validation contracts shared by dispatch and orchestration callers."""

from __future__ import annotations


def validate_lane_output(records: list[dict[str, object]], queue: list[dict[str, object]], run_id: str, lane: str) -> None:
    allowed = {str(item["company_id"]) for item in queue}
    seen: set[str] = set()
    for record in records:
        company_id = str(record.get("company_id") or "")
        if record.get("run_id") != run_id or record.get("lane") != lane:
            raise ValueError("lane output has mismatched run or lane")
        if company_id not in allowed:
            raise ValueError(f"lane output is out of scope: {company_id}")
        if company_id in seen:
            raise ValueError(f"duplicate lane output: {company_id}")
        if str(record.get("status") or "") not in {"succeeded", "failed", "cancelled", "timed_out", "Completed", "Partial", "Unavailable", "Needs review"}:
            raise ValueError(f"lane output has non-terminal status: {company_id}")
        seen.add(company_id)
    missing = sorted(allowed - seen)
    if missing:
        raise ValueError(f"lane output missing queued companies: {', '.join(missing)}")
