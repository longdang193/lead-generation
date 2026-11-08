from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from lead_contract import candidate_sha256, claim_requirements_met


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    decisions = []
    for line in args.claims.read_text(encoding="utf-8").splitlines() if args.claims.exists() else []:
        claim = json.loads(line)
        valid, missing = claim_requirements_met(claim)
        if claim.get("candidate_sha256") != candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"}):
            valid = False
            missing = ["candidate_sha256"]
        decisions.append({"record_type": "VerifierDecision", "candidate_claim_id": claim.get("candidate_claim_id"), "candidate_sha256": claim.get("candidate_sha256"), "decision": "Verified" if valid else "Rejected", "reason_codes": ["native_contract"] if valid else missing, "verifier_id": args.profile, "verifier_run_id": f"{args.run_id}:verifier", "verified_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat()})
    args.output.write_text(json.dumps({"decisions": decisions}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
