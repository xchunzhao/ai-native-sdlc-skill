#!/usr/bin/env python3
"""Validate that the installable AI-Native SDLC package is self-contained."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = REPO_ROOT / "skills" / "ai-native-sdlc"
REQUIRED = (
    "SKILL.md",
    "LICENSE",
    "assets/intent.template.md",
    "assets/spec.template.md",
    "assets/plan.template.md",
    "assets/AGENTS.md.snippet",
    "references/intent-guide.md",
    "references/spec-guide.md",
    "references/plan-guide.md",
    "references/maintain-guide.md",
    "references/approval-matrix.md",
    "references/artifact-lifecycle.md",
    "references/build-handoff.md",
    "schemas/artifact.schema.json",
    "schemas/lifecycle.yaml",
    "scripts/bootstrap",
    "scripts/bootstrap.py",
    "scripts/sdlc-check",
    "scripts/check.py",
)
RUNTIME_COMMANDS = ("scripts/bootstrap", "scripts/sdlc-check")
FORBIDDEN_PARTS = {"tests", "evals", "__pycache__"}
FORBIDDEN_FILES = {"regression.py"}
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def skill_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, ["SKILL.md must start with YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["SKILL.md frontmatter is not closed"]
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values, []


def validate_package(package: Path) -> list[str]:
    package = package.resolve()
    errors: list[str] = []
    for relative in REQUIRED:
        if not (package / relative).is_file():
            errors.append(f"missing required package file: {relative}")

    skill = package / "SKILL.md"
    if skill.is_file():
        frontmatter, parse_errors = skill_frontmatter(skill)
        errors.extend(parse_errors)
        if frontmatter.get("name") != package.name:
            errors.append(f"SKILL.md name must match package directory `{package.name}`")
        if not frontmatter.get("description"):
            errors.append("SKILL.md requires a non-empty description")
        unknown = sorted(set(frontmatter) - ALLOWED_FRONTMATTER)
        if unknown:
            errors.append(f"unsupported top-level SKILL.md frontmatter: {', '.join(unknown)}")

        for match in re.finditer(r"\]\(([^)]+)\)", skill.read_text(encoding="utf-8")):
            reference = match.group(1)
            if reference.startswith(("http://", "https://", "#")) or "<" in reference:
                continue
            if not (package / reference).exists():
                errors.append(f"broken package-relative SKILL.md link: {reference}")

    for path in package.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(package)
        if any(part in FORBIDDEN_PARTS for part in relative.parts) and path.suffix != ".pyc":
            errors.append(f"maintainer-only file leaked into package: {relative}")
        if path.name in FORBIDDEN_FILES:
            errors.append(f"maintainer-only file leaked into package: {relative}")

    for relative in RUNTIME_COMMANDS:
        path = package / relative
        if path.is_file() and not os.access(path, os.X_OK):
            errors.append(f"runtime command is not executable: {relative}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", nargs="?", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    errors = validate_package(args.package)
    if args.json_output:
        print(json.dumps({"ok": not errors, "package": str(args.package), "errors": errors}, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print(f"Installable Skill package valid: {args.package}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
