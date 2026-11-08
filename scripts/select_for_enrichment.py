from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from lead_contract import priority_rank, signal_rank, tier_rank, update_run_manifest


def read_qualification(path: Path) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        company_id = str(row.get("company_id") or "")
        if company_id:
            records[company_id] = row
    return records


def number(value: object, default: float = -1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def eligible_for_enrichment(row: dict[str, str], qualification: dict[str, object]) -> bool:
    resolution = str(qualification.get("resolution_status") or row.get("resolution_status") or "Accepted")
    eligible = qualification.get("eligible", row.get("eligible", "true"))
    if isinstance(eligible, str):
        eligible = eligible.strip().lower() in {"1", "true", "yes", "accepted"}
    return resolution == "Accepted" and bool(eligible) and row.get("lead_tier") in {"A", "B"} and number(row.get("evidence_coverage")) >= 50


def select_accounts(scores: list[dict[str, str]], qualification: dict[str, dict[str, object]], max_accounts: int) -> list[dict[str, str]]:
    selected = [
        row for row in scores
        if eligible_for_enrichment(row, qualification.get(str(row.get("company_id") or ""), {}))
    ]

    def sort_key(row: dict[str, str]) -> tuple[int, int, float, float, float, int, str]:
        return (
            priority_rank(row.get("sales_priority")),
            tier_rank(row.get("lead_tier")),
            -number(row.get("evidence_coverage")),
            -number(row.get("structural_lead_fit")),
            -number(row.get("portfolio_potential")),
            -signal_rank(row.get("buying_signal")),
            str(row.get("company_id") or ""),
        )

    return sorted(selected, key=sort_key)[:max_accounts]


def write_provisional_shortlist(rows: list[dict[str, str]], output: Path, audit_output: Path) -> None:
    selected_ids = {row.get("company_id") for row in rows}
    audit = [
        {
            "company_id": row.get("company_id", ""),
            "selected": "true" if row.get("company_id") in selected_ids else "false",
            "reason": "accepted eligible A/B row with evidence coverage >= 50",
        }
        for row in rows
    ]
    for path, items, fallback in (
        (output, rows, ["company_id", "lead_tier"]),
        (audit_output, audit, ["company_id", "selected"]),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            fields = list(items[0]) if items else fallback
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(items)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--max-accounts", type=int, default=30)
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()

    with args.scores.open(encoding="utf-8-sig", newline="") as handle:
        scores = list(csv.DictReader(handle))
    qualification = read_qualification(args.qualification)
    selected = select_accounts(scores, qualification, args.max_accounts)
    write_provisional_shortlist(selected, args.output, args.audit_output)
    if args.run_manifest and args.run_manifest.exists():
        update_run_manifest(args.run_manifest, inputs={"scores": args.scores, "qualification": args.qualification}, outputs={"provisional_shortlist": args.output, "shortlist_audit": args.audit_output})
    print(json.dumps({"selected": len(selected), "total_scores": len(scores)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
