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

    def test_personal_source_policy_accepts_company_alias_and_approved_external_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims = []
            for claim_id, source_url, source_kind in (
                ("alias-claim", "https://portal.example.de/services", "official_site"),
                ("ted-claim", "https://ted.europa.eu/notice/1", "procurement"),
            ):
                claim = self.claim()
                claim.update({"candidate_claim_id": claim_id, "research_run_id": "run-1:signals:company-1", "source_url": source_url, "source_kind": source_kind})
                claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
                claims.append(claim)
            decisions = [{"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["source_bound"], "verifier_id": "verifier", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"} for claim in claims]
            candidates_path, decisions_path, output_path, manifest_path = (root / name for name in ("candidates.jsonl", "decisions.jsonl", "promoted.jsonl", "active_run.json"))
            candidates_path.write_text("\n".join(json.dumps(claim) for claim in claims) + "\n", encoding="utf-8")
            decisions_path.write_text("\n".join(json.dumps(decision) for decision in decisions) + "\n", encoding="utf-8")
            manifest_path.write_text(json.dumps({
                "run_id": "run-1", "delivery_policy": "personal", "accepted_company_ids": ["company-1"],
                "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}},
                "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier", "capability": "structural_validation"}},
                "source_policy": {"allowed_domains": ["example.de"], "company_domains": {"company-1": "example.de"}, "company_domain_aliases": {"company-1": ["portal.example.de"]}, "approved_external_domains": ["ted.europa.eu"], "external_source_kinds": ["procurement"]},
            }), encoding="utf-8")
            promoted = promote_verified_claims(candidates_path, decisions_path, output_path, manifest_path)
            self.assertEqual({claim["candidate_claim_id"] for claim in promoted}, {"alias-claim", "ted-claim"})

    def test_active_run_rejects_cross_run_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim = self.claim()
            claim["research_run_id"] = "other-run:signals:C1"
            claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
            candidates = root / "candidates.jsonl"
            decisions = root / "decisions.jsonl"
            output = root / "promoted.jsonl"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps({
                "record_type": "VerifierDecision",
                "candidate_claim_id": claim["candidate_claim_id"],
                "candidate_sha256": claim["candidate_sha256"],
                "decision": "Verified",
                "reason_codes": ["page_local"],
                "verifier_id": "verifier",
                "verifier_run_id": "run-1",
                "verified_at": "2026-11-08T10:01:00+00:00",
            }) + "\n", encoding="utf-8")
            manifest = root / "active_run.json"
            manifest.write_text(json.dumps({
                "run_id": "run-1",
                "accepted_company_ids": ["company-1"],
                "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}},
                "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier"}},
                "source_policy": {"allowed_domains": ["example.de"]},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside active run"):
                promote_verified_claims(candidates, decisions, output, manifest)

    def test_active_run_rejects_prefix_collision(self):
        claim = self.claim()
        claim["research_run_id"] = "run-10:signals:company-1"
        claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
        decision = {"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"], "verifier_id": "verifier", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates, decisions, output, manifest = root / "candidates.jsonl", root / "decisions.jsonl", root / "promoted.jsonl", root / "active_run.json"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            manifest.write_text(json.dumps({"run_id": "run-1", "accepted_company_ids": ["company-1"], "research_runs": {}, "verifier_runs": {}, "source_policy": {"allowed_domains": ["example.de"]}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside active run"):
                promote_verified_claims(candidates, decisions, output, manifest)

    def test_active_run_rejects_unregistered_verifier(self):
        claim = self.claim()
        claim["research_run_id"] = "run-1:signals:company-1"
        claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
        decision = {"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"], "verifier_id": "verifier", "verifier_run_id": "run-1:other-verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates, decisions, output, manifest = root / "candidates.jsonl", root / "decisions.jsonl", root / "promoted.jsonl", root / "active_run.json"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            manifest.write_text(json.dumps({"run_id": "run-1", "accepted_company_ids": ["company-1"], "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}}, "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier"}}, "source_policy": {"allowed_domains": ["example.de"]}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not registered"):
                promote_verified_claims(candidates, decisions, output, manifest)

    def test_active_run_rejects_source_from_another_admitted_company(self):
        claim = self.claim()
        claim["research_run_id"] = "run-1:signals:company-1"
        claim["source_url"] = "https://other.example.de/services"
        claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
        decision = {"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"], "verifier_id": "verifier", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates, decisions, output, manifest = root / "candidates.jsonl", root / "decisions.jsonl", root / "promoted.jsonl", root / "active_run.json"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            manifest.write_text(json.dumps({"run_id": "run-1", "accepted_company_ids": ["company-1"], "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}}, "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier"}}, "source_policy": {"allowed_domains": ["trusted.de", "other.example.de"], "company_domains": {"company-1": "trusted.de"}}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source is outside the active source policy"):
                promote_verified_claims(candidates, decisions, output, manifest)

    def test_production_promotion_rejects_structural_verifier_capability(self):
        claim = self.claim()
        claim["research_run_id"] = "run-1:signals:company-1"
        claim["source_url"] = "https://example.de/services"
        claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
        decision = {"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"], "verifier_id": "verifier", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates, decisions, output, manifest = root / "candidates.jsonl", root / "decisions.jsonl", root / "promoted.jsonl", root / "active_run.json"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            manifest.write_text(json.dumps({"run_id": "run-1", "execution_mode": "production", "accepted_company_ids": ["company-1"], "campaign": {"normalized": {"adapter_policy": {"verification_mode": "source_verification"}}}, "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}}, "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier", "capability": "structural_validation"}}, "source_policy": {"allowed_domains": ["example.de"], "company_domains": {"company-1": "example.de"}}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_verification verifier capability"):
                promote_verified_claims(candidates, decisions, output, manifest)

    def test_production_promotion_rejects_structural_campaign_policy(self):
        claim = self.claim()
        claim["research_run_id"] = "run-1:signals:company-1"
        claim["source_url"] = "https://example.de/services"
        claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
        decision = {"record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"], "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"], "verifier_id": "verifier", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates, decisions, output, manifest = root / "candidates.jsonl", root / "decisions.jsonl", root / "promoted.jsonl", root / "active_run.json"
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            manifest.write_text(json.dumps({"run_id": "run-1", "execution_mode": "production", "accepted_company_ids": ["company-1"], "campaign": {"normalized": {"adapter_policy": {"verification_mode": "structural_validation"}}}, "research_runs": {"run-1:signals:company-1": {"research_run_id": "run-1:signals:company-1", "company_id": "company-1"}}, "verifier_runs": {"run-1:verifier": {"verifier_run_id": "run-1:verifier", "verifier_id": "verifier", "capability": "structural_validation"}}, "source_policy": {"allowed_domains": ["example.de"], "company_domains": {"company-1": "example.de"}}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_verification verifier capability"):
                promote_verified_claims(candidates, decisions, output, manifest)

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

    def test_schema_invalid_candidate_is_rejected_before_promotion(self):
        claim = self.claim()
        del claim["record_type"]
        decision = {
            "record_type": "VerifierDecision",
            "candidate_claim_id": "claim-1",
            "candidate_sha256": candidate_sha256(claim),
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
