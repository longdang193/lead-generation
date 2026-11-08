from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_workbook import main as build_workbook
from qa_leads import main as qa_leads


class ArtifactManifestSideEffectTests(unittest.TestCase):
    def test_workbook_build_without_manifest_does_not_mutate_repository_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            companies = root / "companies.csv"
            scores = root / "scores.csv"
            priority = root / "priority.csv"
            contacts = root / "contacts.csv"
            sources = root / "sources.csv"
            for path, header in (
                (companies, "company_id,company_name\n"),
                (scores, "company_id,lead_tier\n"),
                (priority, "company_id,lead_tier\n"),
                (contacts, "company_id,contact_name\n"),
                (sources, "source_id,source_url\n"),
            ):
                path.write_text(header, encoding="utf-8")
            output = root / "workbook.xlsx"
            report = root / "build-report.json"
            manifest = Path("evidence/run_manifest_2026-11-09.json")
            before = hashlib.sha256(manifest.read_bytes()).hexdigest()
            argv = [
                "build_workbook.py",
                "--companies", str(companies),
                "--scores", str(scores),
                "--priority", str(priority),
                "--contacts", str(contacts),
                "--sources", str(sources),
                "--output", str(output),
                "--build-report", str(report),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(build_workbook(), 0)
            after = hashlib.sha256(manifest.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertTrue(output.exists())
            self.assertTrue(report.exists())

    def test_qa_without_manifest_does_not_require_or_mutate_repository_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "workbook.xlsx"
            shutil.copyfile(Path("output/berlin-hausverwaltung-leads_2026-11-09.xlsx"), workbook)
            qa_report = root / "qa-report.md"
            qa_sample = root / "qa-sample.csv"
            qa_argv = [
                "qa_leads.py",
                "--workbook", str(workbook),
                "--schema", str(Path("config/lead_generation_schema.json")),
                "--evidence-dir", str(Path("evidence")),
                "--report", str(qa_report),
                "--sample-output", str(qa_sample),
            ]
            with patch.object(sys, "argv", qa_argv):
                self.assertEqual(qa_leads(), 1)
            self.assertTrue(qa_report.exists())
            self.assertTrue(qa_sample.exists())
            self.assertNotIn("run manifest", qa_report.read_text(encoding="utf-8"))

    def test_qa_rejects_tampered_supporting_source_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "workbook.xlsx"
            shutil.copyfile(Path("output/berlin-hausverwaltung-leads_2026-11-09.xlsx"), workbook)
            manifest_path = Path("evidence/run_manifest_test.json")
            manifest = json.loads(Path("evidence/run_manifest_2026-11-09.json").read_text(encoding="utf-8"))
            manifest["supporting_inputs"]["schema"]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            qa_report = root / "qa-report.md"
            qa_sample = root / "qa-sample.csv"
            qa_argv = [
                "qa_leads.py",
                "--workbook", str(workbook),
                "--schema", str(Path("config/lead_generation_schema.json")),
                "--evidence-dir", str(Path("evidence")),
                "--report", str(qa_report),
                "--sample-output", str(qa_sample),
                "--run-manifest", str(manifest_path),
            ]
            try:
                with patch.object(sys, "argv", qa_argv):
                    self.assertEqual(qa_leads(), 1)
                self.assertIn("manifest hash mismatch: supporting_inputs.schema", qa_report.read_text(encoding="utf-8"))
            finally:
                manifest_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
