from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from orchestrate_enrichment import _native_command_builder, build_verifier_queue, complete_company_ids, create_run_manifest, validate_final_priority_rows, validate_lane_output, write_lane_queue
from run_manifest import update


class OrchestrationTests(unittest.TestCase):
    def test_verifier_queue_is_limited_to_dispatched_scope(self):
        admitted_items = [
            {"company_id": f"R{index:02d}", "lane": "signals", "scope": f"signals:R{index:02d}", "scope_hash": f"hash-{index:02d}"}
            for index in range(30)
        ]
        claims_by_company = {item["company_id"]: [] for item in admitted_items}
        queue, dispatched_ids = build_verifier_queue(
            accepted_ids={f"R{index:02d}" for index in range(35)},
            admitted_items=admitted_items,
            claims_by_company=claims_by_company,
            claims_dir=Path("claims"),
            run_id="run-1",
            delivery_policy="personal",
        )
        self.assertEqual([item["company_id"] for item in queue], [f"R{index:02d}" for index in range(30)])
        self.assertEqual(dispatched_ids, {f"R{index:02d}" for index in range(30)})
        self.assertTrue(all(item["lane"] == "verifier" for item in queue))
        self.assertTrue(all(item["scope"] == f"verifier:{item['company_id']}" for item in queue))

    def test_verifier_queue_preserves_source_scope_as_verifier_scope(self):
        item = {"company_id": "C1", "lane": "contacts", "scope": "contacts:C1", "scope_version": "v1", "scope_hash": "a" * 64}
        queue, _ = build_verifier_queue(
            accepted_ids={"C1"},
            admitted_items=[item],
            claims_by_company={"C1": []},
            claims_dir=Path("claims"),
            run_id="run-1",
            delivery_policy="personal",
        )
        self.assertEqual(queue[0]["lane"], "verifier")
        self.assertEqual(queue[0]["scope"], "verifier:C1")
        self.assertEqual(queue[0]["scope_version"], "v1")
        self.assertEqual(queue[0]["scope_hash"], "a" * 64)

    def test_unavailable_research_is_not_delivered(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "signals-C1.json"
            output.write_text(json.dumps({"research_run": {"status": "Not searched", "provider_status": "Unavailable"}, "claims": []}), encoding="utf-8")
            results = {"signals": [{"company_id": "C1", "status": "succeeded", "output_path": output.as_posix()}], "portfolio": [{"company_id": "C1", "status": "succeeded", "output_path": output.as_posix()}]}
            queues = {"signals": [{"company_id": "C1"}], "portfolio": [{"company_id": "C1"}]}
            self.assertEqual(complete_company_ids(results, queues), set())

    def test_queue_is_deterministic_and_scoped_to_shortlist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain\nB,Bravo,bravo.de\nA,Alpha,alpha.de\n", encoding="utf-8")
            queue = root / "queue.jsonl"
            rows = write_lane_queue(shortlist, queue, "signals", "run-1")
            self.assertEqual([row["company_id"] for row in rows], ["A", "B"])
            self.assertEqual(json.loads(queue.read_text(encoding="utf-8").splitlines()[0])["run_id"], "run-1")

    def test_production_queue_rejects_raw_domain_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain,city,resolution_status\nA,Alpha,alpha.de,Berlin,Accepted\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "trusted domain"):
                write_lane_queue(shortlist, root / "queue.jsonl", "signals", "run-1", campaign_id="campaign-1", accepted_company_ids={"A"}, require_qualification=True)

    def test_production_queue_uses_canonical_company_binding_for_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain\nA,Alpha,alpha.de\n", encoding="utf-8")
            company_rows = {
                "A": {
                    "company_id": "A",
                    "company_name": "Alpha GmbH",
                    "verified_company_domain": "official.example",
                    "city": "Berlin",
                    "berlin_relevance": "Confirmed",
                    "resolution_status": "Accepted",
                }
            }
            queue = write_lane_queue(
                shortlist,
                root / "queue.jsonl",
                "signals",
                "run-1",
                campaign_id="campaign-1",
                accepted_company_ids={"A"},
                require_qualification=True,
                company_rows=company_rows,
                required_location_evidence="Confirmed",
            )
            self.assertEqual(queue[0]["company_name"], "Alpha GmbH")
            self.assertEqual(queue[0]["trusted_domain"], "official.example")
            self.assertEqual(queue[0]["location"], "Berlin")

    def test_production_queue_rejects_probable_location_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain,resolution_status\nA,Alpha,alpha.de,Accepted\n", encoding="utf-8")
            company_rows = {
                "A": {
                    "company_id": "A",
                    "company_name": "Alpha",
                    "verified_company_domain": "official.example",
                    "city": "Berlin",
                    "berlin_relevance": "Probable",
                    "resolution_status": "Accepted",
                }
            }
            with self.assertRaisesRegex(ValueError, "confirmed location evidence"):
                write_lane_queue(
                    shortlist,
                    root / "queue.jsonl",
                    "signals",
                    "run-1",
                    campaign_id="campaign-1",
                    accepted_company_ids={"A"},
                    require_qualification=True,
                    company_rows=company_rows,
                    required_location_evidence="Confirmed",
                )

    def test_production_queue_rejects_missing_canonical_company_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain,verified_company_domain,city,berlin_relevance,resolution_status\nA,Alpha,fabricated.example,fabricated.example,Berlin,Confirmed,Accepted\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "canonical company binding"):
                write_lane_queue(
                    shortlist,
                    root / "queue.jsonl",
                    "signals",
                    "run-1",
                    campaign_id="campaign-1",
                    accepted_company_ids={"A"},
                    require_qualification=True,
                    company_rows={},
                    required_location_evidence="Confirmed",
                )

    def test_production_queue_rejects_incomplete_canonical_company_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain,verified_company_domain,city,berlin_relevance,resolution_status\nA,Alpha,fabricated.example,fabricated.example,Berlin,Confirmed,Accepted\n", encoding="utf-8")
            company_rows = {"A": {"company_id": "A", "company_name": "Alpha", "resolution_status": "Accepted"}}
            with self.assertRaisesRegex(ValueError, "trusted domain"):
                write_lane_queue(
                    shortlist,
                    root / "queue.jsonl",
                    "signals",
                    "run-1",
                    campaign_id="campaign-1",
                    accepted_company_ids={"A"},
                    require_qualification=True,
                    company_rows=company_rows,
                    required_location_evidence="Confirmed",
                )

    def test_queue_contains_stable_admitted_scope_and_worker_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain,verified_company_domain,city,resolution_status\nA,Alpha,alpha.de,official.example,Berlin,Accepted\n", encoding="utf-8")
            queue = write_lane_queue(shortlist, root / "queue.jsonl", "signals", "run-1", campaign_id="campaign-1", accepted_company_ids={"A"}, require_qualification=True)
            item = queue[0]
            self.assertEqual(item["campaign_id"], "campaign-1")
            self.assertEqual(item["trusted_domain"], "official.example")
            self.assertTrue(item["scope_hash"])
            command = _native_command_builder(item, root / "output.json", type("Config", (), {"executable": "python", "adapter_args": (), "profile": "worker"})())
            self.assertIn("--trusted-domain", command)
            self.assertIn("official.example", command)
            self.assertIn("--scope-hash", command)

    def test_manifest_requires_clean_committed_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("orchestrate_enrichment.git_output", side_effect=["a" * 40, " M dirty.py\n"]):
                with self.assertRaises(ValueError):
                    create_run_manifest(root, root / "manifest.json", "run-1", [], [], require_clean=True)

    def test_manifest_update_resolves_nested_paths_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            manifest_path = root / "evidence" / "manifests" / "active_run.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps({"run_id": "run-1", "head_sha": "a" * 40, "inputs": {}, "outputs": {}}), encoding="utf-8")
            artifact = root / "data" / "result.csv"
            artifact.parent.mkdir()
            artifact.write_text("company_id\nC1\n", encoding="utf-8")
            update(manifest_path, root, outputs={"result": artifact}, status="ready")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_id"], "run-1")
            self.assertEqual(manifest["outputs"]["result"]["path"], "data/result.csv")
            self.assertEqual(manifest["status"], "ready")

    def test_lane_output_requires_exact_queue_coverage(self):
        queue = [{"company_id": "A"}, {"company_id": "B"}]
        with self.assertRaisesRegex(ValueError, "missing queued companies"):
            validate_lane_output([{"run_id": "run-1", "lane": "signals", "company_id": "A", "status": "succeeded"}], queue, "run-1", "signals")

    def test_final_priority_rows_require_exact_admitted_membership(self):
        accepted = {f"C{index:02d}" for index in range(30)}
        rows = [{"company_id": company_id} for company_id in sorted(accepted)]
        validate_final_priority_rows(rows, accepted)
        with self.assertRaisesRegex(ValueError, "exactly the admitted 30"):
            validate_final_priority_rows(rows[:-1], accepted)


if __name__ == "__main__":
    unittest.main()
