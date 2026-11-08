from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from run_manifest import portable_path, update as update_manifest


def load_records(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return []
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        return value if isinstance(value, list) else [value]
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, object]], fallback: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else fallback
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _claim_value(claim: dict[str, object]) -> object:
    value = claim.get("claim_value")
    if isinstance(value, dict):
        return value.get("value", value.get("name", value))
    return value


def project_verified_evidence(
    promoted_path: Path,
    base_qualification_path: Path,
    base_scores_path: Path,
    base_contacts_path: Path,
    output_dir: Path,
    *,
    run_id: str,
    manifest_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Path]:
    claims = sorted(load_records(promoted_path), key=lambda row: str(row.get("candidate_claim_id") or ""))
    by_company: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for claim in claims:
        if claim.get("candidate_status") != "Verified":
            raise ValueError("canonical projection accepts only Verified claims")
        if str(claim.get("verifier_run_id") or "").startswith(run_id) is False:
            raise ValueError(f"claim is outside active run: {claim.get('candidate_claim_id')}")
        key = (str(claim.get("company_id") or ""), str(claim.get("claim_type") or ""))
        if not key[0] or not key[1]:
            raise ValueError("verified claim lacks company_id or claim_type")
        if key in seen:
            raise ValueError(f"duplicate canonical claim: {key[0]}:{key[1]}")
        seen.add(key)
        by_company[key[0]].append(claim)

    qualification = load_records(base_qualification_path)
    qualification = sorted(qualification, key=lambda row: str(row.get("company_id") or ""))
    for row in qualification:
        company_id = str(row.get("company_id") or "")
        row_claims = by_company.get(company_id, [])
        urls = [str(row.get("evidence_urls") or "")] if row.get("evidence_urls") else []
        for claim in row_claims:
            claim_type = str(claim["claim_type"])
            value = _claim_value(claim)
            if claim_type in {"service_fit", "residential_weg", "berlin_relevance", "management_type"}:
                row[claim_type] = value
            elif claim_type == "portfolio_size":
                row["portfolio_size"] = value
            if claim.get("source_url"):
                urls.append(str(claim["source_url"]))
        if urls:
            row["evidence_urls"] = " | ".join(sorted(set(url for url in urls if url)))
        row["projection_run_id"] = run_id

    scores = sorted(load_records(base_scores_path), key=lambda row: str(row.get("company_id") or ""))
    events: list[dict[str, object]] = []
    signal_audit: list[dict[str, object]] = []
    for row in scores:
        company_id = str(row.get("company_id") or "")
        row_claims = by_company.get(company_id, [])
        signal_claims = [claim for claim in row_claims if claim.get("claim_type") in {"buying_signal", "event"}]
        for claim in signal_claims:
            value = _claim_value(claim)
            if claim.get("claim_type") == "buying_signal":
                row["buying_signal"] = value
            event = value if isinstance(value, dict) else {}
            events.append({
                "event_id": event.get("event_id", claim.get("candidate_claim_id")),
                "company_id": company_id,
                "match_method": "verified_evidence",
                "match_confidence": "Verified",
                "source_url": claim.get("source_url", ""),
            })
        if signal_claims:
            row["buying_signal_evidence_urls"] = " | ".join(sorted({str(claim.get("source_url")) for claim in signal_claims if claim.get("source_url")}))
        signal_audit.append({"company_id": company_id, "status": "Completed", "verified_claim_count": len(signal_claims), "run_id": run_id})
        row["projection_run_id"] = run_id

    contacts = sorted(load_records(base_contacts_path), key=lambda row: str(row.get("company_id") or ""))
    for row in contacts:
        company_id = str(row.get("company_id") or "")
        contact_claims = [claim for claim in by_company.get(company_id, []) if claim.get("claim_type") == "contact"]
        if contact_claims:
            claim = contact_claims[0]
            row["contact_name"] = claim.get("person_name") or row.get("contact_name", "Unknown")
            row["contact_role"] = claim.get("role") or row.get("contact_role", "Unknown")
            row["contact_email"] = claim.get("email") or row.get("contact_email", "Unknown")
            row["email_source"] = claim.get("source_url") or row.get("email_source", "Unknown")
            row["verification_status"] = "Verified"
        row["projection_run_id"] = run_id

    outputs = {
        "qualification": output_dir / "qualification.jsonl",
        "scores": output_dir / "scores.csv",
        "contacts": output_dir / "contacts.csv",
        "events": output_dir / "events.csv",
        "signal_audit": output_dir / "signal_audit.csv",
    }
    _write_jsonl(outputs["qualification"], qualification)
    _write_csv(outputs["scores"], scores, ["company_id", "buying_signal"])
    _write_csv(outputs["contacts"], contacts, ["company_id", "contact_name", "contact_email"])
    _write_csv(outputs["events"], sorted(events, key=lambda row: (str(row["company_id"]), str(row["event_id"]))), ["event_id", "company_id", "match_method", "match_confidence", "source_url"])
    _write_csv(outputs["signal_audit"], signal_audit, ["company_id", "status", "verified_claim_count", "run_id"])
    if manifest_path and root:
        update_manifest(manifest_path, root, outputs=outputs, registries={"projection": {"outputs": {name: {"path": portable_path(root, path), "format": path.suffix} for name, path in outputs.items()}, "run_id": run_id}}, barriers={"projection": True})
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promoted", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()
    outputs = project_verified_evidence(args.promoted, args.qualification, args.scores, args.contacts, args.output_dir, run_id=args.run_id, manifest_path=args.run_manifest, root=Path.cwd())
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
