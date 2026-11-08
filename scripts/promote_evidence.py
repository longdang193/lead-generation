from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

import jsonschema

from lead_contract import candidate_sha256, claim_requirements_met, run_scope_matches, verifier_decision_valid, update_run_manifest


SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config" / "research_evidence_schema.json").read_text(encoding="utf-8"))
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


def load_records(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        return payload if isinstance(payload, list) else [payload]
    records = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"record at {path}:{line_number} is not an object")
        records.append(value)
    return records


def validate_verifier_decision(decision: dict[str, object], claims: dict[str, dict[str, object]]) -> tuple[bool, list[str]]:
    claim_id = str(decision.get("candidate_claim_id") or "")
    claim = claims.get(claim_id)
    if claim is None:
        return False, ["unknown_candidate_claim_id"]
    return verifier_decision_valid(decision, claim)


def _manifest_context(manifest: dict[str, object]) -> tuple[str, set[str], dict[str, dict[str, object]], dict[str, object]]:
    run_id = str(manifest.get("run_id") or "")
    if not run_id:
        raise ValueError("run manifest has no run_id")
    accepted = {str(value) for value in manifest.get("accepted_company_ids", [])}
    if not accepted:
        raise ValueError("run manifest has no accepted company scope")
    research: dict[str, dict[str, object]] = {}
    for lane_records in (manifest.get("research_runs") or {}).values():
        records = lane_records if isinstance(lane_records, list) else [lane_records]
        for record in records:
            if isinstance(record, dict) and record.get("research_run_id"):
                research[str(record["research_run_id"])] = record
    verifier = manifest.get("verifier_runs") or {}
    if isinstance(verifier, list):
        verifier = {str(item.get("verifier_run_id")): item for item in verifier if isinstance(item, dict)}
    if not isinstance(verifier, dict):
        verifier = {}
    return run_id, accepted, research, verifier


def _source_allowed(source_url: object, policy: dict[str, object]) -> bool:
    allowed = {str(item).lower().removeprefix("www.") for item in policy.get("allowed_domains", []) if str(item).strip()}
    if not allowed:
        return False
    hostname = (urlparse(str(source_url or "")).hostname or "").lower().removeprefix("www.")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed)


def promote_verified_claims(candidates_path: Path, decisions_path: Path, output_path: Path, run_manifest: Path | None = None) -> list[dict[str, object]]:
    active_run_id = None
    accepted_company_ids: set[str] = set()
    research_registry: dict[str, dict[str, object]] = {}
    verifier_registry: dict[str, object] = {}
    source_policy: dict[str, object] = {}
    if run_manifest:
        manifest = json.loads(run_manifest.read_text(encoding="utf-8"))
        active_run_id, accepted_company_ids, research_registry, verifier_registry = _manifest_context(manifest)
        source_policy = manifest.get("source_policy") if isinstance(manifest.get("source_policy"), dict) else {}
    candidates = load_records(candidates_path)
    claims: dict[str, dict[str, object]] = {}
    for claim in candidates:
        claim_id = str(claim.get("candidate_claim_id") or "")
        if not claim_id or claim_id in claims:
            raise ValueError("candidate claims must have unique candidate_claim_id values")
        errors = sorted(error.message for error in VALIDATOR.iter_errors(claim))
        if errors:
            raise ValueError(f"candidate claim schema invalid: {claim_id}: {'; '.join(errors)}")
        if claim.get("candidate_sha256") != candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"}):
            raise ValueError(f"candidate hash mismatch: {claim_id}")
        if active_run_id and not run_scope_matches(claim.get("research_run_id"), active_run_id):
            raise ValueError(f"candidate claim is outside active run: {claim_id}")
        if active_run_id and str(claim.get("company_id")) not in accepted_company_ids:
            raise ValueError(f"candidate company is outside accepted scope: {claim_id}")
        if active_run_id and str(claim.get("research_run_id")) not in research_registry:
            raise ValueError(f"candidate research run is not registered: {claim_id}")
        if active_run_id and research_registry[str(claim["research_run_id"])].get("company_id") != claim.get("company_id"):
            raise ValueError(f"candidate research run is bound to another company: {claim_id}")
        if active_run_id and not _source_allowed(claim.get("source_url"), source_policy):
            raise ValueError(f"candidate source is outside the active source policy: {claim_id}")
        complete, missing = claim_requirements_met(claim)
        if not complete:
            raise ValueError(f"candidate claim incomplete: {claim_id}: {', '.join(missing)}")
        claims[claim_id] = claim

    decisions: dict[str, dict[str, object]] = {}
    for decision in load_records(decisions_path):
        claim_id = str(decision.get("candidate_claim_id") or "")
        if claim_id in decisions:
            raise ValueError(f"duplicate verifier decision: {claim_id}")
        valid, errors = validate_verifier_decision(decision, claims)
        if not valid:
            raise ValueError(f"invalid verifier decision {claim_id}: {', '.join(errors)}")
        if active_run_id and not run_scope_matches(decision.get("verifier_run_id"), active_run_id):
            raise ValueError(f"verifier decision is outside active run: {claim_id}")
        if active_run_id and str(decision.get("verifier_run_id")) not in verifier_registry:
            raise ValueError(f"verifier run is not registered: {claim_id}")
        if active_run_id:
            registration = verifier_registry[str(decision["verifier_run_id"])]
            if isinstance(registration, dict) and registration.get("verifier_id") != decision.get("verifier_id"):
                raise ValueError(f"verifier is not authorized for active run: {claim_id}")
        decisions[claim_id] = decision

    missing_decisions = sorted(set(claims) - set(decisions))
    if missing_decisions:
        raise ValueError(f"missing verifier decisions: {', '.join(missing_decisions)}")

    promoted: list[dict[str, object]] = []
    for claim_id in sorted(claims):
        if decisions[claim_id]["decision"] != "Verified":
            continue
        claim = dict(claims[claim_id])
        claim["candidate_status"] = "Verified"
        claim["verified_at"] = decisions[claim_id]["verified_at"]
        claim["verifier_run_id"] = decisions[claim_id]["verifier_run_id"]
        errors = sorted(error.message for error in VALIDATOR.iter_errors(claim))
        if errors:
            raise ValueError(f"promoted claim schema invalid: {claim_id}: {'; '.join(errors)}")
        promoted.append(claim)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in promoted:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return promoted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    args = parser.parse_args()
    promoted = promote_verified_claims(args.candidates, args.decisions, args.output, args.run_manifest)
    if args.run_manifest.exists():
        update_run_manifest(args.run_manifest, inputs={"candidate_evidence": args.candidates, "verifier_decisions": args.decisions}, outputs={"verified_evidence": args.output})
    print(json.dumps({"promoted": len(promoted)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
