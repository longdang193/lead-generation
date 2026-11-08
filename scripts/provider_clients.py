from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import requests


class ProviderError(RuntimeError):
    """A provider failure without exposing credentials or response bodies."""


def actor_id(value: str) -> str:
    return value.replace("/", "~", 1)


def build_ted_search_body(search_term: str, limit: int = 100) -> dict[str, Any]:
    safe_term = search_term.replace('"', "").strip()
    return {
        "query": f'FT~"{safe_term}"',
        "fields": [
            "publication-number",
            "notice-title",
            "buyer-name",
            "buyer-country",
            "deadline",
            "links",
        ],
        "limit": max(1, min(limit, 250)),
        "scope": "ALL",
        "page": 1,
        "paginationMode": "PAGE_NUMBER",
    }


def normalize_apify_items(items: list[Mapping[str, Any]], actor: str, run_id: str) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    flattened: list[Mapping[str, Any]] = []
    for item in items:
        organic = item.get("organicResults") if isinstance(item, Mapping) else None
        if isinstance(organic, list):
            flattened.extend(result for result in organic if isinstance(result, Mapping))
        else:
            flattened.append(item)
    for index, item in enumerate(flattened, start=1):
        title = item.get("title") or item.get("name") or item.get("company") or ""
        url = item.get("url") or item.get("link") or item.get("website") or ""
        if not title and not url:
            continue
        normalized.append({
            "source_record_id": str(item.get("id") or index),
            "company_name": str(title),
            "source_url": str(url),
            "source_type": "Apify",
            "source_reuse_status": "New retrieval",
            "extraction_method": actor,
            "actor_id": actor,
            "actor_run_id": run_id,
        })
    return normalized


def run_apify_actor(
    actor: str,
    input_payload: Mapping[str, Any],
    token: str,
    timeout: int,
    max_total_charge_usd: float,
    session: Any = requests,
    poll_seconds: float = 2.0,
    max_polls: int = 90,
) -> tuple[list[dict[str, Any]], str, float | None]:
    if not token:
        raise ProviderError("APIFY_API_TOKEN is not configured")
    if max_total_charge_usd <= 0:
        raise ProviderError("Apify spend budget must be positive")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    endpoint = f"https://api.apify.com/v2/acts/{actor_id(actor)}/runs"
    response = session.post(endpoint, headers=headers, json=dict(input_payload), params={"maxTotalChargeUsd": f"{max_total_charge_usd:.2f}"}, timeout=timeout)
    if not response.ok:
        raise ProviderError(f"Apify start failed with HTTP {response.status_code}")
    run = response.json().get("data", response.json())
    run_id = str(run.get("id") or run.get("runId") or "")
    dataset_id = str(run.get("defaultDatasetId") or "")
    if not run_id:
        raise ProviderError("Apify start response did not include a run ID")
    status = str(run.get("status") or "RUNNING")
    usage: float | None = run.get("usageTotalUsd")
    for _ in range(max_polls):
        if status in {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}:
            break
        time.sleep(poll_seconds)
        status_response = session.get(f"https://api.apify.com/v2/actor-runs/{run_id}", headers=headers, timeout=timeout)
        if not status_response.ok:
            raise ProviderError(f"Apify status failed with HTTP {status_response.status_code}")
        status_payload = status_response.json().get("data", status_response.json())
        status = str(status_payload.get("status") or status)
        dataset_id = str(status_payload.get("defaultDatasetId") or dataset_id)
        usage = status_payload.get("usageTotalUsd", usage)
    if status != "SUCCEEDED":
        raise ProviderError(f"Apify run ended with status {status}")
    if not dataset_id:
        raise ProviderError("Apify run did not include a dataset ID")
    items_response = session.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items", headers=headers, params={"format": "json", "clean": "1"}, timeout=timeout)
    if not items_response.ok:
        raise ProviderError(f"Apify dataset read failed with HTTP {items_response.status_code}")
    payload = items_response.json()
    return (payload if isinstance(payload, list) else payload.get("items", [])), run_id, float(usage) if usage is not None else None


def overpass_query(api_url: str, query: str, timeout: int = 30, session: Any = requests, retries: int = 2) -> dict[str, Any]:
    headers = {"User-Agent": "lead-generation-mvp/1.0 (public endpoint query)", "Accept": "application/json"}
    last_status = "unknown"
    for attempt in range(retries + 1):
        try:
            response = session.get(api_url, params={"data": query}, headers=headers, timeout=timeout)
            last_status = str(response.status_code)
            if response.ok:
                payload = response.json()
                if isinstance(payload, dict) and isinstance(payload.get("elements"), list):
                    return payload
        except (requests.RequestException, ValueError):
            pass
        if attempt < retries:
            time.sleep(min(5 * (attempt + 1), 15))
    raise ProviderError(f"Overpass query failed after retries; last HTTP status {last_status}")


def ted_search(base_url: str, search_term: str, timeout: int = 30, session: Any = requests, limit: int = 100) -> list[dict[str, Any]]:
    if not base_url:
        raise ProviderError("TED_API_BASE_URL is not configured")
    endpoint = base_url.rstrip("/") + "/v3/notices/search"
    response = session.post(endpoint, json=build_ted_search_body(search_term, limit), headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=timeout)
    if not response.ok:
        raise ProviderError(f"TED search failed with HTTP {response.status_code}")
    payload = response.json()
    if isinstance(payload, list):
        return payload
    return payload.get("notices") or payload.get("results") or payload.get("data") or []


def hunter_domain_search(domain: str, api_key: str, timeout: int = 30, session: Any = requests) -> dict[str, Any]:
    if not api_key:
        raise ProviderError("HUNTER_API_KEY is not configured")
    response = session.get("https://api.hunter.io/v2/domain-search", params={"domain": domain, "api_key": api_key}, timeout=timeout)
    if not response.ok:
        raise ProviderError(f"Hunter domain search failed with HTTP {response.status_code}")
    payload = response.json()
    return payload.get("data", payload)
