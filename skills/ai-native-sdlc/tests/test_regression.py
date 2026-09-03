from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "regression.py"
SPEC = importlib.util.spec_from_file_location("ai_native_sdlc_regression", SCRIPT)
assert SPEC and SPEC.loader
regression = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = regression
SPEC.loader.exec_module(regression)


class RegressionRunnerTests(unittest.TestCase):
    def test_frozen_baselines_satisfy_structural_contracts(self) -> None:
        suite = regression.load_suite(regression.DEFAULT_SUITE)
        self.assertEqual([], regression.validate_baselines(suite["cases"]))

    def test_structure_requires_frontmatter_on_first_line(self) -> None:
        errors = regression.validate_structure(
            "Preamble\n---\nartifact: intent\n---\n",
            {"required_frontmatter": ["artifact"]},
        )
        self.assertIn("output must start with YAML frontmatter (`---`) on line 1", errors)

    def test_structure_checks_fields_headings_and_placeholders(self) -> None:
        text = """---
artifact: intent
feature: sample
author: eval
status: draft
created: 2026-09-03
---

## Problem

_<placeholder>_
"""
        errors = regression.validate_structure(
            text,
            {
                "required_frontmatter": ["artifact", "feature", "author", "status", "created"],
                "frontmatter_equals": {"artifact": "intent", "status": "draft"},
                "required_headings": ["Problem", "Open questions"],
                "forbidden_patterns": ["_<[^>]+>_"],
            },
        )
        self.assertIn("missing required heading `## Open questions`", errors)
        self.assertIn("forbidden pattern matched: `_<[^>]+>_`", errors)

    def test_verdict_contract(self) -> None:
        self.assertEqual("STABLE", regression.classify_verdict(8.9, 9.0, "B"))
        self.assertEqual("REGRESSION", regression.classify_verdict(8.4, 9.0, "TIE"))
        self.assertEqual("STABLE", regression.classify_verdict(9.2, 9.0, "A"))
        self.assertEqual("IMPROVEMENT", regression.classify_verdict(9.6, 9.0, "A"))

    def test_check_mode_returns_success_without_model_calls(self) -> None:
        self.assertEqual(0, regression.main(["--check"]))


if __name__ == "__main__":
    unittest.main()
