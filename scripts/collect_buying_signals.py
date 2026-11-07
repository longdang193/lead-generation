from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from runtime_config import RuntimeConfig


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--ted-output", type=Path, required=True)
    parser.add_argument("--links-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    with args.companies.open(encoding="utf-8-sig", newline="") as handle:
        companies = list(csv.DictReader(handle))
    events: list[dict[str, object]] = []
    links: list[dict[str, str]] = []
    audit = [{"company_id": row.get("company_id", ""), "search_status": "Unavailable" if not config.ted_api_base_url else "Searched", "event_count": "0", "reason": "TED_API_BASE_URL not configured" if not config.ted_api_base_url else "No event import configured", "retrieved_at": stamp()} for row in companies]
    args.ted_output.parent.mkdir(parents=True, exist_ok=True)
    args.ted_output.write_text(json.dumps(events, indent=2), encoding="utf-8")
    args.links_output.parent.mkdir(parents=True, exist_ok=True)
    with args.links_output.open("w", encoding="utf-8", newline="") as handle:
        fields = ["event_id", "company_id", "match_method", "match_confidence", "source_url"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(links)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.audit_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(audit[0]) if audit else ["company_id", "search_status", "event_count", "reason", "retrieved_at"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audit)
    print(json.dumps({"companies": len(companies), "events": len(events), "links": len(links), "ted_configured": bool(config.ted_api_base_url)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
