from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from runtime_config import RuntimeConfig
from provider_clients import ProviderError, normalize_apify_items, overpass_query, run_apify_actor

OVERPASS_MIN_TIMEOUT_SECONDS = 30


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
        payload = payload.get("items") or payload.get("results") or payload.get("data") or payload.get("elements") or []
    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        tags = item.get("tags") if isinstance(item.get("tags"), dict) else {}
        name = item.get("company_name") or item.get("name") or item.get("title") or item.get("company") or tags.get("name") or ""
        url = item.get("source_url") or item.get("url") or item.get("website") or item.get("link") or tags.get("website") or tags.get("contact:website") or ""
        if name or url:
            rows.append({"company_name": str(name), "source_url": str(url), "source_type": source, "source_record_id": str(item.get("source_record_id") or item.get("id") or "")})
    return rows


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("mailto:"):
        return ""
    if value and not value.startswith(("http://", "https://")):
        return "https://" + value
    return value


def source_access_limitation(metadata: dict[str, object], rows: list[dict[str, str]]) -> str:
    return str(metadata.get("reason") or ("" if rows else "optional provider unavailable"))


def overpass_timeout(config: RuntimeConfig) -> int:
    return max(config.request_timeout_seconds, OVERPASS_MIN_TIMEOUT_SECONDS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vdiv", type=Path)
    parser.add_argument("--apify", type=Path)
    parser.add_argument("--overpass", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-register", type=Path, default=Path("evidence/source_register_2026-11-07.csv"))
    parser.add_argument("--fetch-providers", action="store_true")
    parser.add_argument("--apify-query", action="append", dest="apify_queries")
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    if args.fetch_providers:
        if config.apify_api_token:
            queries = args.apify_queries or ["Hausverwaltung Berlin WEG Verwaltung", "Immobilienverwaltung Berlin Mietverwaltung"]
            try:
                items, run_id, usage = run_apify_actor(
                    "apify/google-search-scraper",
                    {"queries": "\n".join(queries), "maxPagesPerQuery": 1, "resultsPerPage": 10, "countryCode": "de"},
                    config.apify_api_token,
                    config.request_timeout_seconds,
                    config.apify_max_spend_usd,
                )
                args.apify.parent.mkdir(parents=True, exist_ok=True)
                args.apify.write_text(json.dumps({"items": normalize_apify_items(items, "apify/google-search-scraper", run_id), "actor_id": "apify/google-search-scraper", "actor_run_id": run_id, "usage_total_usd": usage}, ensure_ascii=False, indent=2), encoding="utf-8")
            except ProviderError as exc:
                args.apify.parent.mkdir(parents=True, exist_ok=True)
                args.apify.write_text(json.dumps({"items": [], "status": "Unavailable", "reason": str(exc)}, indent=2), encoding="utf-8")
        else:
            args.apify.parent.mkdir(parents=True, exist_ok=True)
            args.apify.write_text(json.dumps({"items": [], "status": "Unavailable", "reason": "APIFY_API_TOKEN is not configured"}, indent=2), encoding="utf-8")
        if config.overpass_api_url:
            query = '[out:json][timeout:10];nwr["office"="property_management"](52.48,13.28,52.52,13.45);out center tags 5;'
            try:
                args.overpass.parent.mkdir(parents=True, exist_ok=True)
                args.overpass.write_text(json.dumps(overpass_query(config.overpass_api_url, query, timeout=overpass_timeout(config), retries=config.max_fetch_retries), ensure_ascii=False, indent=2), encoding="utf-8")
            except ProviderError as exc:
                args.overpass.parent.mkdir(parents=True, exist_ok=True)
                args.overpass.write_text(json.dumps({"elements": [], "status": "Unavailable", "reason": str(exc)}, indent=2), encoding="utf-8")
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
        metadata = {}
        if path and path.exists() and path.suffix.lower() == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                metadata = payload if isinstance(payload, dict) else {}
            except (OSError, ValueError):
                metadata = {}
        register.append({
            "source_type": source,
            "retrieved_at": now(),
            "query_or_export_id": path.name if path else "not supplied",
            "access_limitation": source_access_limitation(metadata, rows),
            "actor_id": metadata.get("actor_id", ""),
            "actor_run_id": metadata.get("actor_run_id", ""),
            "extraction_method": metadata.get("actor_id", "bounded local import"),
            "source_reuse_status": "New retrieval" if source in {"Apify", "Overpass"} and rows else "Existing export" if source != "VDIV" else "New retrieval",
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
