from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from orchestrate_enrichment import create_run_manifest, write_lane_queue


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


if __name__ == "__main__":
    unittest.main()
