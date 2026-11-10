from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lead_contract import is_plausible_company_name
from normalize_dedupe import explicit_berlin_evidence


class NormalizationTests(unittest.TestCase):
    def test_generic_navigation_title_is_not_a_company_identity(self):
        self.assertFalse(is_plausible_company_name("Über uns"))
        self.assertTrue(is_plausible_company_name("Example Hausverwaltung GmbH"))

    def test_marketing_title_is_not_a_company_identity(self):
        self.assertFalse(is_plausible_company_name("Top Hausverwaltung in Berlin: Ihr Ratgeber für die beste Wahl!"))
        self.assertFalse(is_plausible_company_name("Digitale Hausverwaltung für Berlin und Brandenburg"))
        self.assertFalse(is_plausible_company_name("» Übersicht"))
        self.assertFalse(is_plausible_company_name("ImmoArt Immobilienverwaltung Startseite"))

    def test_city_without_corrobating_postcode_is_not_confirmed_berlin(self):
        self.assertEqual(explicit_berlin_evidence({"city": "Berlin", "postal_code": "", "address": ""}), "Unknown")
        self.assertEqual(explicit_berlin_evidence({"city": "Berlin", "postal_code": "10115", "address": "Invalidenstraße 1"}), "Confirmed")


if __name__ == "__main__":
    unittest.main()
