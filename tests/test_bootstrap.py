from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "ai-native-sdlc" / "scripts" / "bootstrap.py"
SPEC = importlib.util.spec_from_file_location("ai_native_sdlc_bootstrap", SCRIPT)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bootstrap
SPEC.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_project_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            agents = project / "AGENTS.md"
            agents.write_text("# Project rules\n\nKeep this line.\n", encoding="utf-8")
            self.assertEqual(0, bootstrap.main([str(project)]))
            first = agents.read_text(encoding="utf-8")
            self.assertIn("Keep this line.", first)
            self.assertIn("AI-NATIVE-SDLC:START version=0.2.0", first)
            self.assertEqual(0, bootstrap.main([str(project)]))
            self.assertEqual(first, agents.read_text(encoding="utf-8"))
            self.assertEqual(0, bootstrap.main([str(project), "--check"]))

    def test_legacy_section_is_migrated_without_consuming_next_section(self) -> None:
        legacy = "# Rules\n\n## AI-Native SDLC\n\nOld block.\n\n## Testing\n\nKeep testing.\n"
        updated, action = bootstrap.replace_managed(legacy, bootstrap.rendered_block())
        self.assertEqual("migrated", action)
        self.assertNotIn("Old block.", updated)
        self.assertIn("## Testing\n\nKeep testing.", updated)
        self.assertEqual(1, updated.count(bootstrap.START_PREFIX))

    def test_malformed_markers_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "malformed"):
            bootstrap.replace_managed("<!-- AI-NATIVE-SDLC:START version=0.1.0 -->\n", bootstrap.rendered_block())


if __name__ == "__main__":
    unittest.main()
