from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = (ROOT / "README.md", ROOT / "CONTRIBUTING.md")
LINK = re.compile(r"\]\(([^)]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self) -> None:
        broken: list[str] = []
        for document in DOCS:
            for target in LINK.findall(document.read_text(encoding="utf-8")):
                path = target.split("#", 1)[0]
                if not path or path.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (document.parent / path).exists():
                    broken.append(f"{document.name}: {target}")
        self.assertEqual([], broken)


if __name__ == "__main__":
    unittest.main()
