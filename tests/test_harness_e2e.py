from __future__ import annotations

import hashlib
import json
import csv
import sys
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from account_intelligence import project_account_intelligence
from action_lifecycle import canonical_request_hash, replay_lifecycle
from action_receipts import replay_run
from harness_tools import invoke
from orchestrate_enrichment import create_run_manifest, run_pipeline
from run_manifest import atomic_write, file_sha256, finalization_eligibility, load, reconstruct_finalization_readiness
import run_manifest


def _claim(claim_id: str, company_id: str, claim_type: str, value: object) -> dict[str, object]:
    return {
        "claim_id": claim_id, "company_id": company_id, "claim_type": claim_type, "value": value,
        "source_url": "https://example.com/account", "evidence_excerpt": "Page-local evidence",
        "source_kind": "official_site", "confidence": "high", "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "candidate_status": "Verified",
        "assurance_level": "source",
    }


class HarnessE2ETests(unittest.TestCase):
    def _production_fixture(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        campaign = {
            "campaign_id": "e2e-production",
            "version": "2026-11-09",
            "target_count": 1,
            "qualification": {
                "resolution_status": "Accepted",
                "city": "Berlin",
                "berlin_relevance": "Confirmed",
                "service_fit": "Hausverwaltung",
                "residential_weg": True,
                "trusted_domain_field": "verified_company_domain",
            },
            "input_bindings": {
                "qualification": "data/qualification.jsonl",
                "scores": "data/scores.csv",
                "contacts": "data/contacts.csv",
                "companies": "data/companies.csv",
                "sources": "data/sources.csv",
                "buying_events": "data/events.json",
                "event_links": "data/event_links.csv",
            },
            "lanes": ["signals", "portfolio", "contacts"],
            "adapter_policy": {
                "worker_profile": "local-stub",
                "verifier_profile": "local-verifier",
                "verification_mode": "source_verification",
                "source_policy": {
                    "approved_external_domains": ["ted.europa.eu"],
                    "external_source_kinds": ["procurement", "public_news"],
                    "company_domain_aliases": {},
                },
            },
            "delivery_policy": "strict",
        }
        campaign_path = root / "config" / "campaigns" / "e2e.json"
        campaign_path.parent.mkdir(parents=True, exist_ok=True)
        campaign_path.write_text(json.dumps(campaign), encoding="utf-8")
        (root / "data").mkdir(parents=True, exist_ok=True)
        (root / "data" / "qualification.jsonl").write_text(
            json.dumps({
                "company_id": "C1",
                "company_name": "Example Hausverwaltung GmbH",
                "domain": "example.de",
                "source_url": "https://example.de/about",
                "retrieved_at": "2026-11-09T00:00:00+00:00",
                "resolution_status": "Accepted",
                "eligible": True,
                "berlin_relevance": "Confirmed",
                "service_fit": "Hausverwaltung",
                "residential_weg": "Confirmed",
            }) + "\n",
            encoding="utf-8",
        )
        score_fields = [
            "company_id", "company_name", "domain", "source_url", "service_fit", "residential_weg",
            "portfolio_size", "portfolio_potential", "berlin_relevance", "structural_lead_fit",
            "evidence_coverage", "buying_signal", "signal_search_status", "actionability", "sales_priority",
            "lead_tier", "evidence_urls", "buying_signal_event_ids", "buying_signal_evidence_urls", "retrieved_at",
        ]
        score_row = {
            "company_id": "C1", "company_name": "Example Hausverwaltung GmbH", "domain": "example.de",
            "source_url": "https://example.de/about", "service_fit": "Confirmed", "residential_weg": "Confirmed",
            "portfolio_size": "Unknown", "portfolio_potential": "Unknown", "berlin_relevance": "Confirmed",
            "structural_lead_fit": "80", "evidence_coverage": "100", "buying_signal": "Unknown",
            "signal_search_status": "Searched", "actionability": "Ready", "sales_priority": "Pursue",
            "lead_tier": "A", "evidence_urls": "https://example.de/about", "buying_signal_event_ids": "",
            "buying_signal_evidence_urls": "", "retrieved_at": "2026-11-09",
        }
        with (root / "data" / "scores.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=score_fields)
            writer.writeheader()
            writer.writerow(score_row)
        contact_fields = [
            "company_id", "company_name", "contact_name", "contact_role", "relevance", "contact_email",
            "email_source", "verification_status", "linkedin_url", "last_verified",
        ]
        with (root / "data" / "contacts.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=contact_fields)
            writer.writeheader()
            writer.writerow({
                "company_id": "C1", "company_name": "Example Hausverwaltung GmbH", "contact_name": "Anna Example",
                "contact_role": "Managing Director", "relevance": "Decision maker", "contact_email": "anna@example.de",
                "email_source": "https://example.de/team", "verification_status": "Verified", "linkedin_url": "Unknown",
                "last_verified": "2026-11-09",
            })
        company_fields = [
            "company_id", "company_name", "domain", "verified_company_domain", "city", "berlin_relevance",
            "resolution_status", "source_url", "retrieved_at", "evidence_level",
        ]
        with (root / "data" / "companies.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=company_fields)
            writer.writeheader()
            writer.writerow({
                "company_id": "C1", "company_name": "Example Hausverwaltung GmbH", "domain": "example.de",
                "verified_company_domain": "example.de", "city": "Berlin", "berlin_relevance": "Confirmed",
                "resolution_status": "Accepted", "source_url": "https://example.de/about",
                "retrieved_at": "2026-11-09", "evidence_level": "Primary",
            })
        with (root / "data" / "sources.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source_id", "source_url"])
            writer.writeheader()
            writer.writerow({"source_id": "source-C1", "source_url": "https://example.de/about"})
        (root / "data" / "events.json").write_text(json.dumps([{
            "event_id": "E1", "company_id": "C1", "event_type": "tender", "buyer": "Example Buyer",
            "title": "Example procurement", "publication_date": "2026-11-08", "deadline": "2026-12-01",
            "source_url": "https://ted.europa.eu/example", "source_kind": "procurement",
        }]), encoding="utf-8")
        with (root / "data" / "event_links.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["event_id", "company_id", "match_confidence"])
            writer.writeheader()
            writer.writerow({"event_id": "E1", "company_id": "C1", "match_confidence": "Verified"})
        shortlist = root / "shortlist.csv"
        shortlist.write_text(
            "company_id,company_name,domain,verified_company_domain,city,resolution_status,berlin_relevance\n"
            "C1,Example Hausverwaltung GmbH,example.de,example.de,Berlin,Accepted,Confirmed\n",
            encoding="utf-8",
        )
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        worker = root / "worker_stub.py"
        worker.write_text(
            """import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, SOURCE_SCRIPTS)
from lead_contract import candidate_claim_id, candidate_sha256
parser = argparse.ArgumentParser()
for name in ("profile", "run-id", "campaign-id", "lane", "company-id", "company-name", "trusted-domain", "location", "scope-version", "scope-hash"):
    parser.add_argument("--" + name)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
claims = []
def add_claim(claim_type, claim_value, **extra):
    claim = {"record_type": "EvidenceClaim", "company_id": args.company_id, "claim_type": claim_type, "claim_value": claim_value, "source_url": extra.pop("source_url", "https://example.de/about"), "source_domain": args.trusted_domain, "source_kind": extra.pop("source_kind", "official_site"), "evidence_excerpt": extra.pop("evidence_excerpt", "Official page evidence."), "retrieved_at": now, "account_relationship": "direct", "confidence": "high", "research_run_id": f"{args.run_id}:{args.lane}:{args.company_id}", "candidate_status": "Candidate", **extra}
    claim["candidate_claim_id"] = candidate_claim_id(claim)
    claim["candidate_sha256"] = candidate_sha256(claim)
    claims.append(claim)
if args.lane == "portfolio":
    add_claim("service_fit", "Confirmed")
    add_claim("residential_weg", "Confirmed")
    add_claim("berlin_relevance", "Confirmed", evidence_excerpt="Berlin residential property management services.")
elif args.lane == "contacts":
    add_claim("contact", "Anna Example", person_name="Anna Example", role="Managing Director", company_affiliation=args.company_name, email="anna@example.de", source_url="https://example.de/team", evidence_excerpt="Anna Example, Managing Director")
elif args.lane == "signals":
    add_claim("buying_signal", "Strong", source_kind="procurement", source_url="https://ted.europa.eu/example", published_at="2026-11-08", evidence_excerpt="Example procurement")
    add_claim("event", {"event_id": "E1", "event_type": "tender", "buyer": "Example Buyer", "title": "Example procurement", "publication_date": "2026-11-08", "deadline": "2026-12-01"}, source_kind="procurement", source_url="https://ted.europa.eu/example", published_at="2026-11-08", evidence_excerpt="Example procurement")
research_run = {"record_type": "ResearchRun", "run_id": f"{args.run_id}:{args.lane}:{args.company_id}", "campaign_id": args.campaign_id, "company_id": args.company_id, "company_name": args.company_name, "trusted_domain": args.trusted_domain, "location": args.location, "research_type": args.lane, "source": args.profile, "scope": f"{args.lane}:{args.company_id}", "status": "Completed", "started_at": now, "completed_at": now, "result_count": len(claims), "truncated": False, "provider_status": "Available", "adapter_capability": "live_research", "assurance_level": "source", "scope_version": args.scope_version, "scope_hash": args.scope_hash, "attempts": [{"attempt_id": f"{args.run_id}:{args.lane}:{args.company_id}:1", "query_or_source": "https://example.de/about", "status": "Completed", "truncated": False}]}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({"adapter_capability": "live_research", "research_run": research_run, "claims": claims}, sort_keys=True) + "\\n", encoding="utf-8")
""".replace("SOURCE_SCRIPTS", repr(str(scripts_dir))), encoding="utf-8")
        verifier = root / "verifier_stub.py"
        verifier.write_text(
            """import json, sys
from pathlib import Path
sys.path.insert(0, SOURCE_SCRIPTS)
import native_verifier
result = native_verifier.main()
if result:
    raise SystemExit(result)
output = Path(sys.argv[sys.argv.index("--output") + 1])
payload = json.loads(output.read_text(encoding="utf-8"))
payload["adapter_capability"] = "source_verification"
for decision in payload.get("decisions", []):
    decision["assurance_level"] = "source"
output.write_text(json.dumps(payload, sort_keys=True) + "\\n", encoding="utf-8")
""".replace("SOURCE_SCRIPTS", repr(str(scripts_dir))), encoding="utf-8")
        return campaign_path, shortlist, worker, verifier, root / "evidence" / "manifests" / "run.json"

    def _commit_fixture(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "E2E Test"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "committed E2E fixture"], cwd=root, check=True, capture_output=True)

    def test_production_mode_trace_is_hermetic_and_replayable(self):
        source_root = Path(__file__).resolve().parents[1]
        source_state = {
            path: (path.stat().st_mtime_ns, path.stat().st_size)
            for path in source_root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign_path, shortlist, worker, verifier, manifest_path = self._production_fixture(root)
            self._commit_fixture(root)
            input_paths = [root / relative_path for relative_path in json.loads(campaign_path.read_text(encoding="utf-8"))["input_bindings"].values()]
            create_run_manifest(root, manifest_path, "run-production", [*input_paths, shortlist], [], accepted_company_ids={"C1"}, campaign_config=campaign_path, require_clean=True)
            original_builder = __import__("orchestrate_enrichment")._native_command_builder
            def local_builder(item, output_path, config):
                command = original_builder(item, output_path, config)
                adapter = worker if item["lane"] != "verifier" else verifier
                prefix = ["--repo-root", str(root)] if item["lane"] == "verifier" else []
                return [command[0], str(adapter), *prefix, *command[1:]]
            publication_markers = []
            original_atomic_write = run_manifest.atomic_write
            def tracked_atomic_write(path, value):
                if Path(path).name == "run-production.publication.json":
                    publication_markers.append(Path(path))
                return original_atomic_write(path, value)
            with patch("orchestrate_enrichment._native_command_builder", side_effect=local_builder), patch("run_manifest.atomic_write", side_effect=tracked_atomic_write):
                result = run_pipeline(root, manifest_path, shortlist, campaign_config=campaign_path, worker_executable=sys.executable, worker_profile="local-stub", verifier_executable=sys.executable, verifier_profile="local-verifier")
            manifest = load(manifest_path)
            self.assertEqual(manifest["status"], "completed")
            self.assertTrue(manifest["barriers"]["published"])
            self.assertTrue((root / "output" / "run-production.xlsx").exists())
            for relative_path in (
                "evidence/action_lifecycle/run-production.jsonl", "evidence/candidate/run-production/claims.jsonl",
                "evidence/verifier/run-production/decisions.jsonl", "evidence/verified/run-production/claims.jsonl",
                "data/processed/run-production/scores.csv", "data/processed/run-production/priority.csv",
                "evidence/reports/run-production/qa.csv", "evidence/reports/run-production/qa.md",
            ):
                self.assertTrue((root / relative_path).exists(), relative_path)
            self.assertEqual(publication_markers, [root / "output" / "run-production.publication.json"])
            self.assertFalse((root / "output" / "run-production.publication.json").exists())
            self.assertEqual(manifest["outputs"]["workbook"]["sha256"], file_sha256(Path(result["workbook"])))
            self.assertEqual(manifest["delivery"]["delivered_count"], 1)
            self.assertEqual(manifest["delivery"]["target_count"], 1)
            lifecycle = replay_lifecycle(root, "run-production")
            self.assertEqual(lifecycle["action_count"], 4)
            self.assertEqual({action["status"] for action in lifecycle["actions"]}, {"Completed"})
            self.assertEqual(lifecycle["budget_settled"], 4)
            restart = reconstruct_finalization_readiness(root, manifest_path, "strict")
            self.assertTrue(restart["ready"], restart["errors"])
            self.assertEqual(load(manifest_path)["status"], "completed")
        self.assertEqual(source_state, {
            path: (path.stat().st_mtime_ns, path.stat().st_size)
            for path in source_state
            if path.exists()
        })

    def test_production_boundary_rejects_tampering_and_unresolved_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            workbook = root / "staging.xlsx"
            workbook.write_bytes(b"workbook")
            atomic_write(manifest_path, {
                "run_id": "run-failure", "execution_mode": "production", "head_sha": "0" * 40,
                "campaign": {"target_count": 1}, "accepted_company_ids": ["C1"],
                "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "complete"},
                "delivery": {"status": "completed", "delivery_policy": "strict", "target_count": 1, "delivered_count": 1, "shortfall": 0},
                "outputs": {"workbook": {"path": "staging.xlsx", "sha256": "0" * 64}},
            })
            readiness = reconstruct_finalization_readiness(root, manifest_path, "strict")
            self.assertFalse(readiness["ready"])
            self.assertTrue(any("lifecycle" in error or "verified evidence" in error or "workbook artifact hash" in error for error in readiness["errors"]))
            eligible, policy_errors = finalization_eligibility({
                "campaign": {"target_count": 1},
                "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")},
                "coverage": {"status": "partial"},
                "delivery": {"status": "blocked", "delivery_policy": "strict", "target_count": 1, "delivered_count": 0, "shortfall": 1},
            }, "strict")
            self.assertFalse(eligible)
            self.assertTrue(any("complete policy coverage" in error for error in policy_errors))
            self.assertTrue(any("complete delivery" in error for error in policy_errors))
            with self.assertRaisesRegex(ValueError, "path must remain under repository root"):
                invoke({"action": "check_finalization", "payload": {"run_id": "run-failure", "manifest_path": "../outside.json", "delivery_policy": "strict"}}, root)
            with self.assertRaisesRegex(ValueError, "direct publish_staged_output"):
                invoke({"action": "publish_staged_output", "payload": {}}, root)
    def _trace(self, root: Path, run_id: str, *, strict: bool, stop_early: bool = False) -> dict[str, object]:
        manifest_path = root / "evidence" / "manifests" / f"native_handoff_{run_id}.json"
        manifest = {
            "record_type": "RunManifest", "run_id": run_id, "execution_mode": "fixture", "head_sha": "0" * 40, "git_revision": "0" * 40,
            "delivery_policy": "strict" if strict else "personal",
            "budget_limit": 1,
            "barriers": {"research": not stop_early, "verifier": not stop_early, "verified_evidence": not stop_early, "projection": not stop_early, "ranking": not stop_early, "readiness": not stop_early},
            "coverage": {"status": "complete" if strict and not stop_early else "partial"},
            "delivery": {
                "status": "completed" if not stop_early else "partial",
                "delivery_policy": "strict" if strict else "personal",
                "target_count": 1,
                "delivered_count": 1 if not stop_early else 0,
                "shortfall": 0 if not stop_early else 1,
            },
            "outputs": {},
        }
        atomic_write(manifest_path, manifest)
        goal = {"goal_id": run_id, "objective": "find Berlin property-management leads", "delivery_policy": "strict" if strict else "personal"}
        invoke({"action": "validate_goal", "payload": goal}, root)
        result_payload = {"claims": 1}
        result_hash = hashlib.sha256(json.dumps(result_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        action = {
            "run_id": run_id, "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1", "action_type": "signals",
            "scope": "signals:C1", "contract_version": "1", "strategy_version": "1", "profile_version": "signal-v1",
            "idempotency_key": f"{run_id}/action-1/attempt-1", "request_hash": "", "budget_units": 1,
        }
        action["request_hash"] = canonical_request_hash(action)
        action["manifest_path"] = manifest_path.relative_to(root).as_posix()
        invoke({"action": "admit_action", "payload": action}, root)
        invoke({"action": "validate_result", "payload": {"run_id": run_id, "action_id": "action-1", "attempt_id": "attempt-1", "company_id": "C1", "status": "Partial" if stop_early else "Completed", "result_hash": result_hash, "result": result_payload}}, root)
        invoke({"action": "record_receipt", "payload": {key: value for key, value in {**action, "result_hash": result_hash, "terminal_status": "Partial" if stop_early else "Completed", "budget_requested": 1, "budget_settled": 1, "created_at": datetime.now(timezone.utc).isoformat(), "coverage_delta": {"signals": 0 if stop_early else 1}}.items() if key not in {"budget_units", "manifest_path"}}}, root)
        if not stop_early:
            claims = [_claim("c1", "C1", "service_fit", "Confirmed"), _claim("c2", "C1", "event", {"event_id": "E1", "event_type": "tender", "event_date": "2026-11-01"})]
            thesis = {"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "structural_fit": 35, "confidence": "high", "why_this_account": "Residential property management fit", "why_now": "Recent procurement activity", "problem_hypothesis": "Operations may need support", "strongest_claim_ids": ["c2"], "semantic_review_ids": ["a1"], "access_summary": "Contact path requires research", "research_gap_impact": "Could change outreach timing", "recommended_action": "research contacts", "hypotheses": [{"company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "hypothesis_type": "opportunity", "statement": "Observed procurement activity may create a near-term opening", "supporting_claim_ids": ["c2"], "confidence": "medium"}]}
            review = {"assertion_id": "a1", "company_id": "C1", "offer_id": "offer-1", "offer_version": "2026-11-09", "reviewed_claim_ids": ["c2"], "offer_criterion": "relevant_triggers", "entailment": "supported", "offer_relevance": "relevant", "temporal_relevance": "current", "contradiction_result": "none", "decision": "approved", "reason_codes": ["supported"], "reviewer_id": "semantic-reviewer"}
            projection = project_account_intelligence(claims, thesis, semantic_reviews=[review])
            self.assertEqual(projection["timeline"][0]["event_identity"], "C1:E1")
            inputs = root / "inputs"
            inputs.mkdir(parents=True, exist_ok=True)
            (inputs / "companies.csv").write_text("company_id,company_name\nC1,Example GmbH\n", encoding="utf-8")
            score_row = "company_id,company_name,source_url,retrieved_at,service_fit,residential_weg,berlin_relevance,structural_lead_fit,evidence_coverage,buying_signal,signal_search_status,actionability,sales_priority,lead_tier,evidence_urls\nC1,Example GmbH,https://example.com,2026-11-09T00:00:00+00:00,Confirmed,Confirmed,Confirmed,80,90,None found,Searched,Ready,Pursue,A,https://example.com\n"
            (inputs / "scores.csv").write_text(score_row, encoding="utf-8")
            (inputs / "priority.csv").write_text(score_row, encoding="utf-8")
            (inputs / "contacts.csv").write_text("company_id,contact_name,contact_role,contact_email,email_source,verification_status,last_verified\nC1,Unknown,Unknown,Unknown,Unknown,Unknown,Unknown\n", encoding="utf-8")
            (inputs / "sources.csv").write_text("company_id,source_url\nC1,https://example.com\n", encoding="utf-8")
            staged = root / "output" / f"{run_id}.staging.xlsx"
            build_report = root / "output" / f"{run_id}.build.json"
            exported = invoke({"action": "export_workbook", "payload": {
                "companies": "inputs/companies.csv", "scores": "inputs/scores.csv", "priority": "inputs/priority.csv",
                "contacts": "inputs/contacts.csv", "sources": "inputs/sources.csv", "output": staged.relative_to(root).as_posix(),
                "build_report": build_report.relative_to(root).as_posix(),
            }}, root)
            self.assertEqual(exported["workbook"]["sha256"], file_sha256(staged))
            workbook = load_workbook(staged, read_only=True)
            try:
                self.assertEqual(workbook.sheetnames, ["01_All_Leads", "02_Qualification", "03_Priority_Leads", "04_Contacts", "05_Methodology_Sources"])
            finally:
                workbook.close()
            manifest["barriers"] = {key: True for key in manifest["barriers"]}
            manifest["outputs"] = {"workbook": {"path": staged.relative_to(root).as_posix(), "sha256": file_sha256(staged)}}
            atomic_write(manifest_path, manifest)
            checked = invoke({"action": "check_finalization", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "delivery_policy": "strict" if strict else "personal"}}, root)
            self.assertTrue(checked["eligible"])
            invoke({"action": "finalize_run", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "staging_path": staged.relative_to(root).as_posix(), "final_path": f"output/{run_id}.xlsx", "status": "complete", "delivery_policy": "strict" if strict else "personal"}}, root)
            self.assertEqual(load(manifest_path)["status"], "complete")
        else:
            checked = invoke({"action": "check_finalization", "payload": {"run_id": run_id, "manifest_path": manifest_path.relative_to(root).as_posix(), "delivery_policy": "personal"}}, root)
            self.assertFalse(checked["eligible"])
        return {"manifest": manifest_path, "replay": replay_run(root, run_id)}

    def test_two_valid_traces_and_early_stop_are_replayable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._trace(root, "run-1", strict=True)
            second = self._trace(root, "run-2", strict=False)
            stopped = self._trace(root, "run-3", strict=False, stop_early=True)
            self.assertTrue((root / "output" / "run-1.xlsx").exists())
            self.assertTrue((root / "output" / "run-2.xlsx").exists())
            self.assertFalse((root / "output" / "run-3.xlsx").exists())
            self.assertEqual(first["replay"]["budget_settled"], 1)
            self.assertEqual(second["replay"]["coverage"], {"signals": 1})
            self.assertEqual(stopped["replay"]["coverage"], {"signals": 0})
            self.assertTrue(load(first["manifest"])["barriers"]["published"])


if __name__ == "__main__":
    unittest.main()
