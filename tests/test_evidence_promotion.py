from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lead_contract import candidate_sha256
from promote_evidence import promote_verified_claims


class EvidencePromotionTests(unittest.TestCase):
    def claim(self) -> dict[str, object]:
        claim = {
            "record_type": "EvidenceClaim",
            "candidate_claim_id": "claim-1",
            "company_id": "company-1",
            "claim_type": "service_fit",
            "claim_value": "Confirmed",
            "source_url": "https://example.de/services",
            "source_kind": "official_site",
            "evidence_excerpt": "Hausverwaltung in Berlin",
            "retrieved_at": "2026-11-08T10:00:00+00:00",
            "account_relationship": "direct",
            "confidence": "high",
            "research_run_id": "run-1",
            "candidate_status": "Candidate",
        }
        claim["candidate_sha256"] = candidate_sha256(claim)
        return claim

    def test_verified_claim_is_promoted_without_mutating_claim_content(self):
        claim = self.claim()
        decision = {
            "record_type": "VerifierDecision",
            "candidate_claim_id": claim["candidate_claim_id"],
            "candidate_sha256": claim["candidate_sha256"],
            "decision": "Verified",
            "reason_codes": ["page_local"],
            "verifier_id": "verifier",
            "verifier_run_id": "run-1",
            "verified_at": "2026-11-08T10:01:00+00:00",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates = root / "candidates.jsonl"
            decisions = root / "decisions.jsonl"
            output = root / "verified.jsonl"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            promoted = promote_verified_claims(candidates, decisions, output)
            self.assertEqual(len(promoted), 1)
            self.assertEqual(promoted[0]["candidate_status"], "Verified")
            for key, value in claim.items():
                if key != "candidate_status":
                    self.assertEqual(promoted[0][key], value)

    def test_hash_mutation_is_rejected(self):
        claim = self.claim()
        decision = {
            "record_type": "VerifierDecision",
            "candidate_claim_id": claim["candidate_claim_id"],
            "candidate_sha256": "f" * 64,
            "decision": "Verified",
            "reason_codes": ["page_local"],
            "verifier_id": "verifier",
            "verifier_run_id": "run-1",
            "verified_at": "2026-11-08T10:01:00+00:00",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates = root / "candidates.jsonl"
            decisions = root / "decisions.jsonl"
            output = root / "verified.jsonl"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                promote_verified_claims(candidates, decisions, output)


if __name__ == "__main__":
    unittest.main()
