"""Thin JSON tool boundary for Codex-native lead-generation handoffs."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from action_lifecycle import admit_action as admit_lifecycle_action, replay_lifecycle, settle_action, validate_result as validate_lifecycle_result
from action_receipts import replay_run
from account_intelligence import calculate_structural_fit, project_account_intelligence, validate_account_thesis
from import_discovery import read_rows
from lead_contract import is_plausible_company_name
from normalize_dedupe import clean_name, company_id, explicit_berlin_evidence, trusted_company_domain
from promote_evidence import promote_verified_claims
from run_manifest import file_sha256, finalization_eligibility, finalize_run, load, reconstruct_finalization_readiness
from select_for_enrichment import select_accounts
from score_leads import rank_account
from typed_contracts import (
    ActionReceipt,
    ArtifactRef,
    EvidenceClaim,
    FinalizationRequest,
    Goal,
    NativeActionRequest,
    WorkerResult,
)


def discover_profiles(root: Path) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for path in sorted((root / "agents").glob("*.toml")):
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        name = str(data.get("name") or path.stem)
        skills = data.get("skills") or []
        if not isinstance(skills, list) or not all(isinstance(skill, str) and skill for skill in skills):
            raise ValueError(f"profile skills must be a list of non-empty strings: {path}")
        profiles.append({
            "name": name,
            "path": path.relative_to(root).as_posix(),
            "task_function": str(data.get("task_function") or ""),
            "skills": list(skills),
        })
    return profiles


def _payload(request: dict[str, Any]) -> dict[str, Any]:
    value = request.get("payload", {})
    if not isinstance(value, dict):
        raise ValueError("payload must be an object")
    return value


def _resolve_path(root: Path, raw: object, *, required: bool = True) -> Path:
    value = str(raw or "")
    if not value:
        if required:
            raise ValueError("path is required")
        return root.resolve()
    path = Path(value)
    resolved = (path if path.is_absolute() else root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path must remain under repository root") from exc
    return resolved


def _artifact(root: Path, path: Path, kind: str) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    return ArtifactRef(path=path.relative_to(root.resolve()).as_posix(), sha256=file_sha256(path), kind=kind).model_dump(mode="json")


def _script(root: Path, name: str) -> Path:
    candidate = root / "scripts" / name
    return candidate if candidate.exists() else Path(__file__).resolve().with_name(name)


def _records(path: Path) -> list[dict[str, object]]:
    if path.suffix.lower() == ".csv":
        import csv
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix.lower() == ".jsonl":
        return [value for value in (json.loads(line) for line in lines if line.strip()) if isinstance(value, dict)]
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _normalize_company(row: dict[str, object]) -> dict[str, object]:
    company_name = str(row.get("company_name") or row.get("legal_name") or "").strip()
    normalized_name = clean_name(company_name)
    trusted_domain = trusted_company_domain({key: str(value or "") for key, value in row.items()})
    postal_code = str(row.get("postal_code") or "").strip()
    normalized = dict(row)
    normalized.update({
        "company_name": company_name,
        "normalized_name": normalized_name,
        "trusted_domain": trusted_domain,
        "company_id": str(row.get("company_id") or company_id(normalized_name, trusted_domain, postal_code)),
        "berlin_evidence": str(row.get("berlin_evidence") or explicit_berlin_evidence({key: str(value or "") for key, value in row.items()})),
    })
    return normalized


def invoke(request: dict[str, Any], root: Path) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    action = str(request.get("action") or "")
    payload = dict(_payload(request))
    if action == "discover_profiles":
        return {"profiles": discover_profiles(root)}
    if action == "discover_companies":
        source = str(payload.get("source") or "approved_input")
        rows = read_rows(_resolve_path(root, payload.get("path")), source)
        limit = int(payload.get("limit", 1000))
        if limit < 0:
            raise ValueError("limit must be nonnegative")
        return {"companies": rows[:limit], "count": len(rows), "truncated": len(rows) > limit, "source": source}
    if action == "normalize_company":
        row = payload.get("company") or payload.get("row")
        if not isinstance(row, dict):
            raise ValueError("company must be an object")
        return {"company": _normalize_company(row)}
    if action in {"deduplicate", "deduplicate_companies"}:
        rows = payload.get("companies")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("companies must be a list of objects")
        unique: list[dict[str, object]] = []
        seen: set[tuple[object, ...]] = set()
        for raw in rows:
            row = _normalize_company(raw)
            key = (row.get("company_id"), row.get("trusted_domain"), row.get("normalized_name"), str(row.get("postal_code") or ""))
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
        return {"companies": unique, "input_count": len(rows), "output_count": len(unique), "duplicates_removed": len(rows) - len(unique)}
    if action == "validate_identity":
        row = payload.get("company") or payload.get("row")
        if not isinstance(row, dict):
            raise ValueError("company must be an object")
        normalized = _normalize_company(row)
        errors: list[str] = []
        if not is_plausible_company_name(normalized.get("company_name")):
            errors.append("company_name is not plausible")
        if not normalized.get("trusted_domain"):
            errors.append("trusted_company_domain is missing or blocked")
        return {"valid": not errors, "errors": errors, "company": normalized}
    if action == "validate_goal":
        return {"goal": Goal.model_validate(payload).model_dump(mode="json")}
    if action == "admit_action":
        manifest_raw = str(payload.pop("manifest_path", "manifest.json"))
        manifest_path = Path(manifest_raw)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        manifest_path = manifest_path.resolve()
        if root.resolve() not in manifest_path.parents:
            raise ValueError("manifest_path must remain under repository root")
        value = admit_lifecycle_action(root, payload, manifest_path)
        return {"action": value.model_dump(mode="json"), "admitted": True}
    if action == "validate_result":
        value = validate_lifecycle_result(root, payload)
        return {"result": value.model_dump(mode="json"), "validated": not bool(value.validation_errors)}
    if action == "validate_evidence":
        value = EvidenceClaim.model_validate(payload)
        return {"claim": value.model_dump(mode="json"), "validated": True}
    if action == "capture_evidence":
        value = EvidenceClaim.model_validate(payload)
        return {"claim": value.model_dump(mode="json"), "validated": True}
    if action in {"promote_evidence", "promote_verified_claims"}:
        candidates = _resolve_path(root, payload.get("candidates_path"))
        decisions = _resolve_path(root, payload.get("decisions_path"))
        output = _resolve_path(root, payload.get("output_path"))
        manifest = _resolve_path(root, payload.get("manifest_path"), required=False) if payload.get("manifest_path") else None
        promoted = promote_verified_claims(candidates, decisions, output, manifest)
        return {"artifact": _artifact(root, output, "verified_evidence"), "count": len(promoted)}
    if action == "validate_thesis":
        claims = payload.pop("claims", [])
        offer_profile = payload.pop("offer_profile", None)
        semantic_reviews = payload.pop("semantic_reviews", [])
        value = validate_account_thesis(payload, claims, semantic_reviews=semantic_reviews, offer_profile=offer_profile)
        return {"thesis": value.model_dump(mode="json"), "validated": True}
    if action == "project_account_intelligence":
        claims = payload.pop("claims", [])
        thesis = payload.pop("thesis", None)
        offer_profile = payload.pop("offer_profile", None)
        semantic_reviews = payload.pop("semantic_reviews", [])
        if not isinstance(thesis, dict):
            raise ValueError("thesis must be an object")
        return project_account_intelligence(claims, thesis, semantic_reviews=semantic_reviews, offer_profile=offer_profile)
    if action == "persist_dossier":
        claims = payload.pop("claims", [])
        thesis = payload.pop("thesis", None)
        offer_profile = payload.pop("offer_profile", None)
        semantic_reviews = payload.pop("semantic_reviews", [])
        output = _resolve_path(root, payload.pop("output"))
        if not isinstance(thesis, dict):
            raise ValueError("thesis must be an object")
        dossier = project_account_intelligence(claims, thesis, semantic_reviews=semantic_reviews, offer_profile=offer_profile)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(dossier, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")) + "\n", encoding="utf-8")
        return {"dossier": dossier, "artifact": _artifact(root, output, "account_dossier")}
    if action == "calculate_fit":
        claims = payload.get("claims", [])
        return {"structural_fit": calculate_structural_fit(claims)}
    if action == "rank_leads":
        scores = payload.get("scores")
        qualification = payload.get("qualification")
        if isinstance(scores, str):
            score_path = _resolve_path(root, scores)
            scores = _records(score_path)
        if isinstance(qualification, str):
            qualification_path = _resolve_path(root, qualification)
            qualification = {str(item.get("company_id") or ""): item for item in _records(qualification_path)}
        if not isinstance(scores, list) or not isinstance(qualification, dict):
            raise ValueError("scores and qualification are required")
        offer_id = str(payload.get("offer_id") or "")
        offer_version = str(payload.get("offer_version") or "")
        production = bool(payload.get("production", False))
        compatibility_mode = bool(payload.get("compatibility_mode", False))
        dossiers = payload.get("dossiers")
        if production and (not offer_id or not offer_version or not isinstance(dossiers, (dict, list))):
            raise ValueError("production ranking requires offer context and one validated dossier per company")
        if not production and not compatibility_mode and not isinstance(dossiers, (dict, list)):
            raise ValueError("flat structural ranking is compatibility-only; pass compatibility_mode=true or dossiers")
        semantic_reviews = payload.get("semantic_reviews")
        if offer_id and offer_version and (isinstance(dossiers, (dict, list)) or compatibility_mode):
            if isinstance(dossiers, dict):
                dossiers_by_company = {str(key): value for key, value in dossiers.items() if isinstance(value, dict)}
            elif isinstance(dossiers, list):
                dossiers_by_company = {str(value.get("company_id") or (value.get("thesis") or {}).get("company_id")): value for value in dossiers if isinstance(value, dict)}
            else:
                dossiers_by_company = {}
            from typed_contracts import OfferProfile
            if not isinstance(semantic_reviews, list):
                semantic_reviews = []
            commercial_scores = []
            for score in scores:
                company_id = str(score.get("company_id") or "")
                enriched = dict(score)
                dossier = dossiers_by_company.get(company_id)
                if dossier is None and compatibility_mode:
                    reviews_by_company: dict[str, list[dict[str, object]]] = {}
                    for review in semantic_reviews:
                        if isinstance(review, dict):
                            reviews_by_company.setdefault(str(review.get("company_id") or ""), []).append(review)
                    enriched["semantic_reviews"] = reviews_by_company.get(company_id, [])
                    audit = rank_account(enriched, offer_id, offer_version)
                    enriched["rank_audit"] = audit.model_dump(mode="json")
                    enriched["_commercial_score"] = audit.total_score
                    commercial_scores.append(enriched)
                    continue
                if not isinstance(dossier, dict):
                    raise ValueError(f"missing validated dossier for company: {company_id}")
                claims = dossier.get("claims") or []
                reviews = dossier.get("semantic_reviews") or []
                if not isinstance(dossier.get("thesis"), dict):
                    raise ValueError(f"dossier thesis is missing for company: {company_id}")
                validate_account_thesis(dossier["thesis"], claims, semantic_reviews=reviews, offer_profile=payload.get("offer_profile"))
                audit = rank_account(enriched, offer_id, offer_version, dossier=dossier)
                enriched["rank_audit"] = audit.model_dump(mode="json")
                enriched["_commercial_score"] = audit.total_score
                commercial_scores.append(enriched)
            scores = commercial_scores
        elif offer_id and offer_version and not compatibility_mode:
            raise ValueError("commercial ranking requires validated dossiers; compatibility_mode is explicit and non-production")
        accepted = payload.get("accepted_company_ids")
        accepted_ids = set(str(item) for item in accepted) if isinstance(accepted, list) else None
        ranked = select_accounts(scores, qualification, int(payload.get("max_accounts", len(scores))), accepted_ids, str(payload.get("delivery_policy") or "strict"))
        return {"leads": ranked, "count": len(ranked)}
    if action == "export_workbook":
        output = _resolve_path(root, payload.get("output"))
        build_report = _resolve_path(root, payload.get("build_report"))
        command = [
            sys.executable, str(_script(root, "build_workbook.py")),
            "--companies", str(_resolve_path(root, payload.get("companies"))),
            "--scores", str(_resolve_path(root, payload.get("scores"))),
            "--priority", str(_resolve_path(root, payload.get("priority"))),
            "--contacts", str(_resolve_path(root, payload.get("contacts"))),
            "--sources", str(_resolve_path(root, payload.get("sources"))),
            "--output", str(output), "--build-report", str(build_report),
        ]
        if payload.get("production_account_intelligence"):
            dossier = payload.get("dossier")
            if not dossier:
                raise ValueError("production workbook export requires dossier artifact")
            command.extend(["--dossier", str(_resolve_path(root, dossier)), "--production-account-intelligence"])
        if payload.get("run_manifest"):
            command.extend(["--run-manifest", str(_resolve_path(root, payload.get("run_manifest")))])
        completed = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError((completed.stdout + completed.stderr).strip() or "workbook export failed")
        return {"workbook": _artifact(root, output, "workbook"), "build_report": _artifact(root, build_report, "build_report")}
    if action == "qa_workbook":
        workbook = _resolve_path(root, payload.get("workbook"))
        report = _resolve_path(root, payload.get("report"))
        sample_output = _resolve_path(root, payload.get("sample_output"))
        command = [
            sys.executable, str(_script(root, "qa_leads.py")),
            "--workbook", str(workbook), "--schema", str(_resolve_path(root, payload.get("schema"))),
            "--evidence-dir", str(_resolve_path(root, payload.get("evidence_dir"))),
            "--report", str(report), "--sample-output", str(sample_output),
        ]
        if payload.get("website_evidence"):
            command.extend(["--website-evidence", str(_resolve_path(root, payload.get("website_evidence")))])
        if payload.get("run_manifest"):
            command.extend(["--run-manifest", str(_resolve_path(root, payload.get("run_manifest")))])
        completed = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError((completed.stdout + completed.stderr).strip() or "workbook QA failed")
        return {"report": _artifact(root, report, "qa_report"), "sample_output": _artifact(root, sample_output, "qa_sample")}
    if action == "record_receipt":
        value = settle_action(root, payload)
        return {"receipt": value.model_dump(mode="json"), "journal": str((root / "evidence" / "action_receipts" / f"{value.run_id}.jsonl").relative_to(root))}
    if action == "replay_lifecycle":
        run_id = str(payload.get("run_id") or "")
        if not run_id:
            raise ValueError("run_id is required")
        return replay_lifecycle(root, run_id)
    if action == "replay_receipts":
        run_id = str(payload.get("run_id") or "")
        if not run_id:
            raise ValueError("run_id is required")
        return replay_run(root, run_id)
    if action == "check_finalization":
        value = FinalizationRequest.model_validate(payload)
        manifest_path = Path(value.manifest_path)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        manifest_path = manifest_path.resolve()
        if root.resolve() not in manifest_path.parents:
            raise ValueError("manifest_path must remain under repository root")
        proof = reconstruct_finalization_readiness(root, manifest_path, value.delivery_policy.value)
        return {"eligible": bool(proof["ready"]), "errors": proof["errors"], "manifest_path": manifest_path.relative_to(root.resolve()).as_posix(), "proof": proof}
    if action == "finalize_run":
        run_id = str(payload.get("run_id") or "")
        staging = root / str(payload.get("staging_path") or "")
        final = root / str(payload.get("final_path") or "")
        manifest_path = root / str(payload.get("manifest_path") or "")
        if not all((run_id, str(payload.get("status") or ""), str(payload.get("staging_path") or ""), str(payload.get("final_path") or ""), str(payload.get("manifest_path") or ""))):
            raise ValueError("run_id, status, staging_path, final_path, and manifest_path are required")
        if load(manifest_path).get("run_id") != run_id:
            raise ValueError("run_id does not match manifest")
        published = finalize_run(root, manifest_path, staging, final, status=str(payload["status"]), delivery_policy=payload.get("delivery_policy"))
        return {"published": True, "path": published.relative_to(root.resolve()).as_posix()}
    if action == "publish_staged_output":
        raise ValueError("direct publish_staged_output is not available through the native facade; use finalize_run")
    raise ValueError(f"unknown harness action: {action}")


def main() -> int:
    try:
        request = json.load(sys.stdin)
        result = invoke(request, Path.cwd().resolve())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
