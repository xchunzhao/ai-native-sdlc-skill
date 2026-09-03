#!/usr/bin/env python3
"""Install or upgrade the managed AI-Native SDLC project block."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "0.2.0"
START_PREFIX = "<!-- AI-NATIVE-SDLC:START"
END = "<!-- AI-NATIVE-SDLC:END -->"
SKILL_ROOT = Path(__file__).resolve().parents[1]
SNIPPET = SKILL_ROOT / "assets" / "AGENTS.md.snippet"


def rendered_block() -> str:
    body = SNIPPET.read_text(encoding="utf-8").strip()
    return f"{START_PREFIX} version={VERSION} -->\n{body}\n{END}"


def replace_managed(text: str, block: str) -> tuple[str, str]:
    starts = [match.start() for match in re.finditer(re.escape(START_PREFIX), text)]
    ends = [match.start() for match in re.finditer(re.escape(END), text)]
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise ValueError("malformed AI-Native SDLC managed markers; refusing to overwrite AGENTS.md")
        end = ends[0] + len(END)
        return text[: starts[0]] + block + text[end:], "updated"

    heading = re.search(r"(?m)^## AI-Native SDLC\s*$", text)
    if heading:
        next_heading = re.search(r"(?m)^## (?!AI-Native SDLC\s*$).+$", text[heading.end() :])
        end = heading.end() + next_heading.start() if next_heading else len(text)
        prefix = text[: heading.start()].rstrip()
        suffix = text[end:].lstrip("\n")
        pieces = [piece for piece in (prefix, block, suffix.rstrip()) if piece]
        return "\n\n".join(pieces) + "\n", "migrated"

    prefix = text.rstrip()
    return (prefix + "\n\n" if prefix else "") + block + "\n", "installed"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        Path(name).replace(path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", nargs="?", default=".")
    parser.add_argument("--check", action="store_true", help="report whether the managed block is current without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project = Path(args.project_dir).resolve()
    agents = project / "AGENTS.md"
    current = agents.read_text(encoding="utf-8") if agents.exists() else "# AGENTS.md\n\nProject-level guidance for coding agents.\n"
    block = rendered_block()
    try:
        updated, action = replace_managed(current, block)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.check:
        if current == updated and (project / "docs" / "sdlc").is_dir():
            print(f"AI-Native SDLC managed block is current (v{VERSION})")
            return 0
        print(f"AI-Native SDLC bootstrap is not current: {project}", file=sys.stderr)
        return 1

    (project / "docs" / "sdlc").mkdir(parents=True, exist_ok=True)
    if current != updated:
        atomic_write(agents, updated)
    else:
        action = "unchanged"
    print(f"{action}: AI-Native SDLC v{VERSION} in {agents}")
    print("wrote: docs/sdlc/" if action != "unchanged" else "unchanged: docs/sdlc/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
