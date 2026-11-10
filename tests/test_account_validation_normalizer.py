import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from normalize_account_validation import normalize_record
from typed_contracts import AccountIndicator, AccountThesis, SelectionRationale


class AccountValidationNormalizerTests(unittest.TestCase):
    def test_normalizes_name_alias_and_infers_turn_count(self):
        record = normalize_record(
            {
                "company_id": "C1",
                "name": "Example Hausverwaltung",
                "domain": "example.de",
                "actions": [
                    {"action": "official_profile", "status": "completed"},
                    {"action": "dated_change", "status": "stopped"},
                ],
            }
        )

        self.assertEqual(record["company_name"], "Example Hausverwaltung")
        self.assertEqual(record["selection_turns_used"], 2)
        self.assertEqual(len(record["actions"]), 2)

    def test_normalizes_source_attempts_into_action_sources(self):
        record = normalize_record(
            {
                "company_id": "C1",
                "company_name": "Example Hausverwaltung",
                "actions": [
                    {
                        "selection_next_action": 1,
                        "action_type": "official_profile",
                        "source_attempts": [
                            {"url": "https://example.de/", "status": "completed"}
                        ],
                    }
                ],
            }
        )

        self.assertEqual(record["actions"][0]["source_urls"], ["https://example.de/"])

    def test_accepts_source_url_alias_from_controller_receipts(self):
        record = normalize_record(
            {
                "company_id": "C1",
                "company_name": "Example Hausverwaltung",
                "actions": [
                    {
                        "source_attempts": [
                            {"source_url": "https://example.de/about", "status": "completed"}
                        ]
                    }
                ],
            }
        )

        self.assertEqual(record["actions"][0]["source_urls"], ["https://example.de/about"])

    def test_requires_company_id(self):
        with self.assertRaises(ValueError):
            normalize_record({"company_name": "Missing ID", "actions": []})

    def test_proactive_account_requires_account_evidence_beyond_fit(self):
        with self.assertRaisesRegex(ValueError, "account evidence"):
            AccountThesis(
                company_id="C1",
                offer_id="offer-1",
                offer_version="v1",
                structural_fit=90,
                confidence="medium",
                why_this_account="Fit",
                why_now="Unknown",
                problem_hypothesis="Unknown",
                strongest_claim_ids=["claim-1"],
                semantic_review_ids=["review-1"],
                access_summary="Unknown",
                research_gap_impact="Need evidence",
                recommended_action="Research",
                decision_class="proactive_account",
                readiness_decision="proactive_qualified",
                selection_rationale=SelectionRationale(
                    summary="Fit",
                    observations=[
                        {
                            "observation": "Fit",
                            "implication": "Unknown",
                            "claim_id": "claim-1",
                            "source_url": "https://example.com",
                        }
                    ],
                    opportunity_hypothesis="Unknown",
                    counterevidence=[],
                    confidence="medium",
                    comparative_basis="Fit only",
                    reversal_condition="Any contrary evidence",
                    recommended_action="Research",
                    unresolved_gaps=["Need evidence"],
                ),
            )

    def test_sales_ready_requires_problem_and_current_change_evidence(self):
        with self.assertRaisesRegex(ValueError, "sales_ready requires"):
            AccountThesis(
                company_id="C1",
                offer_id="offer-1",
                offer_version="v1",
                structural_fit=90,
                confidence="high",
                why_this_account="Fit",
                why_now="Now",
                problem_hypothesis="Need",
                strongest_claim_ids=["claim-1"],
                semantic_review_ids=["review-1"],
                access_summary="Buyer",
                research_gap_impact="None",
                recommended_action="Contact",
                decision_class="sales_ready",
                readiness_decision="sales_ready",
                access_verified=True,
                access_person="Buyer",
                access_role="Owner",
                access_channel="email",
                comparative_rationale="Better fit",
                next_alternative_company_id="C2",
                reversal_condition="Problem disproven",
                access_claim_ids=["claim-1"],
                indicators=[
                    AccountIndicator(
                        company_id="C1",
                        offer_id="offer-1",
                        offer_version="v1",
                        indicator_type="change_readiness",
                        statement="Current change",
                        strength=80,
                        confidence="high",
                        supporting_claim_ids=["claim-1"],
                        offer_criterion="relevant_triggers",
                    )
                ],
                selection_rationale=SelectionRationale(
                    summary="Ready",
                    observations=[
                        {
                            "observation": "Change",
                            "implication": "Act",
                            "claim_id": "claim-1",
                            "source_url": "https://example.com",
                        }
                    ],
                    opportunity_hypothesis="Need",
                    counterevidence=[],
                    confidence="high",
                    comparative_basis="Stronger",
                    reversal_condition="Disproved",
                    recommended_action="Contact",
                    unresolved_gaps=[],
                ),
            )


if __name__ == "__main__":
    unittest.main()
