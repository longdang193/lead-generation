from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from harness_tools import discover_profiles, invoke
from run_manifest import atomic_write, file_sha256, finalization_eligibility, load, reconstruct_finalization_readiness
from action_lifecycle import admit_action, canonical_request_hash, settle_action, validate_result
from action_receipts import canonical_json
from typed_contracts import WorkerResult


class HarnessToolTests(unittest.TestCase):
    def test_profile_discovery_uses_existing_registry(self):
        profiles = discover_profiles(Path(__file__).resolve().parents[1])
        self.assertTrue({item["name"] for item in profiles} >= {"signal-researcher", "evidence-verifier"})
        signal = next(item for item in profiles if item["name"] == "signal-researcher")
        self.assertEqual(signal["task_function"], "account-scoped buying-signal evidence collection")
        self.assertIn("buying-signal-research", signal["skills"])

    def test_json_boundary_validates_goal(self):
        result = invoke({"action": "validate_goal", "payload": {"goal_id": "g1", "objective": "find leads"}}, Path(__file__).resolve().parents[1])
        self.assertEqual(result["goal"]["goal_id"], "g1")

    def test_parent_selected_native_trace_replays_profile_skills_and_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atomic_write(root / "manifest.json", {"run_id": "run-native", "budget_limit": 1})
            request = {
                "run_id": "run-native", "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1",
                "action_type": "signals", "scope": "signals:C1", "contract_version": "1", "strategy_version": "1",
                "profile_version": "signal-v1", "profile_name": "account-intelligence-researcher",
                "skills": ["account-research", "lead-evidence"], "idempotency_key": "native/action-1",
                "budget_units": 1, "provenance": {"source": "parent-codex"}, "request_hash": "0" * 64,
            }
            request["request_hash"] = canonical_request_hash(request)
            invoke({"action": "admit_action", "payload": {**request, "manifest_path": "manifest.json"}}, root)
            result = {"claims": 1}
            result_hash = hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest()
            invoke({"action": "validate_result", "payload": {"run_id": "run-native", "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1", "status": "Completed", "result": result, "result_hash": result_hash}}, root)
            invoke({"action": "record_receipt", "payload": {**request, "result_hash": result_hash, "terminal_status": "Completed", "budget_requested": 1, "budget_settled": 1, "stop_decision": {"run_id": "run-native", "company_id": "C1", "decision": "stop", "reason": "complete"}, "created_at": datetime.now(timezone.utc).isoformat()}}, root)
            replay = invoke({"action": "replay_lifecycle", "payload": {"run_id": "run-native"}}, root)
            self.assertEqual(replay["action_count"], 1)
            self.assertEqual(replay["actions"][0]["profile_name"], "account-intelligence-researcher")
            self.assertEqual(replay["actions"][0]["skills"], ["account-research", "lead-evidence"])
            self.assertEqual(replay["actions"][0]["stop_decision"]["decision"], "stop")

    def test_json_boundary_validates_evidence_and_thesis(self):
        claim = {
            "claim_id": "c1", "company_id": "C1", "claim_type": "event", "value": {"event_id": "E1"},
            "source_url": "https://example.com/source", "evidence_excerpt": "Observed", "source_kind": "official_site",
            "confidence": "high", "retrieved_at": "2026-11-09T00:00:00Z", "assurance_level": "source",
        }
        self.assertTrue(invoke({"action": "validate_evidence", "payload": claim}, Path.cwd())["validated"])
        thesis = {"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 80, "confidence": "high", "why_this_account": "Fit", "why_now": "Now", "problem_hypothesis": "Need", "strongest_claim_ids": ["c1"], "semantic_review_ids": ["a1"], "access_summary": "Contact path", "research_gap_impact": "Could change action", "recommended_action": "research", "claims": [claim], "semantic_reviews": [{"assertion_id": "a1", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "reviewed_claim_ids": ["c1"], "offer_criterion": "relevant_triggers", "entailment": "supported", "offer_relevance": "relevant", "temporal_relevance": "current", "contradiction_result": "none", "decision": "approved", "reason_codes": ["supported"], "reviewer_id": "reviewer-1"}], "hypotheses": [{"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "hypothesis_type": "opportunity", "statement": "Likely", "supporting_claim_ids": ["c1"], "confidence": "medium"}]}
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

    def test_strict_finalization_requires_verifier_coverage_for_each_accepted_company(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            atomic_write(manifest, {
                "run_id": "run-1",
                "execution_mode": "production",
                "budget_limit": 2,
                "accepted_company_ids": ["C1"],
                "admitted_work_items": [{"company_id": "C1", "lane": "signals", "scope": "signals:C1"}],
                "authorization": {
                    "accepted_company_ids": ["C1"],
                    "allowed_action_types": ["signals"],
                    "scope_prefixes": {"signals": "signals:"},
                    "contract_version": "1",
                    "strategy_version": "1",
                    "profile_versions": {"signals": "signals-v1"},
                },
                "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "complete"},
                "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 1, "delivered_count": 1, "shortfall": 0},
            })
            request = {
                "run_id": "run-1", "action_id": "signals:C1", "attempt_id": "signals:C1:attempt-1", "company_id": "C1",
                "action_type": "signals", "scope": "signals:C1", "contract_version": "1", "strategy_version": "1",
                "profile_version": "signals-v1", "idempotency_key": "signals:C1/attempt-1", "budget_units": 1,
                "provenance": {"source": "test"},
            }
            request["request_hash"] = canonical_request_hash(request)
            admit_action(root, request, manifest)
            result_payload = {"ok": True}
            result_hash = hashlib.sha256(canonical_json(result_payload).encode("utf-8")).hexdigest()
            validated = validate_result(root, WorkerResult(
                run_id="run-1", action_id="signals:C1", attempt_id="signals:C1:attempt-1", company_id="C1",
                status="Completed", result=result_payload, result_hash=result_hash, provenance={"source": "test"},
            ))
            settle_action(root, {
                **request,
                "result_hash": validated.result_hash,
                "terminal_status": "Completed",
                "budget_requested": 1,
                "budget_settled": 1,
                "coverage_delta": {"signals": 1},
                "created_at": datetime.now(timezone.utc),
            })
            proof = reconstruct_finalization_readiness(root, manifest, "strict")
            self.assertFalse(proof["ready"])
            self.assertTrue(any("completed verifier action" in error for error in proof["errors"]))

    def test_finalization_rejects_unrelated_artifacts_and_failed_qa(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "verified.jsonl"
            scores = root / "scores.csv"
            priority = root / "priority.csv"
            qa_report = root / "qa.md"
            qa_sample = root / "qa.csv"
            workbook = root / "workbook.xlsx"
            evidence.write_text(json.dumps({"company_id": "FOREIGN", "source_url": "https://example.com", "evidence_excerpt": "unrelated", "research_run_id": "run-1:signals:FOREIGN"}) + "\n", encoding="utf-8")
            scores.write_text("company_id\nFOREIGN\n", encoding="utf-8")
            priority.write_text("company_id\nFOREIGN\n", encoding="utf-8")
            qa_report.write_text("- Errors: 99\n", encoding="utf-8")
            qa_sample.write_text("company_id,lead_tier\nFOREIGN,A\n", encoding="utf-8")
            workbook.write_bytes(b"not-an-xlsx")
            manifest = root / "manifest.json"
            outputs = {
                "verified_evidence": {"path": "verified.jsonl", "sha256": file_sha256(evidence)},
                "scores": {"path": "scores.csv", "sha256": file_sha256(scores)},
                "priority": {"path": "priority.csv", "sha256": file_sha256(priority)},
                "qa_report": {"path": "qa.md", "sha256": file_sha256(qa_report)},
                "qa_sample": {"path": "qa.csv", "sha256": file_sha256(qa_sample)},
                "workbook": {"path": "workbook.xlsx", "sha256": file_sha256(workbook)},
            }
            atomic_write(manifest, {
                "run_id": "run-1", "execution_mode": "production", "accepted_company_ids": ["C1"],
                "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "complete"}, "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 0, "delivered_count": 0, "shortfall": 0},
                "outputs": outputs,
            })
            proof = reconstruct_finalization_readiness(root, manifest, "strict")
            self.assertFalse(proof["ready"])
            self.assertTrue(any("zero-error" in error for error in proof["errors"]))
            self.assertTrue(any("outside the admitted run scope" in error for error in proof["errors"]))

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

    def test_rank_adapter_uses_offer_bound_commercial_ordering(self):
        scores = [
            {"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "semantic_review_ids": ["r1"], "strongest_claim_ids": ["c1"], "lead_tier": "A", "evidence_coverage": 90, "structural_lead_fit": 70, "opportunity_score": 80, "need_score": 85, "change_score": 100, "direct_intent_score": 70, "access_score": 60, "evidence_confidence_score": 90, "buying_signal": "Verified trigger"},
            {"company_id": "C2", "offer_id": "offer-1", "offer_version": "2026-11-09", "semantic_review_ids": ["r2"], "strongest_claim_ids": ["c2"], "lead_tier": "A", "evidence_coverage": 90, "structural_lead_fit": 95, "opportunity_score": 40, "need_score": 30, "change_score": 0, "direct_intent_score": 0, "access_score": 60, "evidence_confidence_score": 80, "buying_signal": "No trigger found"},
        ]
        reviews = [
            {"assertion_id": "r1", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "reviewed_claim_ids": ["c1"], "offer_criterion": "relevant_triggers", "entailment": "supported", "offer_relevance": "relevant", "temporal_relevance": "current", "contradiction_result": "none", "decision": "approved", "reason_codes": ["supported"], "reviewer_id": "reviewer-1"},
            {"assertion_id": "r2", "company_id": "C2", "offer_id": "offer-1", "offer_version": "2026-11-09", "reviewed_claim_ids": ["c2"], "offer_criterion": "relevant_triggers", "entailment": "supported", "offer_relevance": "relevant", "temporal_relevance": "current", "contradiction_result": "none", "decision": "approved", "reason_codes": ["supported"], "reviewer_id": "reviewer-1"},
        ]
        qualification = {company_id: {"resolution_status": "Accepted", "eligible": True} for company_id in ("C1", "C2")}
        result = invoke({"action": "rank_leads", "payload": {"scores": scores, "qualification": qualification, "offer_id": "offer-1", "offer_version": "2026-11-09", "semantic_reviews": reviews, "max_accounts": 2}}, Path.cwd())
        self.assertEqual([row["company_id"] for row in result["leads"]], ["C1", "C2"])

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
