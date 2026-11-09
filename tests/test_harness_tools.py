from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from harness_tools import discover_profiles, invoke
from run_manifest import atomic_write, file_sha256, finalization_eligibility, load, reconstruct_finalization_readiness


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

    def test_native_facade_rejects_direct_publication(self):
        with self.assertRaisesRegex(ValueError, "direct publish_staged_output"):
            invoke({"action": "publish_staged_output", "payload": {"run_id": "run-1", "manifest_path": "manifest.json", "staging_path": "staging.xlsx", "final_path": "final.xlsx", "status": "complete"}}, Path.cwd())

    def test_native_facade_requires_finalization_action(self):
        with self.assertRaisesRegex(ValueError, "direct publish_staged_output"):
            invoke({"action": "publish_staged_output", "payload": {"run_id": "run-1", "manifest_path": "manifest.json", "staging_path": "staging.xlsx", "final_path": "final.xlsx", "status": "partial"}}, Path.cwd())

    def test_finalization_rejects_non_integer_delivery_counts(self):
        manifest = {
            "campaign": {"target_count": 1},
            "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
            "coverage": {"status": "complete"},
            "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 1, "delivered_count": 1.9, "shortfall": -0.9},
        }
        eligible, errors = finalization_eligibility(manifest, "strict")
        self.assertFalse(eligible)
        self.assertTrue(any("nonnegative integers" in error for error in errors))

    def test_finalization_reconstructs_required_artifacts_instead_of_trusting_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "workbook.xlsx"
            workbook.write_bytes(b"workbook")
            manifest = root / "manifest.json"
            atomic_write(manifest, {
                "run_id": "run-1", "execution_mode": "production", "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "complete"}, "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 0, "delivered_count": 0, "shortfall": 0},
                "outputs": {"workbook": {"path": "workbook.xlsx", "sha256": file_sha256(workbook)}},
            })
            proof = reconstruct_finalization_readiness(root, manifest, "strict")
            self.assertFalse(proof["ready"])
            self.assertTrue(any("verified evidence artifact" in error for error in proof["errors"]))

    def test_discover_companies_is_bounded_to_repository_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "companies.json"
            source.write_text(json.dumps([{"company_name": "Example GmbH"}, {"company_name": "Other GmbH"}]), encoding="utf-8")
            result = invoke({"action": "discover_companies", "payload": {"path": "companies.json", "limit": 1}}, root)
            self.assertEqual(result["count"], 2)
            self.assertTrue(result["truncated"])
            self.assertEqual(len(result["companies"]), 1)
            with self.assertRaisesRegex(ValueError, "under repository root"):
                invoke({"action": "discover_companies", "payload": {"path": "../companies.json"}}, root)

    def test_normalize_deduplicate_and_identity_adapters_share_company_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"company_name": "Example Hausverwaltung GmbH", "verified_company_domain": "https://example.de", "postal_code": "10115", "city": "Berlin"},
                {"company_name": "Example Hausverwaltung GmbH", "verified_company_domain": "https://example.de", "postal_code": "10115", "city": "Berlin"},
            ]
            normalized = invoke({"action": "normalize_company", "payload": {"company": rows[0]}}, root)["company"]
            result = invoke({"action": "deduplicate_companies", "payload": {"companies": rows}}, root)
            self.assertEqual(result["output_count"], 1)
            self.assertEqual(result["companies"][0]["company_id"], normalized["company_id"])
            identity = invoke({"action": "validate_identity", "payload": {"company": rows[0]}}, root)
            self.assertTrue(identity["valid"])

    def test_promotion_adapter_returns_hashed_verified_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidates = root / "candidates.jsonl"
            decisions = root / "decisions.jsonl"
            output = root / "verified.jsonl"
            claim = {
                "record_type": "EvidenceClaim", "company_id": "C1", "claim_type": "service_fit",
                "claim_value": "Confirmed", "source_url": "https://example.de/services", "source_domain": "example.de",
                "source_kind": "official", "evidence_excerpt": "Residential property management services.",
                "retrieved_at": "2026-11-08T00:00:00+00:00", "published_at": None, "as_of_date": None,
                "account_relationship": "direct", "confidence": "high", "research_run_id": "run-1:signals:C1",
                "candidate_status": "Candidate",
            }
            from lead_contract import candidate_claim_id, candidate_sha256
            claim["candidate_claim_id"] = candidate_claim_id(claim)
            claim["candidate_sha256"] = candidate_sha256(claim)
            decision = {
                "record_type": "VerifierDecision", "candidate_claim_id": claim["candidate_claim_id"],
                "candidate_sha256": claim["candidate_sha256"], "decision": "Verified", "reason_codes": ["page_local"],
                "verifier_id": "test", "verifier_run_id": "verifier-1", "verified_at": "2026-11-08T00:00:01+00:00",
            }
            candidates.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            decisions.write_text(json.dumps(decision) + "\n", encoding="utf-8")
            result = invoke({"action": "promote_evidence", "payload": {
                "candidates_path": "candidates.jsonl", "decisions_path": "decisions.jsonl", "output_path": "verified.jsonl",
            }}, root)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["artifact"]["sha256"], file_sha256(output))

    def test_rank_adapter_reads_jsonl_scores_and_csv_qualification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scores = root / "scores.jsonl"
            qualification = root / "qualification.csv"
            scores.write_text(json.dumps({
                "company_id": "C1", "lead_tier": "A", "evidence_coverage": "90",
                "sales_priority": "High", "assurance_level": "source", "research_gap": "None",
                "structural_lead_fit": "80", "portfolio_potential": "70", "buying_signal": "High",
            }) + "\n", encoding="utf-8")
            qualification.write_text("company_id,resolution_status,berlin_relevance,verified_company_domain,eligible\nC1,Accepted,Confirmed,example.de,true\n", encoding="utf-8")
            result = invoke({"action": "rank_leads", "payload": {
                "scores": "scores.jsonl", "qualification": "qualification.csv", "max_accounts": 1,
            }}, root)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["leads"][0]["company_id"], "C1")

    def test_export_and_qa_adapters_return_artifact_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output.xlsx"
            build_report = root / "build-report.json"
            report = root / "qa-report.json"
            sample = root / "qa-sample.json"

            def fake_run(command, **kwargs):
                if "build_workbook.py" in command[1]:
                    output.write_bytes(b"xlsx")
                    build_report.write_text("{}", encoding="utf-8")
                else:
                    report.write_text("{}", encoding="utf-8")
                    sample.write_text("[]", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("harness_tools.subprocess.run", side_effect=fake_run) as run:
                exported = invoke({"action": "export_workbook", "payload": {
                    "companies": "companies.csv", "scores": "scores.csv", "priority": "priority.csv",
                    "contacts": "contacts.csv", "sources": "sources.csv", "output": "output.xlsx",
                    "build_report": "build-report.json",
                }}, root)
                checked = invoke({"action": "qa_workbook", "payload": {
                    "workbook": "output.xlsx", "schema": "schema.json", "evidence_dir": "evidence",
                    "report": "qa-report.json", "sample_output": "qa-sample.json",
                }}, root)
            self.assertEqual(exported["workbook"]["sha256"], file_sha256(output))
            self.assertEqual(checked["report"]["sha256"], file_sha256(report))
            self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
