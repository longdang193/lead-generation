from __future__ import annotations

import argparse
import json
from pathlib import Path

from lead_contract import candidate_sha256, claim_requirements_met, verifier_decision_valid, update_run_manifest


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


def promote_verified_claims(candidates_path: Path, decisions_path: Path, output_path: Path) -> list[dict[str, object]]:
    candidates = load_records(candidates_path)
    claims: dict[str, dict[str, object]] = {}
    for claim in candidates:
        claim_id = str(claim.get("candidate_claim_id") or "")
        if not claim_id or claim_id in claims:
            raise ValueError("candidate claims must have unique candidate_claim_id values")
        if claim.get("candidate_sha256") != candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"}):
            raise ValueError(f"candidate hash mismatch: {claim_id}")
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
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()
    promoted = promote_verified_claims(args.candidates, args.decisions, args.output)
    if args.run_manifest and args.run_manifest.exists():
        update_run_manifest(args.run_manifest, inputs={"candidate_evidence": args.candidates, "verifier_decisions": args.decisions}, outputs={"verified_evidence": args.output})
    print(json.dumps({"promoted": len(promoted)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
