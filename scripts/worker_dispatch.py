from __future__ import annotations

import json
import hashlib
import os
import signal
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import jsonschema

from orchestrate_enrichment import validate_lane_output
from lead_contract import candidate_claim_id, candidate_sha256, claim_requirements_met


TERMINAL = {"succeeded", "failed", "cancelled", "timed_out"}
RESEARCH_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))
RESEARCH_VALIDATOR = jsonschema.Draft202012Validator(RESEARCH_SCHEMA)


@dataclass(frozen=True)
class NativeExecutorConfig:
    executable: str
    profile: str
    timeout_seconds: int = 120
    max_retries: int = 1
    max_workers: int = 3
    adapter_args: tuple[str, ...] = ()
    timeout_retries: int = 1


def _terminal(status: str) -> str:
    if status not in TERMINAL:
        raise ValueError(f"invalid terminal worker status: {status}")
    return status


def _terminal_evidence_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta.json")


def _write_terminal_evidence(path: Path, item: dict[str, object], run_id: str, lane: str) -> None:
    evidence: dict[str, object] = {
        "run_id": run_id,
        "lane": lane,
        "company_id": item["company_id"],
        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    claims_path = item.get("claims_path")
    if lane == "verifier" and claims_path:
        claims_file = Path(str(claims_path))
        if claims_file.exists():
            evidence["claims_input_sha256"] = hashlib.sha256(claims_file.read_bytes()).hexdigest()
    _terminal_evidence_path(path).write_text(json.dumps(evidence, sort_keys=True) + "\n", encoding="utf-8")


def _valid_terminal_evidence(path: Path, item: dict[str, object], run_id: str, lane: str) -> bool:
    try:
        evidence = json.loads(_terminal_evidence_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(evidence, dict):
        return False
    expected = {"run_id": run_id, "lane": lane, "company_id": item["company_id"]}
    if any(evidence.get(field) != value for field, value in expected.items()):
        return False
    if lane == "verifier":
        claims_path = Path(str(item.get("claims_path") or ""))
        if not claims_path.exists() or evidence.get("claims_input_sha256") != hashlib.sha256(claims_path.read_bytes()).hexdigest():
            return False
    return evidence.get("output_sha256") == hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_terminal_output(path: Path, item: dict[str, object], run_id: str, lane: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if not _valid_terminal_evidence(path, item, run_id, lane):
        return False
    if lane == "verifier":
        expected = {
            "run_id": run_id,
            "lane": lane,
            "campaign_id": item.get("campaign_id", "legacy"),
            "company_id": item["company_id"],
            "scope": item.get("scope"),
            "scope_version": item.get("scope_version"),
            "scope_hash": item.get("scope_hash"),
        }
        claims_path = Path(str(item.get("claims_path") or ""))
        if not claims_path.exists() or payload.get("claims_input_sha256") != hashlib.sha256(claims_path.read_bytes()).hexdigest():
            return False
        return all(payload.get(field) == value for field, value in expected.items()) and isinstance(payload.get("decisions"), list)
    research_run = payload.get("research_run", payload)
    if not isinstance(research_run, dict):
        return False
    try:
        RESEARCH_VALIDATOR.validate(research_run)
    except jsonschema.ValidationError:
        return False
    expected = {
        "run_id": f"{run_id}:{lane}:{item['company_id']}",
        "campaign_id": item.get("campaign_id", "legacy"),
        "company_id": item["company_id"],
        "scope": item.get("scope"),
        "scope_version": item.get("scope_version"),
        "scope_hash": item.get("scope_hash"),
    }
    claims = payload.get("claims", [])
    if not all(research_run.get(field) == value for field, value in expected.items()):
        return False
    if research_run.get("record_type") != "ResearchRun" or research_run.get("status") not in {"Not searched", "Completed", "Partial", "Unavailable", "Needs review"}:
        return False
    if research_run.get("provider_status") not in {"Available", "Unavailable", "Unknown"} or not isinstance(research_run.get("attempts"), list):
        return False
    if not isinstance(claims, list):
        return False
    for claim in claims:
        if not isinstance(claim, dict) or not claim_requirements_met(claim)[0] or claim.get("candidate_claim_id") != candidate_claim_id(claim) or claim.get("candidate_sha256") != candidate_sha256(claim):
            return False
    return True


def split_material_gap_queue(
    queue: Iterable[dict[str, object]],
    run_id: str,
    lane: str,
    output_dir: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pending: list[dict[str, object]] = []
    reused: list[dict[str, object]] = []
    for item in queue:
        company_id = str(item["company_id"])
        output_path = output_dir / f"{lane}-{company_id}.json"
        if not output_path.exists() or not _valid_terminal_output(output_path, item, run_id, lane):
            pending.append(item)
            continue
        reused.append({
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "status": "succeeded",
            "attempts": 0,
            "reused_terminal": True,
            "exit_code": 0,
            "duration_seconds": 0,
            "output_path": output_path.as_posix(),
            "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        })
    return pending, reused


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
    def run_one(item: dict[str, object]) -> dict[str, object]:
        company_id = str(item["company_id"])
        item_output = output_dir / f"{lane}-{company_id}.json"
        if item_output.exists() and _valid_terminal_output(item_output, item, run_id, lane):
            return {
                "run_id": run_id,
                "lane": lane,
                "company_id": company_id,
                "status": "succeeded",
                "attempts": 0,
                "reused_terminal": True,
                "exit_code": 0,
                "duration_seconds": 0,
                "output_path": item_output.as_posix(),
                "output_sha256": hashlib.sha256(item_output.read_bytes()).hexdigest(),
            }
        if item_output.exists():
            item_output.unlink()
        if _terminal_evidence_path(item_output).exists():
            _terminal_evidence_path(item_output).unlink()
        attempts = 0
        status = "failed"
        exit_code: int | None = None
        started = time.time()
        attempt_history: list[dict[str, object]] = []
        for attempts in range(1, config.max_retries + 2):
            attempt_output = output_dir / f".{lane}-{company_id}-attempt-{attempts}.json"
            if attempt_output.exists():
                attempt_output.unlink()
            attempt_command = command_builder(item, attempt_output, config) if command_builder else [
                config.executable,
                "--profile", config.profile,
                "--run-id", run_id,
                "--lane", lane,
                "--company-id", company_id,
                "--output", str(attempt_output),
            ]
            try:
                completed = subprocess.run(attempt_command, check=False, timeout=config.timeout_seconds, cwd=output_dir.parent.parent.parent)
                exit_code = completed.returncode
                if exit_code == 0 and attempt_output.exists():
                    os.replace(attempt_output, item_output)
                    _write_terminal_evidence(item_output, item, run_id, lane)
                    status = "succeeded"
                    attempt_history.append({"attempt": attempts, "status": status})
                    break
                status = "failed"
                attempt_history.append({"attempt": attempts, "status": status, "exit_code": exit_code})
                if item.get("failure_class") == "deterministic":
                    break
                continue
            except subprocess.TimeoutExpired:
                status = "timed_out"
                attempt_history.append({"attempt": attempts, "status": status})
                if attempts <= min(config.timeout_retries, config.max_retries):
                    continue
                break
            except KeyboardInterrupt:
                status = "cancelled"
                raise
            except OSError:
                status = "failed"
                attempt_history.append({"attempt": attempts, "status": status, "failure_class": "transient"})
                continue
            finally:
                if attempt_output.exists():
                    attempt_output.unlink()
        record: dict[str, object] = {
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "status": _terminal(status),
            "attempts": attempts,
            "exit_code": exit_code,
            "duration_seconds": round(time.time() - started, 3),
            "output_path": item_output.as_posix(),
            "failure_class": str(item.get("failure_class") or ("timeout" if status == "timed_out" else "transient" if status == "failed" and attempts > 1 else "deterministic" if status == "failed" else "none")),
            "attempt_history": attempt_history,
        }
        if item_output.exists():
            record["output_sha256"] = hashlib.sha256(item_output.read_bytes()).hexdigest()
        return record

    items = list(queue)
    if config.max_workers <= 1 or len(items) <= 1:
        return [run_one(item) for item in items]
    with ThreadPoolExecutor(max_workers=max(1, config.max_workers)) as executor:
        futures = [executor.submit(run_one, item) for item in items]
        return [future.result() for future in futures]


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
                "campaign_id": item.get("campaign_id", "legacy"),
                "company_name": item.get("company_name", ""),
                "trusted_domain": item.get("trusted_domain", ""),
                "location": item.get("location", "Unknown"),
                "scope": item.get("scope", f"{lane}:{company_id}"),
                "status": "Completed",
                "started_at": "2026-11-08T00:00:00+00:00",
                "completed_at": "2026-11-08T00:00:01+00:00",
                "result_count": 0,
                "truncated": False,
                "provider_status": "Available",
                "adapter_capability": "replay",
                "scope_version": item.get("scope_version", "fixture-v1"),
                "scope_hash": item.get("scope_hash", "0" * 64),
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


def reconcile_lane_outputs(records: list[dict[str, object]], queue: list[dict[str, object]], run_id: str, lane: str, *, allow_partial: bool = False) -> None:
    validate_lane_output(records, queue, run_id, lane)
    if not allow_partial and any(str(record.get("status")) != "succeeded" for record in records):
        raise ValueError(f"lane {lane} has unsuccessful terminal output")
    expected = {str(item["company_id"]): item for item in queue}
    for record in records:
        if allow_partial and str(record.get("status")) != "succeeded":
            continue
        output_path = Path(str(record.get("output_path") or ""))
        if not output_path.exists():
            raise ValueError(f"lane output is missing: {output_path}")
        actual_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        if record.get("output_sha256") != actual_hash:
            raise ValueError(f"lane output hash mismatch: {output_path}")
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"lane output is not valid JSON: {output_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"lane output must be a JSON object: {output_path}")
        item = expected[str(record["company_id"])]
        if lane == "verifier":
            expected_metadata = {
                "run_id": run_id,
                "lane": lane,
                "campaign_id": item.get("campaign_id", "legacy"),
                "company_id": item["company_id"],
                "scope": item.get("scope"),
                "scope_version": item.get("scope_version"),
                "scope_hash": item.get("scope_hash"),
            }
            for field, expected_value in expected_metadata.items():
                if payload.get(field) != expected_value:
                    raise ValueError(f"verifier output scope mismatch for {output_path}: {field}")
            decisions = payload.get("decisions", [])
            if not isinstance(decisions, list) or any(not isinstance(decision, dict) for decision in decisions):
                raise ValueError(f"verifier output decisions are not objects: {output_path}")
            claims_path = Path(str(item.get("claims_path") or ""))
            if not claims_path.exists():
                raise ValueError(f"verifier claims input is missing: {claims_path}")
            claims_hash = hashlib.sha256(claims_path.read_bytes()).hexdigest()
            if payload.get("claims_input_sha256") != claims_hash:
                raise ValueError(f"verifier claims input hash mismatch: {claims_path}")
            expected_claims: dict[str, str] = {}
            for line in claims_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                claim = json.loads(line)
                if not isinstance(claim, dict):
                    raise ValueError(f"verifier claims input is not an object: {claims_path}")
                claim_id = str(claim.get("candidate_claim_id") or "")
                claim_hash = str(claim.get("candidate_sha256") or "")
                if not claim_id or not claim_hash or claim_id in expected_claims:
                    raise ValueError(f"verifier claims input has invalid or duplicate claim: {claims_path}")
                expected_claims[claim_id] = claim_hash
            seen_decisions: set[str] = set()
            for decision in decisions:
                claim_id = str(decision.get("candidate_claim_id") or "")
                if claim_id in seen_decisions:
                    raise ValueError(f"verifier output has duplicate decision: {claim_id}")
                if claim_id not in expected_claims:
                    raise ValueError(f"verifier output contains foreign decision: {claim_id}")
                if str(decision.get("candidate_sha256") or "") != expected_claims[claim_id]:
                    raise ValueError(f"verifier output hash mismatch: {claim_id}")
                seen_decisions.add(claim_id)
            missing_decisions = sorted(set(expected_claims) - seen_decisions)
            if missing_decisions:
                raise ValueError(f"verifier output missing decisions: {', '.join(missing_decisions)}")
            continue
        research_run = payload.get("research_run", payload)
        if not isinstance(research_run, dict):
            raise ValueError(f"worker output lacks research_run: {output_path}")
        try:
            RESEARCH_VALIDATOR.validate(research_run)
        except jsonschema.ValidationError as exc:
            raise ValueError(f"worker research_run schema invalid: {output_path}: {exc.message}") from exc
        expected_values = {
            "run_id": f"{run_id}:{lane}:{item['company_id']}",
            "campaign_id": item.get("campaign_id", "legacy"),
            "company_id": item["company_id"],
            "scope": item.get("scope"),
            "scope_version": item.get("scope_version"),
            "scope_hash": item.get("scope_hash"),
        }
        for field, expected_value in expected_values.items():
            if research_run.get(field) != expected_value:
                raise ValueError(f"worker output scope mismatch for {output_path}: {field}")
        claims = payload.get("claims", [])
        if not isinstance(claims, list) or any(not isinstance(claim, dict) for claim in claims):
            raise ValueError(f"worker output claims are not objects: {output_path}")
