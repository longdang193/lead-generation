from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from orchestrate_enrichment import create_run_manifest, validate_final_priority_rows, validate_lane_output, write_lane_queue
from run_manifest import update


class OrchestrationTests(unittest.TestCase):
    def test_queue_is_deterministic_and_scoped_to_shortlist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shortlist = root / "shortlist.csv"
            shortlist.write_text("company_id,company_name,domain\nB,Bravo,bravo.de\nA,Alpha,alpha.de\n", encoding="utf-8")
            queue = root / "queue.jsonl"
            rows = write_lane_queue(shortlist, queue, "signals", "run-1")
            self.assertEqual([row["company_id"] for row in rows], ["A", "B"])
            self.assertEqual(json.loads(queue.read_text(encoding="utf-8").splitlines()[0])["run_id"], "run-1")

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
