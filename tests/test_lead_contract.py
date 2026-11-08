from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lead_contract import actionability_for, is_generic_mailbox, is_placeholder_email, is_plausible_full_name, is_valid_business_email, parse_evidence_urls, sales_priority_for


class LeadContractTests(unittest.TestCase):
    def test_parse_evidence_urls_accepts_csv_and_pipe_values(self):
        self.assertEqual(parse_evidence_urls("https://a.example | https://b.example"), ["https://a.example", "https://b.example"])

    def test_contact_helpers_reject_generic_or_fragment_names(self):
        self.assertTrue(is_generic_mailbox("info@example.com"))
        self.assertFalse(is_plausible_full_name("unseren Immobilienverwaltern"))
        self.assertFalse(is_plausible_full_name("Klare Prozesse"))
        self.assertTrue(is_plausible_full_name("Anna Schmidt"))
        self.assertTrue(is_placeholder_email("max.musterman@mail.com"))
        self.assertFalse(is_valid_business_email("privacy@hubspot.com", "example.de"))
        self.assertTrue(is_valid_business_email("anna@example.de", "example.de"))

    def test_actionability_and_priority_are_deterministic(self):
        self.assertEqual(actionability_for("A", 75, "Strong"), "Ready")
        self.assertEqual(sales_priority_for("Ready", "A"), "Pursue")
        self.assertEqual(actionability_for("A", 75, "None found"), "Monitor")
        self.assertEqual(sales_priority_for("Unknown", "A"), "Defer")


if __name__ == "__main__":
    unittest.main()
