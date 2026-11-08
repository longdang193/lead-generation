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
