"""Normalize bounded account-validation handoffs into one controller contract."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _source_attempts(action: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = action.get("source_attempts")
    if isinstance(attempts, list):
        normalized = []
        for item in attempts:
            if not isinstance(item, dict):
                continue
            if item.get("url") or item.get("source_url"):
                normalized.append({**item, "url": item.get("url") or item.get("source_url")})
        return normalized
    urls = action.get("source_urls")
    if isinstance(urls, list):
        return [{"url": str(url), "status": action.get("status", "Unknown")} for url in urls if url]
    attempted = action.get("sources_attempted")
    if isinstance(attempted, list):
        return [{"url": str(url), "status": action.get("status", "Unknown")} for url in attempted if url]
    return []


def _normalize_action(action: Any, index: int) -> dict[str, Any]:
    raw = action if isinstance(action, dict) else {"result": str(action)}
    source_attempts = _source_attempts(raw)
    source_urls = sorted({str(item.get("url")) for item in source_attempts if item.get("url")})
    return {
        "selection_next_action": raw.get("selection_next_action") or index,
        "action_id": raw.get("action_id"),
        "action_type": raw.get("action_type") or raw.get("action") or "Unknown",
        "scope": raw.get("scope") or raw.get("bounded_scope") or "Unknown",
        "status": raw.get("status") or "Unknown",
        "timestamp": raw.get("timestamp") or raw.get("retrieved_at"),
        "source_attempts": source_attempts,
        "source_urls": source_urls,
        "result": raw.get("result"),
        "next_gap": raw.get("next_gap"),
        "claim_ids": _as_list(raw.get("claim_ids")),
    }


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("account-validation record must be an object")
    company_id = str(raw.get("company_id") or "").strip()
    if not company_id:
        raise ValueError("account-validation record requires company_id")
    company_name = str(raw.get("company_name") or raw.get("name") or "").strip()
    if not company_name:
        raise ValueError(f"account-validation record requires company_name: {company_id}")
    actions = [_normalize_action(item, index) for index, item in enumerate(_as_list(raw.get("actions")), start=1)]
    turns = raw.get("selection_turns_used")
    if turns in (None, ""):
        turns = len(actions)
    try:
        turns = int(turns)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"selection_turns_used must be an integer: {company_id}") from exc
    if turns < 1 or turns > 5:
        raise ValueError(f"selection_turns_used must be between 1 and 5: {company_id}")
    return {
        "company_id": company_id,
        "company_name": company_name,
        "domain": raw.get("domain"),
        "selection_turns_used": turns,
        "actions": actions,
        "verified_claims": _as_list(raw.get("verified_claims")),
        "hypotheses": _as_list(raw.get("hypotheses")),
        "counterevidence": _as_list(raw.get("counterevidence")),
        "why_this_account": str(raw.get("why_this_account") or ""),
        "why_now": str(raw.get("why_now") or ""),
        "recommended_next_action": str(raw.get("recommended_next_action") or ""),
        "unresolved_decision_gaps": _as_list(raw.get("unresolved_decision_gaps")),
        "fit_class": str(raw.get("fit_class") or "Unknown"),
        "direct_intent": str(raw.get("direct_intent") or "Unknown"),
        "trigger": str(raw.get("trigger") or "Unknown"),
        "need_indicator": str(raw.get("need_indicator") or "Unknown"),
        "change_readiness": str(raw.get("change_readiness") or "Unknown"),
        "access_summary": str(raw.get("access_summary") or "Unknown"),
        "confidence": str(raw.get("confidence") or "Unknown"),
    }


def normalize_files(input_paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in input_paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = normalize_record(json.loads(line))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            if record["company_id"] in seen:
                raise ValueError(f"duplicate account-validation company_id: {record['company_id']}")
            seen.add(record["company_id"])
            records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-glob", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [Path(item) for item in sorted(glob.glob(args.input_glob))]
    if not paths:
        raise SystemExit(f"no files matched: {args.input_glob}")
    records = normalize_files(paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(args.output), "input_files": [str(path) for path in paths]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
