from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def implementation_status(root: Path) -> str:
    lines = git_output(root, "status", "--porcelain").splitlines()
    preserved = {"lead-generation-architecture.json"}
    return "\n".join(line for line in lines if line[3:] not in preserved)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_entry(root: Path, path: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        portable = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        portable = str(resolved)
    return {"path": portable, "sha256": file_digest(resolved)}


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
        "inputs": {path.stem: manifest_entry(root, path) for path in inputs},
        "supporting_inputs": {path.stem: manifest_entry(root, path) for path in supporting_inputs},
        "queues": {},
        "barriers": {"accepted_identity": True, "provisional_shortlist": False, "verified_evidence": False},
        "outputs": {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def write_lane_queue(shortlist_path: Path, output_path: Path, lane: str, run_id: str) -> list[dict[str, object]]:
    with shortlist_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    queue = []
    for row in sorted(rows, key=lambda item: str(item.get("company_id") or "")):
        company_id = str(row.get("company_id") or "")
        if not company_id:
            raise ValueError("shortlist row lacks company_id")
        queue.append({
            "run_id": run_id,
            "lane": lane,
            "company_id": company_id,
            "company_name": row.get("company_name", ""),
            "trusted_domain": row.get("verified_company_domain") or row.get("domain", ""),
            "location": row.get("city") or "Berlin",
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
        seen.add(company_id)


def verify_manifest(manifest_path: Path, root: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    head_sha = git_output(root, "rev-parse", "HEAD")
    if manifest.get("head_sha") != head_sha:
        errors.append("HEAD does not match manifest head_sha")
    if implementation_status(root):
        errors.append("implementation worktree is dirty")
    for bucket_name in ("inputs", "supporting_inputs", "outputs"):
        for name, item in manifest.get(bucket_name, {}).items():
            path = (root / str(item.get("path"))).resolve()
            if not path.exists():
                errors.append(f"missing {bucket_name}.{name}")
            elif item.get("sha256") != file_digest(path):
                errors.append(f"hash mismatch {bucket_name}.{name}")
    return errors


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
    args = parser.parse_args()
    if args.command == "create":
        print(json.dumps(create_run_manifest(args.root, args.manifest, args.run_id, args.input, args.supporting_input), indent=2))
        return 0
    errors = verify_manifest(args.manifest, args.root)
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
