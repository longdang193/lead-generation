from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from canonical_projection import project_verified_evidence
from lead_contract import candidate_sha256


class CanonicalProjectionTests(unittest.TestCase):
    def test_verified_claims_project_deterministically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = root / "promoted.jsonl"
            claim = {
                "record_type": "EvidenceClaim",
                "candidate_claim_id": "claim-1",
                "company_id": "C1",
                "claim_type": "buying_signal",
                "claim_value": "Strong",
                "source_url": "https://example.de/news",
                "source_kind": "official_site",
                "evidence_excerpt": "C1 announces a new project",
                "retrieved_at": "2026-11-08T10:00:00+00:00",
                "published_at": "2026-11-07",
                "account_relationship": "direct",
                "confidence": "high",
                "research_run_id": "run-1:signals:C1",
                "candidate_status": "Verified",
                "verifier_run_id": "run-1:verifier",
                "verified_at": "2026-11-08T10:01:00+00:00",
            }
            claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
            promoted.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            qualification = root / "qualification.jsonl"
            qualification.write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            scores = root / "scores.csv"
            scores.write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            contacts = root / "contacts.csv"
            contacts.write_text("company_id,contact_name\nC1,Unknown\n", encoding="utf-8")
            outputs = project_verified_evidence(promoted, qualification, scores, contacts, root / "canonical", run_id="run-1")
            row = next(csv.DictReader(outputs["scores"].open(encoding="utf-8")))
            self.assertEqual(row["buying_signal"], "Strong")
            self.assertEqual(next(outputs["events"].open(encoding="utf-8")).strip(), "event_id,company_id,match_method,match_confidence,source_url")

    def test_cross_run_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = root / "promoted.jsonl"
            promoted.write_text(json.dumps({"candidate_status": "Verified", "verifier_run_id": "other-run", "company_id": "C1", "claim_type": "service_fit"}) + "\n", encoding="utf-8")
            for name, content in (("qualification.jsonl", "{}\n"), ("scores.csv", "company_id\nC1\n"), ("contacts.csv", "company_id\nC1\n")):
                (root / name).write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside active run"):
                project_verified_evidence(promoted, root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")


if __name__ == "__main__":
    unittest.main()
