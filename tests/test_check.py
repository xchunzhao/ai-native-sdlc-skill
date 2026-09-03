from __future__ import annotations

import importlib.util
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "ai-native-sdlc" / "scripts" / "check.py"
SPEC = importlib.util.spec_from_file_location("ai_native_sdlc_check", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "skills" / "ai-native-sdlc" / "schemas" / "artifact.schema.json").read_text())


def intent(status: str = "draft", approval: str = "") -> str:
    return f"""---
artifact: intent
feature: sample-feature
author: owner
status: {status}
created: 2026-09-03
risk: low
reviewers: []
{approval}---

# Intent — Sample

## Problem

Users cannot complete the sample flow.

## Proposed outcome

Users complete the flow successfully.

## Affected users and systems

Customers and the sample service.

## Constraints

No new external dependency.

## Open questions

- Which rollout cohort goes first?
"""


def spec() -> str:
    return """---
artifact: spec
feature: sample-feature
author: agent
status: draft
created: 2026-09-03
intent_ref: aaaaaaa
risk: low
reviewers: []
accepted_by:
accepted_at:
---

# Spec — Sample

## Requirements & design spec

The flow returns a successful result.

## Integration with existing code

Extend the sample service.

## Policy compliance

No policy surface changes.

## Areas of concern

No concerns identified.
"""


class ArtifactCheckerTests(unittest.TestCase):
    def test_valid_draft_intent_passes_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            feature = Path(directory) / "sample-feature"
            feature.mkdir()
            path = feature / "intent.md"
            path.write_text(intent(), encoding="utf-8")
            _, errors = checker.validate_artifact(path, SCHEMA)
            self.assertEqual([], errors)
            artifacts = {"intent": (path, checker.parse_frontmatter(path.read_text())[0])}
            self.assertEqual([], checker.validate_chain(feature, artifacts, None, True))

    def test_changed_accepted_intent_makes_spec_reference_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            feature = root / "docs" / "sdlc" / "sample-feature"
            feature.mkdir(parents=True)
            intent_path = feature / "intent.md"
            intent_path.write_text(
                intent(
                    status="accepted",
                    approval="accepted_by: product-owner\naccepted_at: 2026-09-03T12:00:00Z\n",
                ),
                encoding="utf-8",
            )
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"],
                ["git", "add", "."],
                ["git", "commit", "-qm", "accept intent"],
            ):
                subprocess.run(command, cwd=root, check=True)
            accepted = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, text=True, capture_output=True
            ).stdout.strip()
            spec_path = feature / "spec.md"
            spec_path.write_text(spec().replace("aaaaaaa", accepted), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "draft spec"], cwd=root, check=True)
            intent_path.write_text(intent_path.read_text().replace("Users cannot", "Customers cannot"), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "change accepted intent"], cwd=root, check=True)

            artifacts = {
                "intent": (intent_path, checker.parse_frontmatter(intent_path.read_text())[0]),
                "spec": (spec_path, checker.parse_frontmatter(spec_path.read_text())[0]),
            }
            errors = checker.validate_chain(feature, artifacts, root, False)
            self.assertIn("`intent_ref` is stale", "\n".join(errors))


    def test_accepted_artifact_requires_approval_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            feature = Path(directory) / "sample-feature"
            feature.mkdir()
            path = feature / "intent.md"
            path.write_text(intent(status="accepted"), encoding="utf-8")
            _, errors = checker.validate_artifact(path, SCHEMA)
            joined = "\n".join(errors)
            self.assertIn("requires `accepted_by`", joined)
            self.assertIn("requires ISO datetime `accepted_at`", joined)

    def test_spec_cannot_exist_before_intent_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            feature = Path(directory) / "sample-feature"
            feature.mkdir()
            intent_path = feature / "intent.md"
            spec_path = feature / "spec.md"
            intent_path.write_text(intent(), encoding="utf-8")
            spec_path.write_text(spec(), encoding="utf-8")
            intent_data = checker.parse_frontmatter(intent_path.read_text())[0]
            spec_data = checker.parse_frontmatter(spec_path.read_text())[0]
            errors = checker.validate_chain(
                feature,
                {"intent": (intent_path, intent_data), "spec": (spec_path, spec_data)},
                None,
                True,
            )
            self.assertIn("requires `intent` status `accepted`", "\n".join(errors))

    def test_high_risk_requires_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            feature = Path(directory) / "sample-feature"
            feature.mkdir()
            path = feature / "intent.md"
            path.write_text(intent().replace("risk: low", "risk: high"), encoding="utf-8")
            _, errors = checker.validate_artifact(path, SCHEMA)
            self.assertIn("high-risk artifacts must name at least one additional reviewer", "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
