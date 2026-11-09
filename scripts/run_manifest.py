from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping


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


def _complete_publication(root: Path, manifest_path: Path, marker_path: Path, marker: Mapping[str, object]) -> None:
    manifest = load(manifest_path)
    run_id = str(manifest.get("run_id") or "")
    if str(marker.get("run_id") or "") != run_id:
        raise ValueError("publication recovery marker run_id mismatch")
    marker_head_sha = str(marker.get("head_sha") or "")
    if marker_head_sha and marker_head_sha != str(manifest.get("head_sha") or ""):
        raise ValueError("publication recovery marker head_sha mismatch")
    revision_errors = validate_manifest_revision(root, manifest)
    if revision_errors:
        raise ValueError("publication recovery revision validation failed: " + "; ".join(revision_errors))
    staging, final = _marker_paths(root, marker)
    expected = str(marker.get("staging_sha256") or "")
    if not expected or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("publication recovery marker has an invalid staging hash")
    if staging.exists():
        if file_sha256(staging) != expected:
            raise ValueError("publication recovery found a mismatched staging output")
        os.replace(staging, final)
    elif not final.exists():
        raise ValueError("publication recovery found neither a valid staging nor final output")
    elif file_sha256(final) != expected:
        raise ValueError("publication recovery found a mismatched final output")
    update(path=manifest_path, root=root, outputs={"workbook": final}, status=str(manifest.get("status") or "ready_for_validation"), barriers={"published": True})
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
    marker_path = publication_marker_path(root, run_id)
    atomic_write(marker_path, {
        "run_id": run_id,
        "head_sha": str(manifest.get("head_sha") or ""),
        "staging_path": staging.relative_to(root_resolved).as_posix(),
        "final_path": final.relative_to(root_resolved).as_posix(),
        "staging_sha256": file_sha256(staging),
    })
    _complete_publication(root, manifest_path, marker_path, load(marker_path))
    if registries or barriers:
        update(
            manifest_path,
            root,
            registries=registries,
            status=status,
            barriers={"published": True, **(barriers or {})},
        )
    return final


def finalization_eligibility(manifest: Mapping[str, object], delivery_policy: str) -> tuple[bool, list[str]]:
    """Check finalization policy without inferring facts from agent claims."""

    if delivery_policy not in {"strict", "personal"}:
        return False, [f"unknown delivery policy: {delivery_policy}"]
    errors: list[str] = []
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
    if isinstance(delivery, dict):
        status = str(delivery.get("status") or "")
        if delivery_policy == "strict" and status not in {"complete", "completed"}:
            errors.append("strict finalization requires complete delivery")
        if status == "none_found":
            errors.append("None found is not a finalization substitute")
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
) -> dict[str, object]:
    manifest = load(path)
    if not manifest.get("run_id") or not manifest.get("head_sha"):
        raise ValueError("manifest identity is incomplete")
    manifest.setdefault("git_revision", manifest["head_sha"])
    revision_errors = validate_manifest_revision(root, manifest)
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
