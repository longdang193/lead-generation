"""Thin JSON tool boundary for Codex-native lead-generation handoffs."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from action_receipts import append_receipt, replay_run
from account_intelligence import calculate_structural_fit, project_account_intelligence, validate_account_thesis
from run_manifest import finalization_eligibility, load, publish_staged_output
from typed_contracts import (
    ActionReceipt,
    FinalizationRequest,
    Goal,
    NativeActionRequest,
    WorkerResult,
)


def discover_profiles(root: Path) -> list[dict[str, str]]:
    profiles: list[dict[str, str]] = []
    for path in sorted((root / "agents").glob("*.toml")):
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        name = str(data.get("name") or path.stem)
        profiles.append({"name": name, "path": path.relative_to(root).as_posix()})
    return profiles


def _payload(request: dict[str, Any]) -> dict[str, Any]:
    value = request.get("payload", {})
    if not isinstance(value, dict):
        raise ValueError("payload must be an object")
    return value


def invoke(request: dict[str, Any], root: Path) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    action = str(request.get("action") or "")
    payload = _payload(request)
    if action == "discover_profiles":
        return {"profiles": discover_profiles(root)}
    if action == "validate_goal":
        return {"goal": Goal.model_validate(payload).model_dump(mode="json")}
    if action == "admit_action":
        value = NativeActionRequest.model_validate(payload)
        return {"action": value.model_dump(mode="json"), "admitted": True}
    if action == "validate_result":
        value = WorkerResult.model_validate(payload)
        return {"result": value.model_dump(mode="json"), "validated": not bool(value.validation_errors)}
    if action == "validate_evidence":
        from typed_contracts import EvidenceClaim

        value = EvidenceClaim.model_validate(payload)
        return {"claim": value.model_dump(mode="json"), "validated": True}
    if action == "validate_thesis":
        claims = payload.pop("claims", [])
        value = validate_account_thesis(payload, claims)
        return {"thesis": value.model_dump(mode="json"), "validated": True}
    if action == "project_account_intelligence":
        claims = payload.pop("claims", [])
        thesis = payload.pop("thesis", None)
        if not isinstance(thesis, dict):
            raise ValueError("thesis must be an object")
        return project_account_intelligence(claims, thesis)
    if action == "calculate_fit":
        claims = payload.get("claims", [])
        return {"structural_fit": calculate_structural_fit(claims)}
    if action == "record_receipt":
        value = append_receipt(root, ActionReceipt.model_validate(payload))
        return {"receipt": value.model_dump(mode="json"), "journal": str((root / "evidence" / "action_receipts" / f"{value.run_id}.jsonl").relative_to(root))}
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
        allowed, errors = finalization_eligibility(load(manifest_path), value.delivery_policy.value)
        return {"eligible": allowed, "errors": errors, "manifest_path": manifest_path.relative_to(root.resolve()).as_posix()}
    if action == "publish_staged_output":
        run_id = str(payload.get("run_id") or "")
        staging_raw = str(payload.get("staging_path") or "")
        final_raw = str(payload.get("final_path") or "")
        manifest_raw = str(payload.get("manifest_path") or "")
        status = str(payload.get("status") or "")
        if not all((run_id, status, staging_raw, final_raw, manifest_raw)):
            raise ValueError("run_id, status, staging_path, final_path, and manifest_path are required")
        staging = root / staging_raw
        final = root / final_raw
        manifest_path = root / manifest_raw
        manifest = load(manifest_path)
        if str(manifest.get("run_id") or "") != run_id:
            raise ValueError("run_id does not match manifest")
        published = publish_staged_output(root, manifest_path, staging, final, status=status)
        return {"published": True, "path": published.relative_to(root.resolve()).as_posix()}
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

