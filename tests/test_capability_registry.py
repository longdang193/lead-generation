from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from capability_registry import authorize_capability, load_capability_registry, resolve_capability, validate_profile_capabilities


class CapabilityRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_registry_defines_trust_states_and_gap_capabilities(self):
        registry = load_capability_registry(self.root)
        self.assertEqual(set(registry["evidence_statuses"]), {"DISCOVERY", "CANDIDATE_EVIDENCE", "VERIFIED_EVIDENCE"})
        self.assertEqual(registry["capabilities"]["web_search"]["default_evidence_status"], "DISCOVERY")
        self.assertEqual(registry["capabilities"]["official_source_fetch"]["default_evidence_status"], "CANDIDATE_EVIDENCE")
        self.assertEqual(registry["capabilities"]["semantic_review"]["default_evidence_status"], "VERIFIED_EVIDENCE")
        self.assertFalse(registry["evidence_statuses"]["DISCOVERY"]["promotable_without_verification"])
        self.assertFalse(registry["evidence_statuses"]["CANDIDATE_EVIDENCE"]["promotable_without_verification"])

    def test_resolution_keeps_provider_choice_with_parent_runtime(self):
        resolution = resolve_capability(self.root, "web_search", ["ted", "apify"])
        self.assertEqual(resolution["available_providers"], ["apify"])
        self.assertEqual(resolution["resolution_status"], "available")
        self.assertEqual(resolution["provider_selection"], "parent_runtime")
        self.assertEqual(resolution["default_evidence_status"], "DISCOVERY")

    def test_unavailable_provider_is_explicit(self):
        resolution = resolve_capability(self.root, "procurement_search", ["apify"])
        self.assertEqual(resolution["resolution_status"], "unavailable")
        self.assertEqual(resolution["available_providers"], [])

    def test_profile_capabilities_are_registry_bound(self):
        capabilities = validate_profile_capabilities(self.root, ["web_search", "official_source_fetch"])
        self.assertEqual(capabilities, ["web_search", "official_source_fetch"])
        with self.assertRaisesRegex(ValueError, "unknown agent capabilities"):
            validate_profile_capabilities(self.root, ["made_up_provider"])

    def test_authorization_enforces_profile_allowlist_and_provider_binding(self):
        authorized = authorize_capability(self.root, "signal-researcher", "procurement_search", "ted")
        self.assertEqual(authorized["capability"], "procurement_search")
        with self.assertRaisesRegex(ValueError, "not allowed capability"):
            authorize_capability(self.root, "contact-researcher", "procurement_search")
        with self.assertRaisesRegex(ValueError, "not configured"):
            authorize_capability(self.root, "signal-researcher", "procurement_search", "hunter")


if __name__ == "__main__":
    unittest.main()
