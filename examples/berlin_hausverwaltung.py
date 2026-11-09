"""Thin reference entry point for a Codex-native account-intelligence handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from typed_contracts import Goal


def load_goal(path: Path) -> Goal:
    return Goal.model_validate(json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a lead-generation goal for Codex-native handoff")
    parser.add_argument("--goal", type=Path, required=True)
    args = parser.parse_args()
    goal = load_goal(args.goal)
    print(json.dumps(goal.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
