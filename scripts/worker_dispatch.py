from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from orchestrate_enrichment import validate_lane_output
from lead_contract import candidate_claim_id, candidate_sha256


TERMINAL = {"succeeded", "failed", "cancelled", "timed_out"}


@dataclass(frozen=True)
class NativeExecutorConfig:
    executable: str
    profile: str
    timeout_seconds: int = 120
    max_retries: int = 0
    adapter_args: tuple[str, ...] = ()


def _terminal(status: str) -> str:
    if status not in TERMINAL:
        raise ValueError(f"invalid terminal worker status: {status}")
    return status


def dispatch_native_lane(
    queue: Iterable[dict[str, object]],
    run_id: str,
    lane: str,
    output_dir: Path,
    config: NativeExecutorConfig,
    *,
    command_builder: Callable[[dict[str, object], Path, NativeExecutorConfig], list[str]] | None = None,
) -> list[dict[str, object]]:
    """Run one bounded native lane with explicit worker terminal states.

    The worker receives JSON queue item, run ID, lane, profile, and output path
    arguments. It may only write beneath output_dir; the controller records exit
    code, attempts, timeout/cancellation, and output hash for reconciliation.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for item in queue:
        company_id = str(item["company_id"])
        item_output = output_dir / f"{lane}-{company_id}.json"
        command = command_builder(item, item_output, config) if command_builder else [
            config.executable,
            "--profile", config.profile,
            "--run-id", run_id,
            "--lane", lane,
            "--company-id", company_id,
            "--output", str(item_output),
        ]
        attempts = 0
        status = "failed"
        exit_code: int | None = None
        started = time.time()
        for attempts in range(1, config.max_retries + 2):
            try:
                completed = subprocess.run(command, check=False, timeout=config.timeout_seconds, cwd=output_dir.parent.parent.parent)
                exit_code = completed.returncode
                status = "succeeded" if exit_code == 0 and item_output.exists() else "failed"
                break
            except subprocess.TimeoutExpired:
                status = "timed_out"
                break
            except KeyboardInterrupt:
                status = "cancelled"
                raise
            except OSError:
                status = "failed"
                break
        record: dict[str, object] = {
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "status": _terminal(status),
            "attempts": attempts,
            "exit_code": exit_code,
            "duration_seconds": round(time.time() - started, 3),
            "output_path": item_output.as_posix(),
        }
        if item_output.exists():
            record["output_sha256"] = __import__("hashlib").sha256(item_output.read_bytes()).hexdigest()
        records.append(record)
    return records


def dispatch_fixture_lanes(queues: dict[str, list[dict[str, object]]], run_id: str, output_dir: Path) -> dict[str, list[dict[str, object]]]:
    """Deterministic local executor used by tests and provider-free probes."""
    results: dict[str, list[dict[str, object]]] = {}
    for lane, queue in queues.items():
        lane_dir = output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        lane_results: list[dict[str, object]] = []
        for item in reversed(queue):
            company_id = str(item["company_id"])
            research_run = {
                "record_type": "ResearchRun",
                "run_id": f"{run_id}:{lane}:{company_id}",
                "company_id": company_id,
                "research_type": lane,
                "source": "fixture",
                "scope": f"{lane}:{company_id}",
                "status": "Completed",
                "started_at": "2026-11-08T00:00:00+00:00",
                "completed_at": "2026-11-08T00:00:01+00:00",
                "result_count": 0,
                "truncated": False,
                "provider_status": "Available",
                "scope_version": "fixture-v1",
                "scope_hash": "0" * 64,
                "attempts": [{"attempt_id": f"{run_id}:{lane}:{company_id}:1", "query_or_source": "fixture", "status": "Completed", "truncated": False}],
            }
            domain = str(item.get("trusted_domain") or "example.invalid")
            source_url = f"https://{domain}/"
            claims: list[dict[str, object]] = []
            if lane == "portfolio":
                claims.extend([
                    {"claim_type": "service_fit", "claim_value": "Confirmed", "source_url": source_url + "services", "source_kind": "official", "evidence_excerpt": "Hausverwaltung und Immobilienverwaltung für Wohnobjekte in Berlin.", "published_at": None},
                    {"claim_type": "residential_weg", "claim_value": "Confirmed", "source_url": source_url + "services", "source_kind": "official", "evidence_excerpt": "Verwaltung von Wohnungseigentümergemeinschaften und Wohnimmobilien.", "published_at": None},
                    {"claim_type": "berlin_relevance", "claim_value": "Confirmed", "source_url": source_url, "source_kind": "official", "evidence_excerpt": "Hausverwaltung für Eigentümer in Berlin.", "published_at": None},
                    {"claim_type": "portfolio_size", "claim_value": 1000, "unit": "units", "scope": "managed residential portfolio", "as_of_date": "2026-10-01", "source_url": source_url + "portfolio", "source_kind": "official", "evidence_excerpt": "The company manages approximately 1,000 residential units in Berlin.", "published_at": None},
                ])
            elif lane == "signals":
                claims.extend([
                    {"claim_type": "buying_signal", "claim_value": "Strong", "source_url": source_url + "news", "source_kind": "official", "evidence_excerpt": "A current Berlin procurement notice names the company as an active participant.", "published_at": "2026-10-01"},
                    {"claim_type": "event", "claim_value": {"event_id": f"event-{company_id}", "publication_date": "2026-10-01", "deadline": "2026-12-01"}, "source_url": source_url + "news", "source_kind": "official", "evidence_excerpt": "A current Berlin procurement notice names the company as an active participant.", "published_at": "2026-10-01"},
                ])
            elif lane == "contacts":
                claims.append({"claim_type": "contact", "claim_value": "Anna Schmidt", "person_name": "Anna Schmidt", "role": "Geschäftsführung", "company_affiliation": str(item.get("company_name") or ""), "email": f"anna.schmidt@{domain}", "source_url": source_url + "contact", "source_kind": "official", "evidence_excerpt": "Anna Schmidt — Geschäftsführung", "published_at": None})
            normalized_claims: list[dict[str, object]] = []
            for claim in claims:
                normalized = {
                    "record_type": "EvidenceClaim",
                    "candidate_claim_id": candidate_claim_id({"company_id": company_id, **claim}),
                    "company_id": company_id,
                    "claim_type": claim["claim_type"],
                    "claim_value": claim["claim_value"],
                    "unit": claim.get("unit"),
                    "scope": claim.get("scope"),
                    "source_url": claim["source_url"],
                    "source_domain": domain,
                    "source_kind": claim["source_kind"],
                    "evidence_excerpt": claim["evidence_excerpt"],
                    "retrieved_at": "2026-11-08T00:00:00+00:00",
                    "published_at": claim.get("published_at"),
                    "as_of_date": claim.get("as_of_date"),
                    "account_relationship": "direct",
                    "confidence": "high",
                    "research_run_id": research_run["run_id"],
                    "candidate_status": "Candidate",
                    "person_name": claim.get("person_name"),
                    "role": claim.get("role"),
                    "company_affiliation": claim.get("company_affiliation"),
                    "email": claim.get("email"),
                    "verifier_run_id": None,
                    "verified_at": None,
                }
                normalized["candidate_sha256"] = candidate_sha256(normalized)
                normalized_claims.append(normalized)
            path = lane_dir / f"{company_id}.json"
            path.write_text(json.dumps({"research_run": research_run, "claims": normalized_claims}, sort_keys=True) + "\n", encoding="utf-8")
            lane_results.append({
                "run_id": run_id,
                "lane": lane,
                "company_id": company_id,
                "status": "succeeded",
                "research_run_id": research_run["run_id"],
                "output_path": path.as_posix(),
                "output_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
                "attempts": 1,
            })
        results[lane] = lane_results
    return results


def reconcile_lane_outputs(records: list[dict[str, object]], queue: list[dict[str, object]], run_id: str, lane: str) -> None:
    validate_lane_output(records, queue, run_id, lane)
    if any(str(record.get("status")) != "succeeded" for record in records):
        raise ValueError(f"lane {lane} has unsuccessful terminal output")
