from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from runtime_config import RuntimeConfig


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_rows(path: Path, source: str) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("items") or payload.get("results") or payload.get("data") or []
    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("title") or item.get("company") or ""
        url = item.get("url") or item.get("website") or item.get("link") or ""
        if name or url:
            rows.append({"company_name": str(name), "source_url": str(url), "source_type": source, "source_record_id": str(item.get("id") or "")})
    return rows


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("mailto:"):
        return ""
    if value and not value.startswith(("http://", "https://")):
        return "https://" + value
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vdiv", type=Path)
    parser.add_argument("--apify", type=Path)
    parser.add_argument("--overpass", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-register", type=Path, default=Path("evidence/source_register_2026-11-07.csv"))
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    sources = [("VDIV", args.vdiv), ("Apify", args.apify), ("Overpass", args.overpass)]
    records: list[dict[str, str]] = []
    register: list[dict[str, str]] = []
    for source, path in sources:
        rows = read_rows(path, source) if path else []
        for index, row in enumerate(rows, start=1):
            url = normalize_url(row.get("source_url") or row.get("website") or row.get("url") or "")
            name = re.sub(r"\s+", " ", (row.get("company_name") or row.get("name") or "").strip())
            if not name and url:
                name = urlparse(url).netloc
            if not name or not url:
                continue
            records.append({
                "source_type": source,
                "source_record_id": row.get("source_record_id") or str(index),
                "company_name": name,
                "source_url": url,
                "address": row.get("address", ""),
                "city": row.get("city", ""),
                "region": row.get("region", ""),
                "retrieved_at": now(),
                "source_reuse_status": "Existing export" if source != "VDIV" else "New retrieval",
                "extraction_method": row.get("extraction_method", "manual/public export"),
                "actor_id": row.get("actor_id", ""),
                "actor_run_id": row.get("actor_run_id", ""),
            })
        register.append({
            "source_type": source,
            "retrieved_at": now(),
            "query_or_export_id": path.name if path else "not supplied",
            "access_limitation": "optional provider unavailable" if not rows else "",
            "actor_id": "",
            "actor_run_id": "",
            "extraction_method": "bounded local import",
            "source_reuse_status": "Existing export" if source != "VDIV" else "New retrieval",
            "source_url": "https://vdiv-bb.de/mitglieder/" if source == "VDIV" else config.overpass_api_url if source == "Overpass" else "",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(records[0]) if records else ["source_type", "source_record_id", "company_name", "source_url", "address", "city", "region", "retrieved_at", "source_reuse_status", "extraction_method", "actor_id", "actor_run_id"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    args.source_register.parent.mkdir(parents=True, exist_ok=True)
    with args.source_register.open("w", encoding="utf-8", newline="") as handle:
        fields = list(register[0]) if register else ["source_type", "retrieved_at", "query_or_export_id", "access_limitation", "actor_id", "actor_run_id", "extraction_method", "source_reuse_status", "source_url"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(register)
    print(json.dumps({"records": len(records), "sources": {source: len(read_rows(path, source)) if path else 0 for source, path in sources}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
