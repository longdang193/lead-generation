from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from harness_tools import discover_profiles, invoke


class HarnessToolTests(unittest.TestCase):
    def test_profile_discovery_uses_existing_registry(self):
        profiles = discover_profiles(Path(__file__).resolve().parents[1])
        self.assertTrue({item["name"] for item in profiles} >= {"signal-researcher", "evidence-verifier"})

    def test_json_boundary_validates_goal(self):
        result = invoke({"action": "validate_goal", "payload": {"goal_id": "g1", "objective": "find leads"}}, Path(__file__).resolve().parents[1])
        self.assertEqual(result["goal"]["goal_id"], "g1")

    def test_json_boundary_validates_evidence_and_thesis(self):
        claim = {
            "claim_id": "c1", "company_id": "C1", "claim_type": "event", "value": {"event_id": "E1"},
            "source_url": "https://example.com/source", "evidence_excerpt": "Observed", "source_kind": "official_site",
            "confidence": "high", "retrieved_at": "2026-11-09T00:00:00Z", "assurance_level": "source",
        }
        self.assertTrue(invoke({"action": "validate_evidence", "payload": claim}, Path.cwd())["validated"])
        thesis = {"company_id": "C1", "structural_fit": 80, "confidence": "high", "recommended_action": "research", "claims": [claim], "hypotheses": [{"company_id": "C1", "hypothesis_type": "opportunity", "statement": "Likely", "supporting_claim_ids": ["c1"], "confidence": "medium"}]}
        self.assertTrue(invoke({"action": "validate_thesis", "payload": thesis}, Path.cwd())["validated"])

    def test_cli_rejects_malformed_request_with_structured_error(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "harness_tools.py"
        result = subprocess.run([sys.executable, str(script)], input=json.dumps({"action": "validate_goal", "payload": {"unexpected": True}}), text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"ok": false', result.stdout)

    def test_tool_boundary_does_not_import_legacy_orchestrator(self):
        source = (Path(__file__).resolve().parents[1] / "scripts" / "harness_tools.py").read_text(encoding="utf-8")
        self.assertNotIn("run_pipeline", source)

    def test_legacy_cli_fails_closed_without_explicit_opt_in(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "orchestrate_enrichment.py"
        result = subprocess.run([sys.executable, str(script), "run", "--manifest", "missing.json", "--shortlist", "missing.csv"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("live legacy execution is disabled", result.stdout)


if __name__ == "__main__":
    unittest.main()

