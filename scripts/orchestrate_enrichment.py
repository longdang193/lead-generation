from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from campaign_spec import CampaignSpec, admit_work_item, load_campaign_spec
from lead_contract import candidate_sha256, run_scope_matches
from run_manifest import atomic_write, entry, load as load_manifest, portable_path, repository_root, update as update_manifest


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def implementation_status(root: Path) -> str:
    lines = git_output(root, "status", "--porcelain").splitlines()
    preserved = {"lead-generation-architecture.json", "output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx"}
    return "\n".join(line for line in lines if line[3:] not in preserved)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_entry(root: Path, path: Path) -> dict[str, str]:
    return entry(root, path)


def _default_campaign_config(root: Path) -> Path:
    return Path("config") / "campaigns" / "berlin-hausverwaltung.json"


def _manifest_campaign(root: Path, manifest: dict[str, object]) -> CampaignSpec:
    record = manifest.get("campaign")
    if not isinstance(record, dict):
        raise ValueError("manifest campaign binding is missing")
    raw_path = record.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("manifest campaign path is missing")
    spec = load_campaign_spec(root, Path(raw_path))
    if record.get("campaign_id") != spec.campaign_id or record.get("version") != spec.version:
        raise ValueError("manifest campaign identity does not match campaign config")
    if record.get("sha256") != spec.sha256:
        raise ValueError("manifest campaign hash mismatch")
    if record.get("normalized") != spec.normalized:
        raise ValueError("manifest normalized campaign config mismatch")
    return spec


def create_run_manifest(root: Path, output: Path, run_id: str | None, inputs: list[Path], supporting_inputs: list[Path], *, accepted_company_ids: set[str] | None = None, campaign_config: Path | None = None, require_clean: bool = True) -> dict[str, object]:
    head_sha = git_output(root, "rev-parse", "HEAD")
    if len(head_sha) != 40:
        raise ValueError("HEAD is not a full 40-character commit SHA")
    if require_clean and implementation_status(root):
        raise ValueError("implementation worktree must be clean before opening research queues")
    campaign = load_campaign_spec(root, campaign_config or _default_campaign_config(root))
    run_id = run_id or f"lead-{uuid.uuid4().hex[:16]}"
    manifest = {
        "run_id": run_id,
        "generated_at": stamp(),
        "head_sha": head_sha,
        "git_revision": head_sha,
        "git_ref": git_output(root, "branch", "--show-current"),
        "status": "prepared",
        "config_version": "lead-enrichment-run-v1",
        "campaign": campaign.manifest_record(),
        "accepted_company_ids": sorted(accepted_company_ids or set()),
        "inputs": {path.stem: manifest_entry(root, path) for path in inputs},
        "supporting_inputs": {path.stem: manifest_entry(root, path) for path in supporting_inputs},
        "queues": {},
        "barriers": {"accepted_identity": True, "provisional_shortlist": False, "research": False, "verifier": False, "verified_evidence": False, "projection": False, "ranking": False, "readiness": False, "published": False},
        "research_runs": {},
        "verifier_runs": {},
        "source_policy": {},
        "projection": {"outputs": {}, "cli_args": {}},
        "outputs": {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def write_lane_queue(
    shortlist_path: Path,
    output_path: Path,
    lane: str,
    run_id: str,
    *,
    campaign_id: str = "legacy",
    accepted_company_ids: set[str] | None = None,
    require_qualification: bool = False,
    company_rows: dict[str, dict[str, str]] | None = None,
    required_location_evidence: str | None = None,
) -> list[dict[str, object]]:
    with shortlist_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    queue = []
    for row in sorted(rows, key=lambda item: str(item.get("company_id") or "")):
        company_id = str(row.get("company_id") or "")
        if not company_id:
            raise ValueError("shortlist row lacks company_id")
        if accepted_company_ids is not None and company_id not in accepted_company_ids:
            raise ValueError(f"shortlist company is not accepted: {company_id}")
        if company_rows is None:
            bound_row = dict(row)
        else:
            canonical_row = company_rows.get(company_id)
            if canonical_row is None:
                raise ValueError(f"shortlist company lacks canonical company binding: {company_id}")
            if str(canonical_row.get("company_id") or "") != company_id:
                raise ValueError(f"canonical company binding has mismatched company_id: {company_id}")
            bound_row = dict(canonical_row)
            if not str(bound_row.get("company_name") or "").strip():
                raise ValueError(f"canonical company binding lacks company_name: {company_id}")
        if require_qualification and str(bound_row.get("resolution_status") or "") != "Accepted":
            raise ValueError(f"shortlist company lacks accepted qualification: {company_id}")
        admitted = admit_work_item(
            bound_row,
            run_id,
            campaign_id,
            lane,
            require_trusted_identity=accepted_company_ids is not None or require_qualification,
            required_location_evidence=required_location_evidence,
        )
        queue.append({**admitted.as_dict(), "status": "pending"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for item in queue:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return queue


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


def verify_manifest(manifest_path: Path, root: Path) -> list[str]:
    manifest = load_manifest(manifest_path)
    errors: list[str] = []
    try:
        _manifest_campaign(root, manifest)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    if (root / ".git").exists():
        head_sha = git_output(root, "rev-parse", "HEAD")
        if manifest.get("head_sha") != head_sha:
            errors.append("HEAD does not match manifest head_sha")
        if implementation_status(root):
            errors.append("implementation worktree is dirty")
    for bucket_name in ("inputs", "supporting_inputs", "outputs"):
        for name, item in manifest.get(bucket_name, {}).items():
            path = (root / str(item.get("path"))).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"manifest path escapes repository: {bucket_name}.{name}")
                continue
            if not path.exists():
                errors.append(f"missing {bucket_name}.{name}")
            elif item.get("sha256") != file_digest(path):
                errors.append(f"hash mismatch {bucket_name}.{name}")
    return errors


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _fixture_inputs(root: Path, shortlist: list[dict[str, str]], run_id: str) -> dict[str, Path]:
    directory = root / "evidence" / "fixture" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    qualification = directory / "qualification.jsonl"
    with qualification.open("w", encoding="utf-8") as handle:
        for row in sorted(shortlist, key=lambda item: item["company_id"]):
            handle.write(json.dumps({"company_id": row["company_id"], "company_name": row.get("company_name", ""), "domain": row.get("domain", ""), "source_url": f"https://{row.get('domain', '')}/", "retrieved_at": "2026-11-08T00:00:00+00:00", "resolution_status": "Accepted", "eligible": True}) + "\n")
    scores = directory / "scores.csv"
    score_fields = ["company_id", "company_name", "domain", "source_url", "service_fit", "residential_weg", "portfolio_size", "portfolio_potential", "berlin_relevance", "structural_lead_fit", "evidence_coverage", "buying_signal", "signal_search_status", "actionability", "sales_priority", "lead_tier", "evidence_urls", "buying_signal_event_ids", "buying_signal_evidence_urls", "retrieved_at"]
    score_rows = [{
        "company_id": row["company_id"], "company_name": row.get("company_name", ""), "domain": row.get("domain", ""), "source_url": f"https://{row.get('domain', '')}",
        "service_fit": "Confirmed", "residential_weg": "Confirmed", "portfolio_size": "Unknown", "portfolio_potential": "Unknown", "berlin_relevance": "Confirmed", "structural_lead_fit": "65", "evidence_coverage": "100", "buying_signal": "Unknown", "signal_search_status": "Searched", "actionability": "Research", "sales_priority": "Research", "lead_tier": "A", "evidence_urls": f"https://{row.get('domain', '')}", "buying_signal_event_ids": "", "buying_signal_evidence_urls": "", "retrieved_at": "2026-11-08T00:00:00+00:00"
    } for row in shortlist]
    _write_csv(scores, score_rows, score_fields)
    contacts = directory / "contacts.csv"
    _write_csv(contacts, [{"company_id": row["company_id"], "company_name": row.get("company_name", ""), "contact_name": "Unknown", "contact_role": "Unknown", "relevance": "Shortlisted account", "contact_email": "Unknown", "email_source": "Unknown", "verification_status": "Unknown", "linkedin_url": "Unknown", "last_verified": "Unknown"} for row in shortlist], ["company_id", "company_name", "contact_name", "contact_role", "relevance", "contact_email", "email_source", "verification_status", "linkedin_url", "last_verified"])
    companies = directory / "companies.csv"
    _write_csv(companies, [{"company_id": row["company_id"], "company_name": row.get("company_name", ""), "domain": row.get("domain", ""), "verified_company_domain": row.get("domain", ""), "city": row.get("city", "Berlin"), "berlin_relevance": "Confirmed", "resolution_status": "Accepted", "source_url": f"https://{row.get('domain', '')}/", "retrieved_at": "2026-11-08T00:00:00+00:00", "evidence_level": "Primary"} for row in shortlist], ["company_id", "company_name", "domain", "verified_company_domain", "city", "berlin_relevance", "resolution_status", "source_url", "retrieved_at", "evidence_level"])
    sources = directory / "sources.csv"
    _write_csv(sources, [{"source_id": f"source-{row['company_id']}", "source_url": f"https://{row.get('domain', '')}"} for row in shortlist], ["source_id", "source_url"])
    website_evidence = directory / "website_evidence.jsonl"
    website_evidence.parent.mkdir(parents=True, exist_ok=True)
    with website_evidence.open("w", encoding="utf-8") as handle:
        for row in shortlist:
            handle.write(json.dumps({"company_id": row["company_id"], "claims": [
                {"field": "service_fit", "evidence_url": f"https://{row.get('domain', '')}/services", "evidence_excerpt": "Hausverwaltung und Immobilienverwaltung für Wohnobjekte in Berlin.", "confidence": "high"},
                {"field": "residential_weg", "evidence_url": f"https://{row.get('domain', '')}/services", "evidence_excerpt": "Verwaltung von Wohnungseigentümergemeinschaften und Wohnimmobilien.", "confidence": "high"},
                {"field": "berlin_relevance", "evidence_url": f"https://{row.get('domain', '')}/", "evidence_excerpt": "Hausverwaltung für Eigentümer in Berlin.", "confidence": "high"},
            ]}) + "\n")
    supporting = {
        "website_evidence": website_evidence,
        "source_register": directory / "sources.csv",
        "entity_resolution": directory / "companies.csv",
        "buying_signal_audit": directory / "signal_audit.csv",
        "buying_events": directory / "events.json",
        "scoring_audit": directory / "scoring_audit.csv",
        "contact_sources": directory / "contacts.csv",
    }
    for path in supporting.values():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]\n" if path.suffix == ".json" else "company_id\n", encoding="utf-8")
    return {"qualification": qualification, "scores": scores, "contacts": contacts, "companies": companies, "sources": sources, **supporting}


def _worker_payloads(records: dict[str, list[dict[str, object]]], queues: dict[str, list[dict[str, object]]] | None = None) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    research_runs: list[dict[str, object]] = []
    claims: list[dict[str, object]] = []
    for lane_records in records.values():
        for record in lane_records:
            output_path = Path(str(record["output_path"]))
            if record.get("status") != "succeeded":
                continue
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            research_run = payload.get("research_run", payload)
            if not isinstance(research_run, dict):
                raise ValueError(f"worker output lacks research_run: {output_path}")
            if queues is not None:
                expected = next((item for item in queues.get(str(record.get("lane")), []) if str(item.get("company_id")) == str(record.get("company_id"))), None)
                if expected is None:
                    raise ValueError(f"worker output is outside admitted queue: {output_path}")
                for field in ("run_id", "company_id", "campaign_id", "scope", "scope_version", "scope_hash"):
                    expected_value = expected.get(field)
                    actual_value = research_run.get(field)
                    if field == "run_id":
                        expected_value = f"{expected_value}:{expected['lane']}:{expected['company_id']}"
                    if actual_value != expected_value:
                        raise ValueError(f"worker output scope mismatch for {output_path}: {field}")
            research_runs.append(research_run)
            output_claims = payload.get("claims", [])
            if not isinstance(output_claims, list):
                raise ValueError(f"worker claims are not a list: {output_path}")
            if any(not isinstance(item, dict) for item in output_claims):
                raise ValueError(f"worker claims contain a non-object record: {output_path}")
            claims.extend(output_claims)
    return research_runs, claims


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _fixture_decisions(claims: list[dict[str, object]], run_id: str) -> list[dict[str, object]]:
    return [{
        "record_type": "VerifierDecision",
        "candidate_claim_id": claim["candidate_claim_id"],
        "candidate_sha256": claim["candidate_sha256"],
        "decision": "Verified",
        "reason_codes": ["fixture_page_local", "fixture_company_bound"],
        "verifier_id": "fixture-verifier",
        "verifier_run_id": f"{run_id}:verifier",
        "verified_at": "2026-11-08T00:00:02+00:00",
    } for claim in claims]


def _native_command_builder(item: dict[str, object], output_path: Path, config: object) -> list[str]:
    return [str(config.executable), *getattr(config, "adapter_args", ()), "--profile", str(config.profile), "--run-id", str(item["run_id"]), "--campaign-id", str(item.get("campaign_id") or "legacy"), "--lane", str(item["lane"]), "--company-id", str(item["company_id"]), "--company-name", str(item.get("company_name") or ""), "--trusted-domain", str(item["trusted_domain"]), "--location", str(item["location"]), "--scope-version", str(item.get("scope_version") or ""), "--scope-hash", str(item["scope_hash"]), "--output", str(output_path)]


def validate_final_priority_rows(priority_rows: list[dict[str, object]], accepted_ids: set[str], target_count: int | None = None) -> None:
    priority_ids = [str(row.get("company_id") or "") for row in priority_rows]
    expected_count = target_count if target_count is not None else len(accepted_ids)
    if len(priority_rows) != expected_count or len(set(priority_ids)) != expected_count or set(priority_ids) != accepted_ids:
        raise ValueError(f"final priority shortlist must contain exactly the admitted {expected_count} companies")


def run_pipeline(root: Path, manifest_path: Path, shortlist_path: Path, *, campaign_config: Path | None = None, fixture: bool = False, worker_executable: str | None = None, worker_profile: str = "default", verifier_executable: str | None = None, verifier_profile: str = "evidence-verifier") -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    admission_errors = verify_manifest(manifest_path, root)
    if admission_errors:
        raise ValueError("run admission failed: " + "; ".join(admission_errors))
    campaign = _manifest_campaign(root, manifest)
    if campaign_config is not None and campaign.path != load_campaign_spec(root, campaign_config).path:
        raise ValueError("requested campaign config does not match manifest campaign path")
    run_id = str(manifest["run_id"])
    shortlist = _load_csv(shortlist_path)
    if len(shortlist) != campaign.target_count:
        raise ValueError(f"run requires exactly {campaign.target_count} provisional companies, got {len(shortlist)}")
    recorded_inputs = manifest.get("inputs", {})
    def recorded_path(item: object) -> Path:
        raw = Path(str(item or ""))
        return raw if raw.is_absolute() else (root / raw).resolve()
    recorded_shortlist = [item for item in recorded_inputs.values() if isinstance(item, dict) and recorded_path(item.get("path")) == shortlist_path.resolve()]
    if len(recorded_shortlist) != 1 or recorded_shortlist[0].get("sha256") != file_digest(shortlist_path):
        raise ValueError("provisional shortlist is not the manifest-bound input")
    accepted_ids = {str(value) for value in manifest.get("accepted_company_ids", [])}
    shortlist_ids = {str(row.get("company_id") or "") for row in shortlist}
    if accepted_ids != shortlist_ids or len(accepted_ids) != campaign.target_count:
        raise ValueError(f"manifest accepted company scope does not exactly match the provisional {campaign.target_count}-company shortlist")
    fixture_inputs = _fixture_inputs(root, shortlist, run_id) if fixture else {
        name: root / relative_path for name, relative_path in campaign.input_bindings.items()
    }
    scripts_dir = Path(__file__).resolve().parent
    worker_adapter_args: tuple[str, ...] = ()
    verifier_adapter_args: tuple[str, ...] = ()
    if not fixture and not worker_executable:
        worker_executable = sys.executable
        worker_adapter_args_list = [str(scripts_dir / "native_worker.py"), "--repo-root", str(root)]
        for argument, key in (("--website-evidence", "qualification"), ("--contacts-input", "contacts"), ("--companies-input", "companies"), ("--events-input", "buying_events"), ("--event-links-input", "event_links")):
            if key in fixture_inputs:
                worker_adapter_args_list.extend((argument, str(fixture_inputs[key])))
        worker_adapter_args = tuple(worker_adapter_args_list)
    if not fixture and not verifier_executable:
        verifier_executable = sys.executable
        verifier_adapter_args = (str(scripts_dir / "native_verifier.py"), "--repo-root", str(root))
    queue_dir = root / "evidence" / "queues" / run_id
    company_rows = {str(row.get("company_id") or ""): row for row in _load_csv(fixture_inputs["companies"]) if row.get("company_id")}
    required_location_evidence = str(campaign.qualification.get("berlin_relevance") or "").strip() or None
    queues = {}
    for lane in campaign.lanes:
        queue_path = queue_dir / f"{lane}.jsonl"
        queues[lane] = write_lane_queue(
            shortlist_path,
            queue_path,
            lane,
            run_id,
            campaign_id=campaign.campaign_id,
            accepted_company_ids=accepted_ids,
            require_qualification=True,
            company_rows=company_rows,
            required_location_evidence=required_location_evidence,
        )
    admitted_items = [item for lane in campaign.lanes for item in queues[lane]]
    domain_by_company = {str(item["company_id"]): str(item["trusted_domain"]) for item in admitted_items}
    update_manifest_file(manifest_path, root, inputs=fixture_inputs, outputs={f"queue_{lane}": queue_dir / f"{lane}.jsonl" for lane in queues}, registries={"execution_mode": "fixture" if fixture else "production", "admitted_work_items": admitted_items, "source_policy": {"allowed_domains": sorted(set(domain_by_company.values())), "company_domains": domain_by_company}}, status="queued", barriers={"provisional_shortlist": True})
    from worker_dispatch import NativeExecutorConfig, dispatch_fixture_lanes, dispatch_native_lane, reconcile_lane_outputs
    if fixture:
        results = dispatch_fixture_lanes(queues, run_id, root / "evidence" / "candidate" / run_id)
    else:
        worker_config = NativeExecutorConfig(worker_executable, worker_profile, adapter_args=worker_adapter_args)
        results = {lane: dispatch_native_lane(queues[lane], run_id, lane, root / "evidence" / "candidate" / run_id / lane, worker_config, command_builder=_native_command_builder) for lane in queues}
    for lane, records in results.items():
        reconcile_lane_outputs(records, queues[lane], run_id, lane)
    research_runs, claims = _worker_payloads(results, queues)
    candidate_path = root / "evidence" / "candidate" / run_id / "claims.jsonl"
    decision_path = root / "evidence" / "verifier" / run_id / "decisions.jsonl"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(candidate_path, claims)
    verifier_run_id = f"{run_id}:verifier"
    verifier_capability = "replay" if fixture else "structural_validation"
    if fixture:
        decisions = _fixture_decisions(claims, run_id)
    else:
        verifier_input_dir = root / "evidence" / "verifier" / run_id / "inputs"
        verifier_queue = []
        claims_by_company: dict[str, list[dict[str, object]]] = {}
        for claim in claims:
            claims_by_company.setdefault(str(claim["company_id"]), []).append(claim)
        for company_id in sorted(accepted_ids):
            claims_path = verifier_input_dir / f"{company_id}.jsonl"
            _write_jsonl(claims_path, claims_by_company.get(company_id, []))
            admitted = next((item for item in admitted_items if str(item["company_id"]) == company_id), None)
            if admitted is None:
                raise ValueError(f"accepted company lacks admitted work item: {company_id}")
            verifier_queue.append({**admitted, "lane": "verifier", "claims_path": claims_path})
        def verifier_command_builder(item: dict[str, object], output_path: Path, config: object) -> list[str]:
            return _native_command_builder(item, output_path, config) + ["--claims", str(item["claims_path"])]
        verifier_config = NativeExecutorConfig(verifier_executable, verifier_profile, adapter_args=verifier_adapter_args)
        verifier_results = dispatch_native_lane(verifier_queue, run_id, "verifier", root / "evidence" / "verifier" / run_id / "outputs", verifier_config, command_builder=verifier_command_builder)
        reconcile_lane_outputs(verifier_results, verifier_queue, run_id, "verifier")
        decisions = []
        for record in verifier_results:
            if record.get("status") != "succeeded":
                continue
            payload = json.loads(Path(str(record["output_path"])).read_text(encoding="utf-8"))
            if payload.get("adapter_capability") != verifier_capability:
                raise ValueError("verifier output capability does not match the configured adapter")
            output_decisions = payload.get("decisions", payload if isinstance(payload, list) else [])
            if not isinstance(output_decisions, list):
                raise ValueError("verifier output decisions are not a list")
            decisions.extend(item for item in output_decisions if isinstance(item, dict))
    _write_jsonl(decision_path, decisions)
    research_registry = {
        str(run["run_id"]): {**dict(run), "research_run_id": run["run_id"]}
        for run in research_runs
    }
    verifier_registry = {verifier_run_id: {"verifier_run_id": verifier_run_id, "verifier_id": "fixture-verifier" if fixture else verifier_profile, "status": "Completed", "capability": verifier_capability, "decision_count": len(decisions)}}
    update_manifest_file(manifest_path, root, inputs={"candidate_evidence": candidate_path, "verifier_decisions": decision_path}, registries={"accepted_company_ids": sorted(accepted_ids), "research_runs": research_registry, "verifier_runs": verifier_registry}, status="research_complete", barriers={"research": True, "verifier": True})
    from promote_evidence import promote_verified_claims
    verified_path = root / "evidence" / "verified" / run_id / "claims.jsonl"
    promote_verified_claims(candidate_path, decision_path, verified_path, manifest_path)
    update_manifest_file(manifest_path, root, outputs={"verified_evidence": verified_path}, status="evidence_promoted", barriers={"verified_evidence": True})
    from canonical_projection import project_verified_evidence
    canonical = project_verified_evidence(verified_path, fixture_inputs["qualification"], fixture_inputs["scores"], fixture_inputs["contacts"], root / "data" / "processed" / run_id, run_id=run_id, manifest_path=manifest_path, root=root)
    scoring_audit = root / "evidence" / "reports" / run_id / "scoring_audit.csv"
    scripts_dir = Path(__file__).resolve().parent
    score_command = [sys.executable, str(scripts_dir / "score_leads.py"), "--qualification", str(canonical["qualification"]), "--events", str(canonical["events"]), "--event-links", str(canonical["event_links"]), "--signal-audit", str(canonical["signal_audit"]), "--output", str(canonical["scores"]), "--audit-output", str(scoring_audit)]
    subprocess.run(score_command, cwd=root, check=True, capture_output=True, text=True)
    update_manifest_file(manifest_path, root, outputs={"scores": canonical["scores"], "scoring_audit": scoring_audit}, supporting_inputs={"website_evidence": fixture_inputs.get("website_evidence", fixture_inputs["qualification"]), "source_register": fixture_inputs.get("source_register", fixture_inputs["sources"]), "entity_resolution": fixture_inputs.get("entity_resolution", fixture_inputs["companies"]), "buying_signal_audit": canonical["signal_audit"], "buying_events": canonical["events"], "scoring_audit": scoring_audit, "contact_sources": fixture_inputs.get("contact_sources", fixture_inputs["contacts"])}, status="scored", barriers={"projection": True, "ranking": False})
    with canonical["scores"].open(encoding="utf-8-sig", newline="") as handle:
        projected_scores = list(csv.DictReader(handle))
    qualification = {row["company_id"]: row for row in _load_records_jsonl(canonical["qualification"])}
    from select_for_enrichment import select_accounts, write_provisional_shortlist
    priority_rows = select_accounts(projected_scores, qualification, campaign.target_count, accepted_ids)
    validate_final_priority_rows(priority_rows, accepted_ids, campaign.target_count)
    priority_path = root / "data" / "processed" / run_id / "priority.csv"
    shortlist_audit_path = root / "evidence" / "audits" / run_id / "shortlist.csv"
    write_provisional_shortlist(priority_rows, priority_path, shortlist_audit_path)
    update_manifest_file(manifest_path, root, outputs={"priority": priority_path, "shortlist_audit": shortlist_audit_path}, status="ranked", barriers={"ranking": True})
    staging = root / "output" / f"{run_id}.staging.xlsx"
    final_output = root / "output" / f"{run_id}.xlsx"
    build_report = root / "evidence" / "reports" / run_id / "build.json"
    build_report.parent.mkdir(parents=True, exist_ok=True)
    build_command = [sys.executable, str(scripts_dir / "build_workbook.py"), "--companies", str(fixture_inputs["companies"]), "--scores", str(canonical["scores"]), "--priority", str(priority_path), "--contacts", str(canonical["contacts"]), "--sources", str(fixture_inputs["sources"]), "--output", str(staging), "--build-report", str(build_report), "--run-manifest", str(manifest_path)]
    subprocess.run(build_command, cwd=root, check=True, capture_output=True, text=True)
    validator = subprocess.run([sys.executable, str(scripts_dir / "validate_workbook.py"), "--workbook", str(staging)], cwd=root, check=False, capture_output=True, text=True)
    if validator.returncode:
        raise RuntimeError(validator.stdout + validator.stderr)
    qa_report = root / "evidence" / "reports" / run_id / "qa.md"
    qa_sample = root / "evidence" / "reports" / run_id / "qa.csv"
    schema_path = root / "config" / "lead_generation_schema.json"
    if not schema_path.exists():
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).resolve().parents[1] / "config" / "lead_generation_schema.json", schema_path)
    update_manifest_file(manifest_path, root, supporting_inputs={"schema": schema_path}, outputs={"workbook": staging, "build_report": build_report}, status="ready_for_validation", barriers={"projection": True})
    qa_command = [sys.executable, str(scripts_dir / "qa_leads.py"), "--workbook", str(staging), "--schema", str(schema_path), "--evidence-dir", str(root / "evidence"), "--website-evidence", str(fixture_inputs.get("website_evidence", fixture_inputs["qualification"])), "--report", str(qa_report), "--sample-output", str(qa_sample), "--run-manifest", str(manifest_path)]
    qa_result = subprocess.run(qa_command, cwd=root, check=False, capture_output=True, text=True)
    if qa_result.returncode:
        report_text = qa_report.read_text(encoding="utf-8") if qa_report.exists() else ""
        raise RuntimeError(qa_result.stdout + qa_result.stderr + report_text)
    update_manifest_file(manifest_path, root, outputs={"qa_report": qa_report, "qa_sample": qa_sample}, status="ready_for_validation", barriers={"readiness": True})
    reachability_flag = ["--allow-unreachable-revision"] if not (root / ".git").exists() else []
    deliverable_check = subprocess.run([sys.executable, str(scripts_dir / "validate_deliverables.py"), "--workbook", str(staging), "--deck", str(root / "output" / "missing-fixture-deck.pptx"), "--qa-report", str(qa_report), "--run-manifest", str(manifest_path), "--workbook-only", *reachability_flag], cwd=root, check=False, capture_output=True, text=True)
    if deliverable_check.returncode:
        raise RuntimeError(deliverable_check.stdout + deliverable_check.stderr)
    final_output.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging, final_output)
    update_manifest_file(manifest_path, root, outputs={"workbook": final_output}, status="completed", barriers={"readiness": True, "published": True})
    return {"run_id": run_id, "workbook": final_output, "priority": priority_path, "qa_report": qa_report}


def _load_records_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def update_manifest_file(manifest_path: Path, root: Path, **kwargs: object) -> dict[str, object]:
    return update_manifest(manifest_path, root, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--root", type=Path, default=Path.cwd())
    create.add_argument("--manifest", type=Path, required=True)
    create.add_argument("--run-id")
    create.add_argument("--input", type=Path, action="append", default=[])
    create.add_argument("--supporting-input", type=Path, action="append", default=[])
    create.add_argument("--accepted-company-ids", type=Path)
    create.add_argument("--campaign-config", type=Path, default=_default_campaign_config(Path.cwd()))
    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--root", type=Path, default=Path.cwd())
    run = subparsers.add_parser("run")
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--shortlist", type=Path, required=True)
    run.add_argument("--accepted-company-ids", type=Path)
    run.add_argument("--campaign-config", type=Path, default=_default_campaign_config(Path.cwd()))
    run.add_argument("--fixture", action="store_true")
    run.add_argument("--worker-executable")
    run.add_argument("--worker-profile", default="default")
    run.add_argument("--verifier-executable")
    run.add_argument("--verifier-profile", default="evidence-verifier")
    args = parser.parse_args()
    if args.command == "create":
        accepted_ids = set()
        if args.accepted_company_ids:
            accepted_ids = {str(row.get("company_id") or "") for row in _load_csv(args.accepted_company_ids) if row.get("company_id")}
        print(json.dumps(create_run_manifest(args.root, args.manifest, args.run_id, args.input, args.supporting_input, accepted_company_ids=accepted_ids, campaign_config=args.campaign_config), indent=2))
        return 0
    if args.command == "run":
        root = args.root.resolve()
        try:
            result = run_pipeline(root, args.manifest, args.shortlist, campaign_config=args.campaign_config, fixture=args.fixture, worker_executable=args.worker_executable, worker_profile=args.worker_profile, verifier_executable=args.verifier_executable, verifier_profile=args.verifier_profile)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"ERROR: {exc}")
            return 1
        print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
        return 0
    errors = verify_manifest(args.manifest, args.root)
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
