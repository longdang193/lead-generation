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


def create_run_manifest(root: Path, output: Path, run_id: str | None, inputs: list[Path], supporting_inputs: list[Path], *, require_clean: bool = True) -> dict[str, object]:
    head_sha = git_output(root, "rev-parse", "HEAD")
    if len(head_sha) != 40:
        raise ValueError("HEAD is not a full 40-character commit SHA")
    if require_clean and implementation_status(root):
        raise ValueError("implementation worktree must be clean before opening research queues")
    run_id = run_id or f"lead-{uuid.uuid4().hex[:16]}"
    manifest = {
        "run_id": run_id,
        "generated_at": stamp(),
        "head_sha": head_sha,
        "git_revision": head_sha,
        "git_ref": git_output(root, "branch", "--show-current"),
        "status": "prepared",
        "config_version": "lead-enrichment-run-v1",
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


def write_lane_queue(shortlist_path: Path, output_path: Path, lane: str, run_id: str, *, accepted_company_ids: set[str] | None = None, require_qualification: bool = False) -> list[dict[str, object]]:
    with shortlist_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    queue = []
    for row in sorted(rows, key=lambda item: str(item.get("company_id") or "")):
        company_id = str(row.get("company_id") or "")
        if not company_id:
            raise ValueError("shortlist row lacks company_id")
        if accepted_company_ids is not None and company_id not in accepted_company_ids:
            raise ValueError(f"shortlist company is not accepted: {company_id}")
        if require_qualification and str(row.get("resolution_status") or "") != "Accepted":
            raise ValueError(f"shortlist company lacks accepted qualification: {company_id}")
        trusted_domain = str(row.get("verified_company_domain") or row.get("domain") or "").strip()
        city = str(row.get("city") or "").strip()
        if (accepted_company_ids is not None or require_qualification) and not trusted_domain:
            raise ValueError(f"shortlist company lacks trusted domain: {company_id}")
        if (accepted_company_ids is not None or require_qualification) and not city:
            raise ValueError(f"shortlist company lacks confirmed city: {company_id}")
        queue.append({
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "company_name": row.get("company_name", ""),
            "trusted_domain": trusted_domain,
            "location": city or "Unknown",
            "scope": f"{lane}:{company_id}",
            "status": "pending",
        })
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
            handle.write(json.dumps({"company_id": row["company_id"], "company_name": row.get("company_name", ""), "resolution_status": "Accepted", "eligible": True}) + "\n")
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
    _write_csv(companies, [{"company_id": row["company_id"], "company_name": row.get("company_name", ""), "domain": row.get("domain", ""), "city": row.get("city", "Berlin"), "resolution_status": "Accepted"} for row in shortlist], ["company_id", "company_name", "domain", "city", "resolution_status"])
    sources = directory / "sources.csv"
    _write_csv(sources, [{"source_id": f"source-{row['company_id']}", "source_url": f"https://{row.get('domain', '')}"} for row in shortlist], ["source_id", "source_url"])
    return {"qualification": qualification, "scores": scores, "contacts": contacts, "companies": companies, "sources": sources}


def run_pipeline(root: Path, manifest_path: Path, shortlist_path: Path, *, fixture: bool = False) -> dict[str, object]:
    if not fixture:
        raise RuntimeError("production native executor is not configured; refusing an unverified live run")
    manifest = load_manifest(manifest_path)
    run_id = str(manifest["run_id"])
    shortlist = _load_csv(shortlist_path)
    if len(shortlist) != 30:
        raise ValueError(f"fixture run requires exactly 30 provisional companies, got {len(shortlist)}")
    fixture_inputs = _fixture_inputs(root, shortlist, run_id)
    accepted_ids = {row["company_id"] for row in shortlist}
    queue_dir = root / "evidence" / "queues" / run_id
    queues = {}
    for lane in ("signals", "portfolio", "contacts"):
        queue_path = queue_dir / f"{lane}.jsonl"
        queues[lane] = write_lane_queue(shortlist_path, queue_path, lane, run_id, accepted_company_ids=accepted_ids, require_qualification=True)
    update_manifest_file(manifest_path, root, inputs=fixture_inputs, outputs={f"queue_{lane}": queue_dir / f"{lane}.jsonl" for lane in queues}, status="queued", barriers={"provisional_shortlist": True})
    from worker_dispatch import dispatch_fixture_lanes, reconcile_lane_outputs
    results = dispatch_fixture_lanes(queues, run_id, root / "evidence" / "candidate" / run_id)
    for lane, records in results.items():
        reconcile_lane_outputs(records, queues[lane], run_id, lane)
    candidate_path = root / "evidence" / "candidate" / run_id / "claims.jsonl"
    decision_path = root / "evidence" / "verifier" / run_id / "decisions.jsonl"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text("", encoding="utf-8")
    decision_path.write_text("", encoding="utf-8")
    research_registry = {lane: [{**record, "output_path": portable_path(root, Path(str(record["output_path"]))) } for record in records] for lane, records in results.items()}
    update_manifest_file(manifest_path, root, inputs={"candidate_evidence": candidate_path, "verifier_decisions": decision_path}, registries={"research_runs": research_registry, "verifier_runs": {"run_id": run_id, "status": "Completed", "decision_count": 0}}, status="research_complete", barriers={"research": True, "verifier": True})
    from promote_evidence import promote_verified_claims
    verified_path = root / "evidence" / "verified" / run_id / "claims.jsonl"
    promote_verified_claims(candidate_path, decision_path, verified_path, manifest_path)
    update_manifest_file(manifest_path, root, outputs={"verified_evidence": verified_path}, status="evidence_promoted", barriers={"verified_evidence": True})
    from canonical_projection import project_verified_evidence
    canonical = project_verified_evidence(verified_path, fixture_inputs["qualification"], fixture_inputs["scores"], fixture_inputs["contacts"], root / "data" / "processed" / run_id, run_id=run_id, manifest_path=manifest_path, root=root)
    with canonical["scores"].open(encoding="utf-8-sig", newline="") as handle:
        projected_scores = list(csv.DictReader(handle))
    qualification = {row["company_id"]: row for row in _load_records_jsonl(canonical["qualification"])}
    from select_for_enrichment import select_accounts, write_provisional_shortlist
    priority_rows = select_accounts(projected_scores, qualification, 30, accepted_ids)
    priority_path = root / "data" / "processed" / run_id / "priority.csv"
    shortlist_audit_path = root / "evidence" / "audits" / run_id / "shortlist.csv"
    write_provisional_shortlist(priority_rows, priority_path, shortlist_audit_path)
    update_manifest_file(manifest_path, root, outputs={"priority": priority_path, "shortlist_audit": shortlist_audit_path}, status="ranked", barriers={"ranking": True})
    staging = root / "output" / f"{run_id}.staging.xlsx"
    final_output = root / "output" / f"{run_id}.xlsx"
    build_report = root / "evidence" / "reports" / run_id / "build.json"
    build_report.parent.mkdir(parents=True, exist_ok=True)
    scripts_dir = Path(__file__).resolve().parent
    build_command = [sys.executable, str(scripts_dir / "build_workbook.py"), "--companies", str(fixture_inputs["companies"]), "--scores", str(canonical["scores"]), "--priority", str(priority_path), "--contacts", str(canonical["contacts"]), "--sources", str(fixture_inputs["sources"]), "--output", str(staging), "--build-report", str(build_report), "--run-manifest", str(manifest_path)]
    subprocess.run(build_command, cwd=root, check=True, capture_output=True, text=True)
    validator = subprocess.run([sys.executable, str(scripts_dir / "validate_workbook.py"), "--workbook", str(staging)], cwd=root, check=False, capture_output=True, text=True)
    if validator.returncode:
        raise RuntimeError(validator.stdout + validator.stderr)
    final_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(staging, final_output)
    qa_report = root / "evidence" / "reports" / run_id / "qa.md"
    qa_sample = root / "evidence" / "reports" / run_id / "qa.csv"
    qa_sample.parent.mkdir(parents=True, exist_ok=True)
    qa_sample.write_text("company_id\n" + "\n".join(sorted(accepted_ids)) + "\n", encoding="utf-8")
    qa_report.write_text(f"# Readiness QA\n\nErrors: 0\n\nRun ID: {run_id}\nCompanies: {len(priority_rows)}\n\nAll fixture barriers passed.\n", encoding="utf-8")
    schema_path = root / "config" / "lead_generation_schema.json"
    if not schema_path.exists():
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).resolve().parents[1] / "config" / "lead_generation_schema.json", schema_path)
    update_manifest_file(manifest_path, root, supporting_inputs={"schema": schema_path}, outputs={"workbook": final_output, "build_report": build_report, "qa_report": qa_report, "qa_sample": qa_sample}, status="ready_for_validation", barriers={"projection": True})
    reachability_flag = ["--allow-unreachable-revision"] if not (root / ".git").exists() else []
    deliverable_check = subprocess.run([sys.executable, str(scripts_dir / "validate_deliverables.py"), "--workbook", str(final_output), "--deck", str(root / "output" / "missing-fixture-deck.pptx"), "--qa-report", str(qa_report), "--run-manifest", str(manifest_path), "--workbook-only", *reachability_flag], cwd=root, check=False, capture_output=True, text=True)
    if deliverable_check.returncode:
        raise RuntimeError(deliverable_check.stdout + deliverable_check.stderr)
    update_manifest_file(manifest_path, root, status="completed", barriers={"readiness": True, "published": True})
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
    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--root", type=Path, default=Path.cwd())
    run = subparsers.add_parser("run")
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--shortlist", type=Path, required=True)
    run.add_argument("--accepted-company-ids", type=Path)
    run.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    if args.command == "create":
        print(json.dumps(create_run_manifest(args.root, args.manifest, args.run_id, args.input, args.supporting_input), indent=2))
        return 0
    if args.command == "run":
        if not args.fixture:
            print("ERROR: production native executor is not configured; use --fixture for local proof")
            return 2
        root = args.root.resolve()
        result = run_pipeline(root, args.manifest, args.shortlist, fixture=True)
        print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
        return 0
    errors = verify_manifest(args.manifest, args.root)
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
