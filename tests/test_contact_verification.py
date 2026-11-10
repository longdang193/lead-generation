from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lead_contract import contact_claim_valid, email_owner_matches_person
from build_shortlist import contact_verified_date, same_person


class ContactVerificationTests(unittest.TestCase):
    def test_navigation_and_role_fragments_are_not_named_contacts(self):
        candidate = {
            "person_name": "Schadensmeldungen Mitgliedschaften",
            "role": "Geschäftsführung",
            "company_affiliation": "Example Hausverwaltung GmbH",
            "source_url": "https://example.de/kontakt",
            "evidence_excerpt": "Schadensmeldungen Mitgliedschaften Geschäftsführung",
        }
        self.assertFalse(contact_claim_valid(candidate, "example.de")[0])

    def test_named_owner_requires_page_local_name_and_role_evidence(self):
        candidate = {
            "person_name": "Anna Schmidt",
            "role": "Geschäftsführerin",
            "company_affiliation": "Example Hausverwaltung GmbH",
            "source_url": "https://example.de/team",
            "evidence_excerpt": "Anna Schmidt, Geschäftsführerin der Example Hausverwaltung GmbH",
            "email": "anna.schmidt@example.de",
        }
        self.assertTrue(contact_claim_valid(candidate, "example.de")[0])

    def test_generic_mailbox_is_separate_from_personal_contact(self):
        candidate = {
            "person_name": "Anna Schmidt",
            "role": "Geschäftsführerin",
            "company_affiliation": "Example Hausverwaltung GmbH",
            "source_url": "https://example.de/team",
            "evidence_excerpt": "Anna Schmidt, Geschäftsführerin der Example Hausverwaltung GmbH",
            "email": "info@example.de",
        }
        self.assertFalse(contact_claim_valid(candidate, "example.de")[0])

    def test_provider_email_must_match_the_named_owner(self):
        self.assertTrue(same_person("Anna Schmidt", "Anna Schmidt"))
        self.assertFalse(same_person("Anna Schmidt", "Peter Müller"))
        self.assertTrue(email_owner_matches_person("anna.schmidt@example.de", "Anna Schmidt"))
        self.assertFalse(email_owner_matches_person("peter.mueller@example.de", "Anna Schmidt"))

    def test_published_email_gets_verification_date(self):
        self.assertEqual(contact_verified_date({}, "info@example.de", today="2026-11-10"), "2026-11-10")
        self.assertEqual(contact_verified_date({"last_verified": "2026-11-01"}, "info@example.de", today="2026-11-10"), "2026-11-01")
        self.assertEqual(contact_verified_date({}, "", today="2026-11-10"), "Unknown")


if __name__ == "__main__":
    unittest.main()
