from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from canonical_projection import project_verified_evidence
from campaign_spec import load_campaign_spec
import orchestrate_enrichment
from orchestrate_enrichment import validate_final_priority_rows
from run_manifest import entry
from select_for_enrichment import select_accounts


class PersonalModeTests(unittest.TestCase):
    def test_personal_policy_selects_best_available_reserve_without_inventing_eligibility(self):
        scores = [
            {"company_id": f"C{index}", "lead_tier": "A", "evidence_coverage": "100", "structural_lead_fit": str(90 - index), "portfolio_potential": "80", "sales_priority": "Pursue", "buying_signal": "Strong"}
            for index in range(5)
        ]
        qualification = {
            f"C{index}": {"company_id": f"C{index}", "resolution_status": "Accepted", "eligible": index != 4}
            for index in range(5)
        }
        selected = select_accounts(scores, qualification, 3, {f"C{index}" for index in range(5)})
        self.assertEqual([row["company_id"] for row in selected], ["C0", "C1", "C2"])
        self.assertFalse(any(row["company_id"] == "C4" for row in selected))
        validate_final_priority_rows(selected, {f"C{index}" for index in range(5)}, 3, "personal")
        with self.assertRaisesRegex(ValueError, "exactly"):
            validate_final_priority_rows(selected, {f"C{index}" for index in range(5)}, 3, "strict")

    def test_projection_emits_eligibility_when_qualification_omits_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = root / "promoted.jsonl"
            qualification = root / "qualification.jsonl"
            scores = root / "scores.csv"
            contacts = root / "contacts.csv"
            output = root / "canonical"
            promoted.write_text("", encoding="utf-8")
            qualification.write_text(json.dumps({"company_id": "C1", "company_name": "Example", "domain": "example.de", "verified_company_domain": "example.de", "resolution_status": "Accepted", "berlin_relevance": "Probable"}) + "\n", encoding="utf-8")
            with scores.open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=["company_id", "buying_signal"]).writeheader()
            with contacts.open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=["company_id", "contact_name"]).writeheader()
            result = project_verified_evidence(promoted, qualification, scores, contacts, output, run_id="run-1", delivery_policy="personal")
            row = json.loads(result["qualification"].read_text(encoding="utf-8").splitlines()[0])
            self.assertTrue(row["eligible"])

    def test_berlin_campaign_defaults_to_personal_delivery(self):
        root = Path(__file__).resolve().parents[1]
        campaign = load_campaign_spec(root, root / "config" / "campaigns" / "berlin-hausverwaltung.json")
        self.assertEqual(campaign.delivery_policy, "personal")

    def test_personal_fixture_backfills_from_reserve_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign_path = root / "config" / "campaigns" / "berlin-hausverwaltung.json"
            campaign_path.parent.mkdir(parents=True)
            source_campaign = Path(__file__).resolve().parents[1] / "config" / "campaigns" / "berlin-hausverwaltung.json"
            campaign_path.write_text(source_campaign.read_text(encoding="utf-8"), encoding="utf-8")
            shortlist = root / "shortlist.csv"
            with shortlist.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_id", "company_name", "domain", "verified_company_domain", "city", "resolution_status"])
                writer.writeheader()
                for index in range(35):
                    writer.writerow({"company_id": f"R{index:02d}", "company_name": f"Reserve Company {index:02d}", "domain": f"reserve{index:02d}.de", "verified_company_domain": f"reserve{index:02d}.de", "city": "Berlin", "resolution_status": "Accepted"})
            manifest = root / "evidence" / "manifests" / "personal.json"
            manifest.parent.mkdir(parents=True)
            revision = __import__("subprocess").run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
            campaign = load_campaign_spec(root, campaign_path).manifest_record()
            manifest.write_text(json.dumps({"run_id": "personal-1", "head_sha": revision, "git_revision": revision, "config_version": "lead-enrichment-run-v1", "campaign": campaign, "generated_at": "2026-11-08T00:00:00+00:00", "accepted_company_ids": [f"R{index:02d}" for index in range(35)], "inputs": {"provisional_shortlist": entry(root, shortlist)}, "outputs": {}, "barriers": {}},), encoding="utf-8")
            argv = ["orchestrate_enrichment.py", "run", "--root", str(root), "--manifest", str(manifest), "--shortlist", str(shortlist), "--campaign-config", str(campaign_path), "--fixture"]
            with patch.object(sys, "argv", argv):
                self.assertEqual(orchestrate_enrichment.main(), 0)
            priority = list(csv.DictReader((root / "data" / "processed" / "personal-1" / "priority.csv").open(encoding="utf-8", newline="")))
            self.assertEqual(len(priority), 30)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["delivery_policy"], "personal")


if __name__ == "__main__":
    unittest.main()
