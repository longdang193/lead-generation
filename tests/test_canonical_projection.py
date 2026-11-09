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
                "assurance_level": "source",
                "verifier_run_id": "run-1:verifier",
                "verified_at": "2026-11-08T10:01:00+00:00",
            }
            claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
            event = {
                **claim,
                "candidate_claim_id": "event-1",
                "claim_type": "event",
                "claim_value": {"event_id": "E1", "event_type": "tender", "buyer": "C1", "title": "Current procurement", "publication_date": "2026-11-07", "deadline": "2026-12-01"},
                "evidence_excerpt": "Current procurement",
                "assurance_level": "source",
            }
            event["candidate_sha256"] = candidate_sha256({key: value for key, value in event.items() if key != "candidate_sha256"})
            promoted.write_text(json.dumps(claim) + "\n" + json.dumps(event) + "\n", encoding="utf-8")
            qualification = root / "qualification.jsonl"
            qualification.write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            scores = root / "scores.csv"
            scores.write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            contacts = root / "contacts.csv"
            contacts.write_text("company_id,contact_name\nC1,Unknown\n", encoding="utf-8")
            outputs = project_verified_evidence(promoted, qualification, scores, contacts, root / "canonical", run_id="run-1")
            row = next(csv.DictReader(outputs["scores"].open(encoding="utf-8")))
            self.assertEqual(row["buying_signal"], "Strong")
            events = json.loads(outputs["events"].read_text(encoding="utf-8"))
            self.assertEqual(events[0]["event_id"], "E1")

    def test_cross_run_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = root / "promoted.jsonl"
            promoted.write_text(json.dumps({"candidate_status": "Verified", "verifier_run_id": "other-run", "company_id": "C1", "claim_type": "service_fit"}) + "\n", encoding="utf-8")
            for name, content in (("qualification.jsonl", "{}\n"), ("scores.csv", "company_id\nC1\n"), ("contacts.csv", "company_id\nC1\n")):
                (root / name).write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside active run"):
                project_verified_evidence(promoted, root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")

    def test_unavailable_signal_research_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = root / "promoted.jsonl"
            promoted.write_text("", encoding="utf-8")
            qualification = root / "qualification.jsonl"
            qualification.write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            scores = root / "scores.csv"
            scores.write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            contacts = root / "contacts.csv"
            contacts.write_text("company_id,contact_name\nC1,Unknown\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "run_id": "run-1",
                "head_sha": "a" * 40,
                "research_runs": {"run-1:signals:C1": {
                    "run_id": "run-1:signals:C1",
                    "company_id": "C1",
                    "research_type": "signals",
                    "status": "Unavailable",
                    "provider_status": "Unavailable",
                    "truncated": False,
                    "attempts": [],
                }},
            }), encoding="utf-8")
            outputs = project_verified_evidence(promoted, qualification, scores, contacts, root / "canonical", run_id="run-1", manifest_path=manifest, root=root)
            audit = next(csv.DictReader(outputs["signal_audit"].open(encoding="utf-8")))
            score = next(csv.DictReader(outputs["scores"].open(encoding="utf-8")))
            self.assertEqual(audit["research_status"], "Unavailable")
            self.assertEqual(audit["search_status"], "Unavailable")
            self.assertEqual(audit["signal_state"], "Unknown")
            self.assertEqual(score["buying_signal"], "Unknown")

    def test_structural_score_claim_is_retained_but_not_scored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim = {
                "record_type": "EvidenceClaim", "candidate_claim_id": "service-1", "company_id": "C1", "claim_type": "service_fit", "claim_value": "Confirmed",
                "source_url": "https://example.de/about", "source_kind": "official_site", "evidence_excerpt": "Service", "retrieved_at": "2026-11-08T10:00:00+00:00",
                "research_run_id": "run-1:signals:C1", "candidate_status": "Supported", "assurance_level": "structural", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00",
            }
            claim["candidate_sha256"] = candidate_sha256({key: value for key, value in claim.items() if key != "candidate_sha256"})
            (root / "promoted.jsonl").write_text(json.dumps(claim) + "\n", encoding="utf-8")
            (root / "qualification.jsonl").write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            (root / "scores.csv").write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            (root / "contacts.csv").write_text("company_id,contact_name\nC1,Unknown\n", encoding="utf-8")
            outputs = project_verified_evidence(root / "promoted.jsonl", root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")
            projected = json.loads(outputs["qualification"].read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(projected["service_fit"], "Confirmed")
            self.assertEqual(projected["field_assurance"]["service_fit"], "structural")
            from score_leads import calculate_fit
            self.assertEqual(calculate_fit(projected), (None, 0))

    def test_projection_keeps_multiple_event_claims_for_one_company(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims = []
            for index in (1, 2):
                claim = {
                    "record_type": "EvidenceClaim", "candidate_claim_id": f"event-claim-{index}", "company_id": "C1", "claim_type": "event",
                    "claim_value": {"event_id": f"E{index}", "publication_date": f"2026-11-0{index}", "deadline": None}, "source_url": f"https://ted.europa.eu/{index}",
                    "source_kind": "procurement", "evidence_excerpt": f"Event {index}", "retrieved_at": "2026-11-08T10:00:00+00:00", "published_at": f"2026-11-0{index}",
                    "account_relationship": "directory", "confidence": "high", "research_run_id": "run-1:signals:C1", "candidate_status": "Verified", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00",
                }
                claims.append(claim)
            (root / "promoted.jsonl").write_text("\n".join(json.dumps(claim) for claim in claims) + "\n", encoding="utf-8")
            (root / "qualification.jsonl").write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            (root / "scores.csv").write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            (root / "contacts.csv").write_text("company_id,contact_name\nC1,Unknown\n", encoding="utf-8")
            outputs = project_verified_evidence(root / "promoted.jsonl", root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")
            events = json.loads(outputs["events"].read_text(encoding="utf-8"))
            self.assertEqual([event["event_id"] for event in events], ["E1", "E2"])

    def test_projection_replaces_base_contacts_without_cross_person_inheritance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claims = []
            for claim_id, person, email in (("contact-1", "Alice Smith", "alice@example.de"), ("contact-2", "Bob Jones", None)):
                claims.append({"record_type": "EvidenceClaim", "candidate_claim_id": claim_id, "company_id": "C1", "claim_type": "contact", "claim_value": person, "person_name": person, "role": "Owner", "email": email, "company_affiliation": "Example", "source_url": "https://example.de/contact", "source_kind": "official", "evidence_excerpt": person, "retrieved_at": "2026-11-08T10:00:00+00:00", "account_relationship": "direct", "confidence": "high", "research_run_id": "run-1:contacts:C1", "candidate_status": "Verified", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"})
            (root / "promoted.jsonl").write_text("\n".join(json.dumps(claim) for claim in claims) + "\n", encoding="utf-8")
            (root / "qualification.jsonl").write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            (root / "scores.csv").write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            (root / "contacts.csv").write_text("company_id,contact_name,contact_email\nC1,Legacy Alice,alice@example.de\nC1,Legacy Bob,bob@example.de\n", encoding="utf-8")
            outputs = project_verified_evidence(root / "promoted.jsonl", root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")
            contacts = list(csv.DictReader(outputs["contacts"].open(encoding="utf-8", newline="")))
            self.assertEqual([(row["contact_name"], row["contact_email"]) for row in contacts], [("Alice Smith", "alice@example.de"), ("Bob Jones", "Unknown")])

    def test_projection_preserves_structural_assurance_in_contacts_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contact = {"record_type": "EvidenceClaim", "candidate_claim_id": "contact-1", "company_id": "C1", "claim_type": "contact", "claim_value": "Alice Smith", "person_name": "Alice Smith", "role": "Owner", "email": "alice@example.de", "company_affiliation": "Example", "source_url": "https://example.de/contact", "source_kind": "official", "evidence_excerpt": "Alice Smith", "retrieved_at": "2026-11-08T10:00:00+00:00", "account_relationship": "direct", "confidence": "high", "research_run_id": "run-1:contacts:C1", "candidate_status": "Supported", "assurance_level": "structural", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
            event = {"record_type": "EvidenceClaim", "candidate_claim_id": "event-1", "company_id": "C1", "claim_type": "event", "claim_value": {"event_id": "E1", "publication_date": "2026-11-01", "deadline": None}, "source_url": "https://ted.europa.eu/event", "source_kind": "procurement", "evidence_excerpt": "Event", "retrieved_at": "2026-11-08T10:00:00+00:00", "published_at": "2026-11-01", "account_relationship": "directory", "confidence": "high", "research_run_id": "run-1:signals:C1", "candidate_status": "Supported", "assurance_level": "structural", "verifier_run_id": "run-1:verifier", "verified_at": "2026-11-08T10:01:00+00:00"}
            (root / "promoted.jsonl").write_text(json.dumps(contact) + "\n" + json.dumps(event) + "\n", encoding="utf-8")
            (root / "qualification.jsonl").write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            (root / "scores.csv").write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            (root / "contacts.csv").write_text("company_id,contact_name,contact_email\nC1,Unknown,Unknown\n", encoding="utf-8")
            outputs = project_verified_evidence(root / "promoted.jsonl", root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")
            contact_row = next(csv.DictReader(outputs["contacts"].open(encoding="utf-8", newline="")))
            event_link = next(csv.DictReader(outputs["event_links"].open(encoding="utf-8", newline="")))
            self.assertEqual(contact_row["verification_status"], "Unverified")
            self.assertEqual(contact_row["assurance_level"], "structural")
            self.assertEqual(event_link["match_confidence"], "Supported")


    def test_projection_preserves_base_contacts_once_without_promoted_contact_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "promoted.jsonl").write_text("", encoding="utf-8")
            (root / "qualification.jsonl").write_text(json.dumps({"company_id": "C1", "resolution_status": "Accepted", "eligible": True}) + "\n", encoding="utf-8")
            (root / "scores.csv").write_text("company_id,buying_signal\nC1,None found\n", encoding="utf-8")
            (root / "contacts.csv").write_text("company_id,contact_name,contact_email,last_verified,projection_run_id\nC1,Alice,alice@example.de,2026-11-01,old-run\nC1,Bob,bob@example.de,2026-11-01,old-run\n", encoding="utf-8")
            outputs = project_verified_evidence(root / "promoted.jsonl", root / "qualification.jsonl", root / "scores.csv", root / "contacts.csv", root / "canonical", run_id="run-1")
            contacts = list(csv.DictReader(outputs["contacts"].open(encoding="utf-8", newline="")))
            self.assertEqual([(row["contact_name"], row["contact_email"]) for row in contacts], [("Alice", "alice@example.de"), ("Bob", "bob@example.de")])
            self.assertEqual({row["projection_run_id"] for row in contacts}, {"old-run"})
if __name__ == "__main__":
    unittest.main()
