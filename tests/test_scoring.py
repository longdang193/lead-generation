from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from score_leads import classify_signal
from extract_website_evidence import claim


class ScoringTests(unittest.TestCase):
    def test_signal_classification_is_freshness_based(self):
        today = date.today()
        self.assertEqual(classify_signal([]), "None found")
        self.assertEqual(classify_signal([{"publication_date": today.isoformat(), "deadline": "Unknown"}]), "Strong")
        self.assertEqual(classify_signal([{"publication_date": (today - timedelta(days=240)).isoformat(), "deadline": "Unknown"}]), "Medium")
        self.assertEqual(classify_signal([{"publication_date": (today - timedelta(days=500)).isoformat(), "deadline": "Unknown"}]), "Weak")
        self.assertEqual(classify_signal([{"publication_date": "Unknown", "deadline": "Unknown"}]), "Unknown")

    def test_ordinary_weg_word_is_not_condominium_evidence(self):
        value, _, _ = claim("Wir weisen den Weg zu guter Verwaltung.", [r"wohnungseigent[üu]mergemeinschaft", r"\bweg[- ]verwaltung\b", r"eigent[üu]mergemeinschaft"])
        self.assertEqual(value, "Unknown")


if __name__ == "__main__":
    unittest.main()
