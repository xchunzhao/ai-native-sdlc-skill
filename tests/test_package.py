from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_package.py"
SPEC = importlib.util.spec_from_file_location("ai_native_sdlc_package", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class PackageValidationTests(unittest.TestCase):
    def test_current_installable_package_is_self_contained(self) -> None:
        self.assertEqual([], validator.validate_package(validator.DEFAULT_PACKAGE))

    def test_maintainer_files_are_rejected_from_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "ai-native-sdlc"
            shutil.copytree(validator.DEFAULT_PACKAGE, package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            leaked = package / "tests" / "test_leak.py"
            leaked.parent.mkdir(exist_ok=True)
            leaked.write_text("pass\n", encoding="utf-8")
            self.assertIn("maintainer-only file leaked into package: tests/test_leak.py", validator.validate_package(package))


if __name__ == "__main__":
    unittest.main()
