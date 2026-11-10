from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping

from openpyxl import load_workbook

from lead_contract import has_complete_production_lineage


FULL_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def repository_root(start: Path) -> Path:
    candidate = start.resolve()
    for path in (candidate, *candidate.parents):
        if (path / ".git").exists():
            return path
        if path.name == "manifests" and path.parent.name == "evidence":
            return path.parent.parent
    return candidate


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def validate_manifest_revision(
    root: Path,
    manifest: Mapping[str, object],
    *,
    require_current: bool = True,
) -> list[str]:
    errors: list[str] = []
    recorded = str(manifest.get("git_revision") or manifest.get("head_sha") or "")
    head_sha = str(manifest.get("head_sha") or "")
    if not FULL_COMMIT_SHA.fullmatch(recorded):
        errors.append("run manifest missing full Git revision")
    if head_sha and recorded and head_sha != recorded:
        errors.append(f"run manifest revision fields disagree: git_revision={recorded}, head_sha={head_sha}")
    current = git_revision(root)
    if current:
        try:
            subprocess.run(
                ["git", "-C", str(root), "cat-file", "-e", f"{recorded}^{{commit}}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            errors.append(f"run manifest Git revision is not reachable: {recorded}")
        if require_current and recorded != current:
            errors.append(f"run manifest Git revision mismatch: expected current HEAD {current}, observed {recorded}")
    return errors


def manifest_path(root: Path, manifest: Path) -> Path:
    return manifest.resolve() if manifest.is_absolute() else (root / manifest).resolve()


def portable_path(root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside repository root: {resolved}") from exc


def entry(root: Path, path: Path, *, format: str | None = None) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    result = {"path": portable_path(root, resolved), "sha256": file_sha256(resolved)}
    if format:
        result["format"] = format
    return result


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("run manifest must be a JSON object")
    return value


def prepare_run(path: Path, root: Path) -> dict[str, object]:
    """Admit a manifest for a native action without dispatching work."""

    manifest = load(path)
    errors = validate_manifest_revision(root, manifest)
    if errors:
        raise ValueError("run admission failed: " + "; ".join(errors))
    if not manifest.get("run_id") or not manifest.get("head_sha"):
        raise ValueError("manifest identity is incomplete")
    return manifest


def atomic_write(path: Path, manifest: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def publication_marker_path(root: Path, run_id: str) -> Path:
    return root / "output" / f"{run_id}.publication.json"


def _marker_paths(root: Path, marker: Mapping[str, object]) -> tuple[Path, Path]:
    root_resolved = root.resolve()

    def marker_path_value(name: str) -> Path:
        raw = str(marker.get(name) or "")
        if not raw:
            raise ValueError(f"publication recovery marker is missing {name}")
        resolved = (root / raw).resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"publication recovery {name} escapes repository root") from exc
        return resolved

    return marker_path_value("staging_path"), marker_path_value("final_path")


def _bind_workbook_output(manifest: dict[str, object], root: Path, workbook: Path, sha256: str) -> dict[str, object]:
    outputs = manifest.get("outputs")
    bound_outputs = dict(outputs) if isinstance(outputs, dict) else {}
    bound_outputs["workbook"] = {
        "path": workbook.resolve().relative_to(root.resolve()).as_posix(),
        "sha256": sha256,
    }
    manifest["outputs"] = bound_outputs
    return manifest


def _publication_status_errors(status: str, manifest: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    if status not in {"complete", "completed", "partial"}:
        errors.append(f"publication status is not terminal: {status}")
        return errors
    delivery = manifest.get("delivery")
    delivery_status = str(delivery.get("status") or "") if isinstance(delivery, dict) else ""
    if status in {"complete", "completed"} and delivery_status not in {"complete", "completed"}:
        errors.append("complete publication requires complete delivery")
    if status == "partial" and delivery_status not in {"partial", "blocked"}:
        errors.append("partial publication requires partial delivery")
    return errors


def _validate_publication_artifact(root: Path, manifest: Mapping[str, object], staging: Path, final: Path, expected_hash: str) -> None:
    outputs = manifest.get("outputs")
    workbook = outputs.get("workbook") if isinstance(outputs, dict) else None
    if not isinstance(workbook, dict):
        raise ValueError("manifest workbook artifact is missing")
    recorded_path = Path(str(workbook.get("path") or ""))
    recorded_path = recorded_path if recorded_path.is_absolute() else (root / recorded_path)
    recorded_path = recorded_path.resolve()
    if recorded_path not in {staging.resolve(), final.resolve()}:
        raise ValueError("staging artifact does not match the manifest workbook path")
    recorded_hash = str(workbook.get("sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
        raise ValueError("manifest workbook artifact has an invalid hash")
    if recorded_hash != expected_hash:
        raise ValueError("staging artifact does not match the manifest workbook hash")
    source = staging if staging.exists() else final if final.exists() else None
    if source is None or file_sha256(source) != expected_hash:
        raise ValueError("publication artifact hash does not match the staged or final bytes")


def _complete_publication(root: Path, manifest_path: Path, marker_path: Path, marker: Mapping[str, object]) -> None:
    manifest = load(manifest_path)
    run_id = str(manifest.get("run_id") or "")
    if str(marker.get("run_id") or "") != run_id:
        raise ValueError("publication recovery marker run_id mismatch")
    marker_head_sha = str(marker.get("head_sha") or "")
    if marker_head_sha and marker_head_sha != str(manifest.get("head_sha") or ""):
        raise ValueError("publication recovery marker head_sha mismatch")
    revision_errors = validate_manifest_revision(root, manifest, require_current=False)
    if revision_errors:
        raise ValueError("publication recovery revision validation failed: " + "; ".join(revision_errors))
    staging, final = _marker_paths(root, marker)
    expected = str(marker.get("staging_sha256") or "")
    if not expected or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("publication recovery marker has an invalid staging hash")
    campaign = manifest.get("campaign")
    campaign_policy = campaign.get("delivery_policy") if isinstance(campaign, dict) else None
    delivery_policy = str(marker.get("delivery_policy") or manifest.get("delivery_policy") or campaign_policy or "strict")
    status = str(marker.get("status") or manifest.get("status") or "ready_for_validation")
    registries = marker.get("registries")
    if not isinstance(registries, dict):
        registries = {}
    barriers = marker.get("barriers")
    if not isinstance(barriers, dict):
        barriers = {}
    candidate = dict(manifest)
    candidate.update(registries)
    candidate["status"] = status
    candidate_barriers = candidate.get("barriers")
    if not isinstance(candidate_barriers, dict):
        candidate_barriers = {}
    candidate_barriers = {**candidate_barriers, **barriers, "published": True}
    candidate["barriers"] = candidate_barriers
    status_errors = _publication_status_errors(status, candidate)
    if status_errors:
        raise ValueError("publication status validation failed: " + "; ".join(status_errors))
    candidate = _bind_workbook_output(candidate, root, staging if staging.exists() else final, expected)
    proof = reconstruct_finalization_readiness(root, manifest_path, delivery_policy, overlay=candidate)
    if not proof["ready"]:
        raise ValueError("publication finalization admission failed: " + "; ".join(proof["errors"]))
    if staging.exists():
        if file_sha256(staging) != expected:
            raise ValueError("publication recovery found a mismatched staging output")
        os.replace(staging, final)
    elif not final.exists():
        raise ValueError("publication recovery found neither a valid staging nor final output")
    elif file_sha256(final) != expected:
        raise ValueError("publication recovery found a mismatched final output")
    _validate_publication_artifact(root, manifest, staging, final, expected)
    update(
        path=manifest_path,
        root=root,
        outputs={"workbook": final},
        registries=registries,
        status=status,
        barriers=candidate_barriers,
        require_current_revision=False,
    )
    marker_path.unlink()
    return


def recover_publication(root: Path, manifest_path: Path) -> None:
    manifest = load(manifest_path)
    run_id = str(manifest.get("run_id") or "")
    if not run_id:
        return
    marker_path = publication_marker_path(root, run_id)
    if marker_path.exists():
        _complete_publication(root, manifest_path, marker_path, load(marker_path))


def publish_staged_output(
    root: Path,
    manifest_path: Path,
    staging: Path,
    final: Path,
    *,
    status: str,
    registries: Mapping[str, object] | None = None,
    barriers: Mapping[str, object] | None = None,
    delivery_policy: str | None = None,
) -> Path:
    """Publish one validated staging artifact through the shared barrier."""

    manifest = load(manifest_path)
    run_id = str(manifest.get("run_id") or "")
    if not run_id:
        raise ValueError("manifest run_id is required for publication")
    staging = staging.resolve()
    final = final.resolve()
    root_resolved = root.resolve()
    for candidate, label in ((staging, "staging"), (final, "final")):
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"{label} output escapes repository root") from exc
    if not staging.exists():
        raise FileNotFoundError(staging)
    campaign = manifest.get("campaign")
    campaign_policy = campaign.get("delivery_policy") if isinstance(campaign, dict) else None
    policy = delivery_policy or str(manifest.get("delivery_policy") or campaign_policy or "strict")
    candidate = dict(manifest)
    candidate.update(registries or {})
    candidate["status"] = status
    candidate_barriers = candidate.get("barriers")
    if not isinstance(candidate_barriers, dict):
        candidate_barriers = {}
    candidate["barriers"] = {**candidate_barriers, **(barriers or {}), "published": True}
    status_errors = _publication_status_errors(status, candidate)
    if status_errors:
        raise ValueError("publication status validation failed: " + "; ".join(status_errors))
    candidate = _bind_workbook_output(candidate, root, staging, file_sha256(staging))
    proof = reconstruct_finalization_readiness(root, manifest_path, policy, overlay=candidate)
    if not proof["ready"]:
        raise ValueError("publication finalization admission failed: " + "; ".join(proof["errors"]))
    _validate_publication_artifact(root, manifest, staging, final, file_sha256(staging))
    marker_path = publication_marker_path(root, run_id)
    atomic_write(marker_path, {
        "run_id": run_id,
        "head_sha": str(manifest.get("head_sha") or ""),
        "staging_path": staging.relative_to(root_resolved).as_posix(),
        "final_path": final.relative_to(root_resolved).as_posix(),
        "staging_sha256": file_sha256(staging),
        "status": status,
        "delivery_policy": policy,
        "registries": dict(registries or {}),
        "barriers": dict(barriers or {}),
    })
    _complete_publication(root, manifest_path, marker_path, load(marker_path))
    return final


def _validate_finalization_artifacts(
    root: Path,
    manifest: Mapping[str, object],
    outputs: Mapping[str, object],
    artifacts: Mapping[str, Path],
    errors: list[str],
) -> None:
    """Validate semantic relationships between production artifacts before publish."""

    run_id = str(manifest.get("run_id") or "")
    accepted = {str(value) for value in manifest.get("accepted_company_ids", []) if str(value)}

    def json_records(path: Path) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"verified evidence is not valid JSON at line {line_number}")
                continue
            if not isinstance(value, dict):
                errors.append(f"verified evidence record at line {line_number} is not an object")
                continue
            records.append(value)
        return records

    def csv_rows(path: Path, label: str) -> list[dict[str, str]]:
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                fields = reader.fieldnames or []
        except (OSError, csv.Error) as exc:
            errors.append(f"{label} is not readable CSV: {exc}")
            return []
        if "company_id" not in fields:
            errors.append(f"{label} is missing a company_id column")
        return rows

    evidence_ids: set[str] = set()
    evidence_path = artifacts.get("verified_evidence")
    if evidence_path:
        for record in json_records(evidence_path):
            company_id = str(record.get("company_id") or "")
            if not company_id or (accepted and company_id not in accepted):
                errors.append("verified evidence contains a company outside the admitted run scope")
            if not record.get("source_url") or not record.get("evidence_excerpt"):
                errors.append("verified evidence contains an incomplete claim")
            research_run_id = str(record.get("research_run_id") or "")
            if not research_run_id.startswith(f"{run_id}:"):
                errors.append("verified evidence is not bound to the admitted run")
            if company_id:
                evidence_ids.add(company_id)

    scores_ids: set[str] = set()
    scores_path = artifacts.get("scores")
    if scores_path:
        for row in csv_rows(scores_path, "projection scores"):
            company_id = str(row.get("company_id") or "")
            if not company_id:
                errors.append("projection scores contain a row without company_id")
                continue
            scores_ids.add(company_id)
            if accepted and company_id not in accepted:
                errors.append("projection scores contain a company outside the admitted run scope")

    priority_ids: set[str] = set()
    priority_path = artifacts.get("priority")
    if priority_path:
        priority_rows = csv_rows(priority_path, "ranked leads")
        for row in priority_rows:
            company_id = str(row.get("company_id") or "")
            if not company_id:
                errors.append("ranked leads contain a row without company_id")
                continue
            priority_ids.add(company_id)
            if company_id not in scores_ids:
                errors.append("ranked leads contain a company absent from projection scores")
            if accepted and company_id not in accepted:
                errors.append("ranked leads contain a company outside the admitted run scope")
        if str(manifest.get("account_intelligence_mode") or "") == "production":
            dossier_path = artifacts.get("dossier")
            dossier_records = json_records(dossier_path) if dossier_path else []
            dossiers_by_company = {
                str(item.get("company_id") or (item.get("thesis") or {}).get("company_id") or ""): item
                for item in dossier_records
            }
            for row in priority_rows:
                company_id = str(row.get("company_id") or "")
                if not has_complete_production_lineage(row):
                    errors.append(f"ranked leads lack complete dossier lineage: {company_id}")
                dossier = dossiers_by_company.get(company_id)
                if not dossier:
                    errors.append(f"ranked leads lack a matching dossier artifact: {company_id}")
                elif str(row.get("dossier_hash") or "") != str(dossier.get("dossier_hash") or ""):
                    errors.append(f"ranked leads dossier hash does not match dossier artifact: {company_id}")

    if evidence_ids and not evidence_ids.issubset(scores_ids):
        errors.append("projection scores do not cover every verified-evidence company")

    qa_report = artifacts.get("qa_report")
    if qa_report:
        report = qa_report.read_text(encoding="utf-8")
        if not re.search(r"(?m)^- Errors: 0\s*$", report):
            errors.append("QA report is not a zero-error report")
    qa_sample = artifacts.get("qa_sample")
    if qa_sample:
        try:
            with qa_sample.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                sample = list(reader)
                fields = reader.fieldnames or []
            if "company_id" not in fields:
                errors.append("QA sample is missing a company_id column")
            sample_scope = {str(row.get("company_id") or "") for row in sample if row.get("company_id")}
            if accepted and not sample_scope.issubset(accepted):
                errors.append("QA sample contains a company outside the admitted run scope")
            if any(not row.get("lead_tier") for row in sample):
                errors.append("QA sample contains a row without lead_tier")
        except (OSError, csv.Error):
            errors.append("QA sample is not valid CSV")

    workbook_record = outputs.get("workbook")
    if isinstance(workbook_record, dict):
        workbook_path = Path(str(workbook_record.get("path") or ""))
        workbook_path = workbook_path if workbook_path.is_absolute() else root / workbook_path
        workbook = None
        try:
            workbook = load_workbook(workbook_path.resolve(), read_only=True, data_only=True)
            expected_sheets = ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources"]
            if str(manifest.get("account_intelligence_mode") or "") == "production":
                expected_sheets = ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources", "06_Account_Dossiers", "07_Account_Theses", "08_Account_Timeline", "09_Evidence_Ledger", "10_Research_Gaps"]
            if workbook.sheetnames != expected_sheets:
                errors.append("workbook tabs do not match the native export contract")

            def sheet_ids(name: str) -> set[str]:
                if name not in workbook.sheetnames:
                    return set()
                rows = list(workbook[name].values)
                if not rows or not rows[0]:
                    return set()
                headers = [str(value or "") for value in rows[0]]
                if "company_id" not in headers:
                    return set()
                index = headers.index("company_id")
                return {str(row[index]) for row in rows[1:] if len(row) > index and row[index] not in (None, "", "No records")}

            if sheet_ids("02_Qualification") != scores_ids:
                errors.append("workbook qualification rows do not match projection scores")
            if sheet_ids("03_Priority_Leads") != priority_ids:
                errors.append("workbook priority rows do not match ranked leads")
        except Exception as exc:
            errors.append(f"workbook semantic validation failed: {exc}")
        finally:
            if workbook is not None:
                workbook.close()


def reconstruct_finalization_readiness(root: Path, manifest_path: Path, delivery_policy: str, *, overlay: Mapping[str, object] | None = None) -> dict[str, object]:
    """Reconstruct finalization prerequisites from durable evidence, not flags alone."""

    manifest = load(manifest_path)
    existing_barriers = manifest.get("barriers")
    if overlay:
        manifest = {**manifest, **overlay}
        if isinstance(overlay.get("barriers"), Mapping):
            manifest["barriers"] = {
                **(existing_barriers if isinstance(existing_barriers, Mapping) else {}),
                **overlay["barriers"],
            }
    errors: list[str] = []
    run_id = str(manifest.get("run_id") or "")
    lifecycle: dict[str, object] = {}
    if not run_id:
        errors.append("manifest run_id is missing")
    elif str(manifest.get("execution_mode") or "production") == "fixture":
        lifecycle = {"action_count": 0, "actions": [], "budget_reserved": 0, "budget_settled": 0, "coverage": {}, "fixture_replay": True}
    else:
        from action_lifecycle import replay_lifecycle
        try:
            lifecycle = replay_lifecycle(root, run_id)
        except (OSError, ValueError) as exc:
            errors.append(f"lifecycle replay failed: {exc}")
        if not lifecycle.get("action_count"):
            errors.append("finalization requires durable action lifecycle evidence")
        else:
            unsettled = [item for item in lifecycle.get("actions", []) if item.get("settled") is not True]
            if unsettled:
                errors.append("finalization requires all admitted actions to settle")
            accepted_ids = {str(value) for value in manifest.get("accepted_company_ids", []) if str(value)}
            actions = lifecycle.get("actions", []) if isinstance(lifecycle.get("actions"), list) else []
            completed_tuples = {(str(item.get("company_id") or ""), str(item.get("action_type") or ""), str(item.get("scope") or "")) for item in actions if item.get("status") == "Completed" and item.get("settled") is True}
            admitted_items = manifest.get("admitted_work_items", []) if isinstance(manifest.get("admitted_work_items"), list) else []
            required_tuples = {(str(item.get("company_id") or ""), str(item.get("lane") or item.get("action_type") or ""), str(item.get("scope") or "")) for item in admitted_items if isinstance(item, dict)}
            missing_tuples = sorted(required_tuples - completed_tuples)
            if delivery_policy == "strict" and missing_tuples:
                errors.append("durable lifecycle does not cover every admitted work item: " + ", ".join("/".join(item) for item in missing_tuples))
            verifier_ids = {str(item.get("company_id") or "") for item in actions if item.get("action_type") == "verifier" and item.get("status") == "Completed" and item.get("settled") is True}
            if delivery_policy == "strict" and accepted_ids and not accepted_ids.issubset(verifier_ids):
                errors.append("durable lifecycle does not cover every accepted company with a completed verifier action")
            completed_ids = {company_id for company_id, _, _ in completed_tuples}
            recorded_coverage = manifest.get("coverage") or manifest.get("research_coverage")
            if isinstance(recorded_coverage, dict):
                recorded_status = str(recorded_coverage.get("status") or recorded_coverage.get("coverage_status") or "unknown")
                derived_status = "complete" if not accepted_ids or accepted_ids.issubset(completed_ids) else "partial"
                if recorded_status in {"complete", "completed"} and derived_status != "complete":
                    errors.append("recorded coverage claims complete but durable lifecycle coverage is incomplete")
    allowed, policy_errors = finalization_eligibility(manifest, delivery_policy)
    if not allowed:
        errors.extend(policy_errors)
    outputs = manifest.get("outputs")
    if str(manifest.get("execution_mode") or "production") != "fixture":
        required_outputs = {
            "verified_evidence": "verified evidence",
            "scores": "projection scores",
            "priority": "ranked leads",
            "qa_report": "QA report",
            "qa_sample": "QA sample",
        }
        if str(manifest.get("account_intelligence_mode") or "") == "production":
            required_outputs.update({"dossier": "account dossier", "ranking": "ranking audit"})
        output_bucket = outputs if isinstance(outputs, dict) else {}
        validated_artifacts: dict[str, Path] = {}
        for key, label in required_outputs.items():
            artifact = output_bucket.get(key)
            if not isinstance(artifact, dict):
                errors.append(f"finalization requires a recorded {label} artifact")
                continue
            raw_path = str(artifact.get("path") or "")
            raw_hash = str(artifact.get("sha256") or "")
            path = Path(raw_path)
            path = path if path.is_absolute() else root / path
            try:
                path = path.resolve()
                path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{label} artifact path escapes repository root")
                continue
            if not path.exists() or not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", raw_hash) or file_sha256(path) != raw_hash:
                errors.append(f"{label} artifact hash is invalid or stale")
            else:
                validated_artifacts[key] = path
        _validate_finalization_artifacts(root, manifest, output_bucket, validated_artifacts, errors)
        delivery = manifest.get("delivery")
        if isinstance(delivery, dict) and "priority" in validated_artifacts:
            try:
                with validated_artifacts["priority"].open(encoding="utf-8-sig", newline="") as handle:
                    priority_rows = list(csv.DictReader(handle))
                durable_delivered_count = len({str(row.get("company_id") or "") for row in priority_rows if row.get("company_id")})
                if delivery.get("delivered_count") != durable_delivered_count:
                    errors.append("delivery count does not match durable ranked-lead artifact")
                target_count = delivery.get("target_count")
                if isinstance(target_count, int) and not isinstance(target_count, bool) and delivery.get("shortfall") != max(target_count - durable_delivered_count, 0):
                    errors.append("delivery shortfall does not match durable ranked-lead artifact")
            except (OSError, csv.Error):
                errors.append("ranked leads artifact is not readable CSV")
    workbook = outputs.get("workbook") if isinstance(outputs, dict) else None
    if not isinstance(workbook, dict):
        errors.append("finalization requires a recorded workbook artifact")
    else:
        recorded_path = Path(str(workbook.get("path") or ""))
        recorded_path = recorded_path if recorded_path.is_absolute() else root / recorded_path
        recorded_path = recorded_path.resolve()
        recorded_hash = str(workbook.get("sha256") or "")
        if not recorded_path.exists():
            errors.append("recorded workbook artifact is missing")
        elif not re.fullmatch(r"[0-9a-f]{64}", recorded_hash) or file_sha256(recorded_path) != recorded_hash:
            errors.append("recorded workbook artifact hash is invalid or stale")
    return {
        "ready": not errors,
        "errors": errors,
        "run_id": run_id,
        "lifecycle": lifecycle,
        "manifest": manifest,
    }


def finalize_run(
    root: Path,
    manifest_path: Path,
    staging: Path,
    final: Path,
    *,
    status: str,
    delivery_policy: str | None = None,
    registries: Mapping[str, object] | None = None,
    barriers: Mapping[str, object] | None = None,
) -> Path:
    manifest = load(manifest_path)
    campaign = manifest.get("campaign")
    campaign_policy = campaign.get("delivery_policy") if isinstance(campaign, dict) else None
    policy = delivery_policy or str(manifest.get("delivery_policy") or campaign_policy or "strict")
    pending_manifest = dict(registries or {})
    if barriers:
        pending_manifest["barriers"] = dict(barriers)
    proof = reconstruct_finalization_readiness(root, manifest_path, policy, overlay=pending_manifest)
    if not proof["ready"]:
        raise ValueError("finalization readiness proof failed: " + "; ".join(str(item) for item in proof["errors"]))
    return publish_staged_output(root, manifest_path, staging, final, status=status, delivery_policy=policy, registries=registries, barriers=barriers)

def finalization_eligibility(manifest: Mapping[str, object], delivery_policy: str) -> tuple[bool, list[str]]:
    """Check finalization policy without inferring facts from agent claims."""

    if delivery_policy not in {"strict", "personal"}:
        return False, [f"unknown delivery policy: {delivery_policy}"]
    errors: list[str] = []
    if str(manifest.get("account_intelligence_mode") or "") == "production":
        outputs = manifest.get("outputs")
        if not isinstance(outputs, dict):
            errors.append("production account-intelligence finalization requires recorded outputs")
        else:
            for name in ("dossier", "ranking", "workbook"):
                artifact = outputs.get(name)
                if not isinstance(artifact, dict) or not artifact.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("sha256") or "")):
                    errors.append(f"production finalization requires manifest-bound {name} artifact")
    barriers = manifest.get("barriers")
    if not isinstance(barriers, dict):
        errors.append("manifest barriers are missing")
    else:
        for name in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness"):
            if barriers.get(name) is not True:
                errors.append(f"barrier is not complete: {name}")
    coverage = manifest.get("coverage") or manifest.get("research_coverage") or {}
    if isinstance(coverage, dict):
        status = str(coverage.get("status") or coverage.get("coverage_status") or "unknown")
        if delivery_policy == "strict" and status not in {"complete", "completed"}:
            errors.append("strict finalization requires complete policy coverage")
    elif delivery_policy == "strict":
        errors.append("strict finalization requires recorded policy coverage")
    delivery = manifest.get("delivery")
    if not isinstance(delivery, dict):
        errors.append("finalization requires recorded delivery")
    else:
        status = str(delivery.get("status") or "")
        if status not in {"complete", "completed", "partial", "blocked"}:
            errors.append("delivery has an invalid status")
        if delivery_policy == "strict" and status not in {"complete", "completed"}:
            errors.append("strict finalization requires complete delivery")
        if status == "none_found":
            errors.append("None found is not a finalization substitute")
        recorded_policy = str(delivery.get("delivery_policy") or "")
        if recorded_policy != delivery_policy:
            errors.append("delivery policy does not match finalization policy")
        raw_counts = {name: delivery.get(name) for name in ("target_count", "delivered_count", "shortfall")}
        invalid_counts = [
            name for name, value in raw_counts.items()
            if not isinstance(value, int) or isinstance(value, bool) or value < 0
        ]
        if invalid_counts:
            errors.append("delivery counts must be nonnegative integers: " + ", ".join(sorted(invalid_counts)))
        else:
            target_count = raw_counts["target_count"]
            delivered_count = raw_counts["delivered_count"]
            shortfall = raw_counts["shortfall"]
        if invalid_counts:
            errors.append("delivery counts are incomplete")
        else:
            if shortfall != max(target_count - delivered_count, 0):
                errors.append("delivery shortfall is inconsistent with delivery counts")
            if status in {"complete", "completed"} and delivered_count < target_count:
                errors.append("complete delivery is below target count")
            campaign = manifest.get("campaign")
            expected_target = campaign.get("target_count") if isinstance(campaign, dict) else manifest.get("target_count")
            if expected_target is not None:
                try:
                    if target_count != int(expected_target):
                        errors.append("delivery target count does not match the admitted campaign")
                except (TypeError, ValueError):
                    errors.append("admitted campaign target count is invalid")
    if manifest.get("none_found_unqualified") is True:
        errors.append("None found is not allowed for partial or unavailable research")
    return not errors, errors


def update(
    path: Path,
    root: Path,
    *,
    inputs: Mapping[str, Path] | None = None,
    supporting_inputs: Mapping[str, Path] | None = None,
    outputs: Mapping[str, Path] | None = None,
    registries: Mapping[str, object] | None = None,
    status: str | None = None,
    barriers: Mapping[str, object] | None = None,
    require_current_revision: bool = True,
) -> dict[str, object]:
    manifest = load(path)
    if not manifest.get("run_id") or not manifest.get("head_sha"):
        raise ValueError("manifest identity is incomplete")
    manifest.setdefault("git_revision", manifest["head_sha"])
    revision_errors = validate_manifest_revision(root, manifest, require_current=require_current_revision)
    if revision_errors:
        raise ValueError("manifest revision validation failed: " + "; ".join(revision_errors))
    for section, values in (
        ("inputs", inputs),
        ("supporting_inputs", supporting_inputs),
        ("outputs", outputs),
    ):
        bucket = manifest.setdefault(section, {})
        if not isinstance(bucket, dict):
            raise ValueError(f"manifest section is not an object: {section}")
        for name, item in (values or {}).items():
            bucket[name] = entry(root, item)
    if registries:
        for name, value in registries.items():
            manifest[name] = value
    if status is not None:
        manifest["status"] = status
    if barriers:
        existing = manifest.setdefault("barriers", {})
        if not isinstance(existing, dict):
            raise ValueError("manifest barriers is not an object")
        existing.update(barriers)
    atomic_write(path, manifest)
    return manifest


def resolve_recorded_path(root: Path, manifest: Mapping[str, object], section: str, key: str) -> Path:
    bucket = manifest.get(section, {})
    if not isinstance(bucket, dict) or key not in bucket or not isinstance(bucket[key], dict):
        raise KeyError(f"manifest entry missing: {section}.{key}")
    raw = str(bucket[key].get("path") or "")
    resolved = Path(raw)
    return resolved if resolved.is_absolute() else (root / resolved).resolve()
