from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_workbook import main as build_workbook
from qa_leads import main as qa_leads
from run_manifest import atomic_write, file_sha256, publication_marker_path, recover_publication, validate_manifest_revision


class ArtifactManifestSideEffectTests(unittest.TestCase):
    def test_publication_recovery_rebinds_manifest_after_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            final = root / "output" / "run-1.xlsx"
            final.parent.mkdir(parents=True)
            final.write_bytes(b"published workbook")
            manifest_path.write_text(json.dumps({"run_id": "run-1", "head_sha": "a" * 40, "status": "ready_for_validation", "delivery_policy": "personal", "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")}, "coverage": {"status": "partial"}, "delivery": {"status": "partial", "delivery_policy": "personal", "target_count": 1, "delivered_count": 0, "shortfall": 1}, "outputs": {}, "inputs": {}, "supporting_inputs": {}}), encoding="utf-8")
            atomic_write(publication_marker_path(root, "run-1"), {"run_id": "run-1", "head_sha": "a" * 40, "status": "complete", "delivery_policy": "personal", "final_path": "output/run-1.xlsx", "staging_path": "output/run-1.staging.xlsx", "staging_sha256": file_sha256(final)})
            recover_publication(root, manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["outputs"]["workbook"]["path"], "output/run-1.xlsx")
            self.assertFalse(publication_marker_path(root, "run-1").exists())

    def test_publication_recovery_finishes_replacement_when_old_final_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            final = root / "output" / "run-1.xlsx"
            staging = root / "output" / "run-1.staging.xlsx"
            final.parent.mkdir(parents=True)
            final.write_bytes(b"old workbook")
            staging.write_bytes(b"new workbook")
            manifest_path.write_text(json.dumps({"run_id": "run-1", "head_sha": "a" * 40, "status": "ready_for_validation", "delivery_policy": "personal", "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")}, "coverage": {"status": "partial"}, "delivery": {"status": "partial", "delivery_policy": "personal", "target_count": 1, "delivered_count": 0, "shortfall": 1}, "outputs": {}, "inputs": {}, "supporting_inputs": {}}), encoding="utf-8")
            atomic_write(publication_marker_path(root, "run-1"), {"run_id": "run-1", "head_sha": "a" * 40, "status": "complete", "delivery_policy": "personal", "final_path": "output/run-1.xlsx", "staging_path": "output/run-1.staging.xlsx", "staging_sha256": file_sha256(staging)})
            recover_publication(root, manifest_path)
            self.assertEqual(final.read_bytes(), b"new workbook")
            self.assertFalse(staging.exists())

    def test_publication_recovery_preserves_outputs_when_revision_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            final = root / "output" / "run-1.xlsx"
            staging = root / "output" / "run-1.staging.xlsx"
            final.parent.mkdir(parents=True)
            final.write_bytes(b"old workbook")
            staging.write_bytes(b"new workbook")
            manifest_path.write_text(json.dumps({"run_id": "run-1", "head_sha": "a" * 40, "git_revision": "a" * 40, "status": "ready_for_validation", "delivery_policy": "personal", "barriers": {key: True for key in ("research", "verifier", "verified_evidence", "projection", "ranking", "readiness")}, "coverage": {"status": "partial"}, "delivery": {"status": "partial", "delivery_policy": "personal", "target_count": 1, "delivered_count": 0, "shortfall": 1}, "outputs": {}, "inputs": {}, "supporting_inputs": {}}), encoding="utf-8")
            atomic_write(publication_marker_path(root, "run-1"), {"run_id": "run-1", "head_sha": "a" * 40, "status": "complete", "delivery_policy": "personal", "head_sha": "a" * 40, "final_path": "output/run-1.xlsx", "staging_path": "output/run-1.staging.xlsx", "staging_sha256": file_sha256(staging)})
            with patch("run_manifest.git_revision", return_value="b" * 40):
                with self.assertRaisesRegex(ValueError, "revision validation"):
                    recover_publication(root, manifest_path)
            self.assertEqual(final.read_bytes(), b"old workbook")
            self.assertEqual(staging.read_bytes(), b"new workbook")
            self.assertTrue(publication_marker_path(root, "run-1").exists())

    def test_stale_reachable_revision_is_rejected_against_current_checkout(self):
        root = Path(__file__).resolve().parents[1]
        revisions = subprocess.run(["git", "rev-list", "--max-count=2", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(len(revisions), 2)
        errors = validate_manifest_revision(root, {"git_revision": revisions[1], "head_sha": revisions[1]})
        self.assertTrue(any("expected current HEAD" in error and revisions[1] in error for error in errors))

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

    def test_qa_rejects_unbound_website_evidence_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "workbook.xlsx"
            shutil.copyfile(Path("output/berlin-hausverwaltung-leads_2026-11-09.xlsx"), workbook)
            manifest_path = Path("evidence/run_manifest_test.json")
            manifest = json.loads(Path("evidence/run_manifest_2026-11-09.json").read_text(encoding="utf-8"))
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            alternate = root / "alternate-website-evidence.jsonl"
            alternate.write_text("\n", encoding="utf-8")
            qa_report = root / "qa-report.md"
            qa_sample = root / "qa-sample.csv"
            qa_argv = [
                "qa_leads.py",
                "--workbook", str(workbook),
                "--schema", str(Path("config/lead_generation_schema.json")),
                "--evidence-dir", str(Path("evidence")),
                "--website-evidence", str(alternate),
                "--report", str(qa_report),
                "--sample-output", str(qa_sample),
                "--run-manifest", str(manifest_path),
            ]
            try:
                with patch.object(sys, "argv", qa_argv):
                    self.assertEqual(qa_leads(), 1)
                self.assertIn("website evidence override does not match run manifest binding", qa_report.read_text(encoding="utf-8"))
            finally:
                manifest_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
