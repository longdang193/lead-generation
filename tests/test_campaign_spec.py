from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from campaign_spec import load_campaign_spec
from orchestrate_enrichment import create_run_manifest, verify_manifest


class CampaignSpecTests(unittest.TestCase):
    def write_spec(self, root: Path, value: dict[str, object], name: str = "campaign.json") -> Path:
        path = root / "config" / "campaigns" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def valid_spec(self) -> dict[str, object]:
        return {
            "campaign_id": "test-campaign",
            "version": "2026-11-08",
            "target_count": 5,
            "qualification": {"resolution_status": "Accepted", "city": "Berlin"},
            "input_bindings": {"qualification": "data/qualification.jsonl"},
            "lanes": ["signals", "portfolio"],
            "adapter_policy": {"verification_mode": "source_verification"},
            "delivery_policy": "strict",
        }

    def test_normalization_and_hash_are_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_spec(root, self.valid_spec())
            first = load_campaign_spec(root, path)
            path.write_text(json.dumps({"delivery_policy": "strict", **self.valid_spec()}, separators=(",", ":")), encoding="utf-8")
            second = load_campaign_spec(root, path)
            self.assertEqual(first.normalized_json, second.normalized_json)
            self.assertEqual(first.sha256, second.sha256)

    def test_campaign_path_must_remain_under_repository_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / "outside-campaign.json"
            outside.write_text(json.dumps(self.valid_spec()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repository root"):
                load_campaign_spec(root, outside)

    def test_incomplete_spec_fails_before_manifest_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_spec(root, {"campaign_id": "missing-fields"})
            with self.assertRaisesRegex(ValueError, "required campaign fields"):
                load_campaign_spec(root, path)

    def test_manifest_records_and_verifies_campaign_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_spec(root, self.valid_spec())
            manifest_path = root / "evidence" / "manifests" / "run.json"
            with patch("orchestrate_enrichment.git_output", side_effect=["a" * 40, "", "main"]):
                manifest = create_run_manifest(root, manifest_path, "run-1", [], [], campaign_config=path, require_clean=True)
            self.assertEqual(manifest["campaign"]["campaign_id"], "test-campaign")
            self.assertEqual(manifest["campaign"]["version"], "2026-11-08")
            self.assertEqual(manifest["campaign"]["sha256"], load_campaign_spec(root, path).sha256)
            self.assertEqual(verify_manifest(manifest_path, root), [])
            path.write_text(json.dumps({**self.valid_spec(), "target_count": 6}), encoding="utf-8")
            self.assertTrue(any("campaign hash mismatch" in error for error in verify_manifest(manifest_path, root)))

    def test_manifest_lifecycle_allows_runtime_artifacts_in_real_git_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign_path = self.write_spec(root, self.valid_spec())
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=root, check=True)
            subprocess.run(["git", "add", str(campaign_path.relative_to(root))], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            manifest_path = root / "evidence" / "manifests" / "run.json"

            create_run_manifest(root, manifest_path, "run-1", [], [], campaign_config=campaign_path, require_clean=True)

            for path in (root / "evidence" / "fixture" / "run-1" / "qualification.jsonl", root / "output" / "run-1.xlsx"):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("runtime\n", encoding="utf-8")

            self.assertEqual(verify_manifest(manifest_path, root), [])
            dirty_source = root / "scripts" / "dirty.py"
            dirty_source.parent.mkdir()
            dirty_source.write_text("changed = True\n", encoding="utf-8")
            self.assertIn("implementation worktree is dirty", verify_manifest(manifest_path, root))


if __name__ == "__main__":
    unittest.main()
