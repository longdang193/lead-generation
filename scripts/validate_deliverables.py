from __future__ import annotations

import argparse
import json
import hashlib
import re
import subprocess
from pathlib import Path

from openpyxl import load_workbook
from pptx import Presentation


def resolve_manifest_path(manifest_path: Path, value: object) -> Path:
    raw = str(value or "").replace("\\", "/")
    path = Path(raw)
    if path.is_absolute():
        return path
    return (manifest_path.parent.parent / path).resolve()


def verify_manifest_bucket(errors: list[str], manifest_path: Path, bucket_name: str, bucket: dict[str, object]) -> None:
    for key, item in bucket.items():
        if not isinstance(item, dict):
            errors.append(f"manifest entry is invalid: {bucket_name}.{key}")
            continue
        path = resolve_manifest_path(manifest_path, item.get("path"))
        if not path.exists():
            errors.append(f"manifest path missing: {bucket_name}.{key}: {path}")
            continue
        expected = item.get("sha256")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected != actual:
            errors.append(f"manifest hash mismatch: {bucket_name}.{key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--qa-report", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, default=Path("evidence/run_manifest_2026-11-09.json"))
    args = parser.parse_args()
    errors = []
    qualification = priority = contacts = []
    if not args.workbook.exists():
        errors.append("workbook missing")
    else:
        workbook = load_workbook(args.workbook, read_only=True)
        required = ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources"]
        if workbook.sheetnames != required:
            errors.append("workbook tabs mismatch")
        else:
            def rows(sheet):
                values = list(workbook[sheet].values)
                return [dict(zip(values[0], row)) for row in values[1:] if any(value not in (None, "") for value in row)]
            qualification = rows("02_Qualification")
            priority = rows("03_Priority_Leads")
            contacts = rows("04_Contacts")
    if not args.deck.exists():
        errors.append("deck missing")
    elif len(Presentation(args.deck).slides) != 5:
        errors.append("deck must contain exactly five slides")
    elif qualification:
        deck_text = "\n".join(shape.text for slide in Presentation(args.deck).slides for shape in slide.shapes if hasattr(shape, "text"))
        tier_counts = {}
        for row in qualification:
            tier_counts[row.get("lead_tier")] = tier_counts.get(row.get("lead_tier"), 0) + 1
        email_count = sum(row.get("contact_email") not in (None, "", "Unknown") for row in contacts)
        named_count = sum(row.get("contact_name") not in (None, "", "Unknown") for row in contacts)
        expected_fragments = [
            f"Qualified Accounts ({len(qualification)} accepted)",
            f"Priority Leads ({len(priority)})",
            f"Email-evidence contacts ({email_count} Published; {named_count} named decision-makers)",
            f"A {tier_counts.get('A', 0)}",
            f"Research {tier_counts.get('Research', 0)}",
        ]
        for fragment in expected_fragments:
            if fragment not in deck_text:
                errors.append(f"deck metric is stale: {fragment}")
    if not args.qa_report.exists() or "Errors: 0" not in args.qa_report.read_text(encoding="utf-8"):
        errors.append("QA report missing or reports errors")
    if not args.run_manifest.exists():
        errors.append("run manifest missing")
    else:
        try:
            manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
            revision = str(manifest.get("git_revision") or "")
            if not re.fullmatch(r"[0-9a-f]{40}", revision):
                errors.append("run manifest missing full Git revision")
            else:
                try:
                    subprocess.run(["git", "cat-file", "-e", f"{revision}^{{commit}}"], check=True, capture_output=True)
                except (OSError, subprocess.CalledProcessError):
                    errors.append("run manifest Git revision is not reachable")
            output_manifest = manifest.get("outputs", {})
            expected = output_manifest.get("workbook", {}).get("sha256")
            digest = hashlib.sha256(args.workbook.read_bytes()).hexdigest() if args.workbook.exists() else ""
            if expected != digest:
                errors.append("workbook does not match run manifest")
            verify_manifest_bucket(errors, args.run_manifest, "outputs", output_manifest)
            for key in ("build_report", "qa_report", "qa_sample", "deck"):
                if key not in output_manifest:
                    errors.append(f"run manifest missing {key} output")
            for key in ("companies", "scores", "priority", "contacts", "sources"):
                if key not in manifest.get("inputs", {}):
                    errors.append(f"run manifest missing {key} input")
            for key in ("schema", "website_evidence", "source_register", "entity_resolution", "buying_signal_audit", "buying_events", "scoring_audit", "contact_sources"):
                if key not in manifest.get("supporting_inputs", {}):
                    errors.append(f"run manifest missing {key} supporting input")
            verify_manifest_bucket(errors, args.run_manifest, "inputs", manifest.get("inputs", {}))
            verify_manifest_bucket(errors, args.run_manifest, "supporting_inputs", manifest.get("supporting_inputs", {}))
        except (OSError, ValueError):
            errors.append("run manifest unreadable")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("deliverables valid: workbook, five-slide deck, and QA report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
