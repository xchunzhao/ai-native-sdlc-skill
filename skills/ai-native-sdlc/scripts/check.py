#!/usr/bin/env python3
"""Validate AI-Native SDLC artifacts and their Git-backed gate chain."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "schemas" / "artifact.schema.json"
ARTIFACT_FILES = {"intent": "intent.md", "spec": "spec.md", "plan": "plan.md"}
REQUIRED_HEADINGS = {
    "intent": ["Problem", "Proposed outcome", "Affected users and systems", "Constraints", "Open questions"],
    "spec": ["Requirements & design spec", "Integration with existing code", "Policy compliance", "Areas of concern"],
    "plan": ["Files that change", "Order of work", "Risks", "Proof", "Requirement traceability", "Build handoff"],
}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"<[^>]+>|_(?:e\.g\.|What |Which |How |Question |Step |Risk |Concern )", re.IGNORECASE)


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    if value == "[]":
        return []
    if value in {"true", "false"}:
        return value == "true"
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], list[str]]:
    if not text.startswith("---\n"):
        return {}, ["must start with YAML frontmatter (`---`) on line 1"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["frontmatter is not closed with `---`"]

    values: dict[str, Any] = {}
    errors: list[str] = []
    active_list: str | None = None
    for number, line in enumerate(text[4:end].splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and active_list:
            item = parse_scalar(line[4:])
            if not isinstance(item, str) or not item:
                errors.append(f"line {number}: list item must be a non-empty string")
            else:
                values[active_list].append(item)
            continue
        if line.startswith((" ", "\t")):
            errors.append(f"line {number}: nested mappings are not supported")
            continue
        if ":" not in line:
            errors.append(f"line {number}: expected `key: value`")
            active_list = None
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key or key in values:
            errors.append(f"line {number}: invalid or duplicate key `{key}`")
            active_list = None
            continue
        value = parse_scalar(raw)
        if value is None and not raw.strip():
            values[key] = [] if key == "reviewers" else None
            active_list = key if key == "reviewers" else None
        else:
            values[key] = value
            active_list = key if isinstance(value, list) else None
    return values, errors


def body_after_frontmatter(text: str) -> str:
    end = text.find("\n---\n", 4)
    return text[end + 5 :] if end >= 0 else ""


def validate_artifact(path: Path, schema: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    text = path.read_text(encoding="utf-8")
    values, errors = parse_frontmatter(text)
    label = str(path)
    required = set(schema["required"])
    properties = schema["properties"]

    for key in sorted(required - values.keys()):
        errors.append(f"missing required frontmatter field `{key}`")
    for key in sorted(values.keys() - properties.keys()):
        errors.append(f"unknown frontmatter field `{key}`")

    artifact = values.get("artifact")
    if artifact not in ARTIFACT_FILES:
        errors.append("`artifact` must be intent, spec, or plan")
    elif path.name != ARTIFACT_FILES[artifact]:
        errors.append(f"artifact `{artifact}` must be stored as `{ARTIFACT_FILES[artifact]}`")

    feature = values.get("feature")
    if not isinstance(feature, str) or not SLUG_RE.fullmatch(feature):
        errors.append("`feature` must be a kebab-case slug")
    elif path.parent.name != feature:
        errors.append(f"`feature` `{feature}` does not match directory `{path.parent.name}`")

    for key in ("author",):
        if not isinstance(values.get(key), str) or not values[key].strip():
            errors.append(f"`{key}` must be a non-empty string")

    status = values.get("status")
    allowed_statuses = properties["status"]["enum"]
    if status not in allowed_statuses:
        errors.append(f"`status` must be one of {', '.join(allowed_statuses)}")

    risk = values.get("risk")
    if risk not in properties["risk"]["enum"]:
        errors.append("`risk` must be low, medium, or high")

    reviewers = values.get("reviewers")
    if not isinstance(reviewers, list) or any(not isinstance(item, str) or not item for item in reviewers):
        errors.append("`reviewers` must be a YAML list of non-empty strings")
    elif len(reviewers) != len(set(reviewers)):
        errors.append("`reviewers` must not contain duplicates")
    if risk == "high" and not reviewers:
        errors.append("high-risk artifacts must name at least one additional reviewer")

    created = values.get("created")
    try:
        dt.date.fromisoformat(str(created))
    except ValueError:
        errors.append("`created` must be an ISO date (YYYY-MM-DD)")

    if status in {"accepted", "stale", "superseded"}:
        if not values.get("accepted_by"):
            errors.append(f"status `{status}` requires `accepted_by`")
        try:
            dt.datetime.fromisoformat(str(values.get("accepted_at", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"status `{status}` requires ISO datetime `accepted_at`")
    if status == "superseded" and not values.get("superseded_by"):
        errors.append("status `superseded` requires `superseded_by`")

    required_refs = {"spec": ("intent_ref",), "plan": ("intent_ref", "spec_ref")}.get(artifact, ())
    for key in required_refs:
        value = values.get(key)
        if not isinstance(value, str) or not SHA_RE.fullmatch(value):
            errors.append(f"`{key}` must be a 7-40 character lowercase Git commit SHA")

    body = body_after_frontmatter(text)
    if artifact in REQUIRED_HEADINGS:
        for heading in REQUIRED_HEADINGS[artifact]:
            if not re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.MULTILINE):
                errors.append(f"missing required heading `## {heading}`")
    if PLACEHOLDER_RE.search(body):
        errors.append("artifact still contains template placeholder text")

    return values, [f"{label}: {error}" for error in errors]


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def git_root(path: Path) -> Path | None:
    probe = git(path if path.is_dir() else path.parent, "rev-parse", "--show-toplevel")
    return Path(probe.stdout.strip()) if probe.returncode == 0 else None


def latest_artifact_commit(root: Path, path: Path) -> str | None:
    relative = path.resolve().relative_to(root.resolve())
    result = git(root, "log", "-n", "1", "--format=%H", "--", str(relative))
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def resolve_commit(root: Path, reference: str) -> str | None:
    result = git(root, "rev-parse", "--verify", f"{reference}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def artifact_at_commit(root: Path, path: Path, reference: str) -> tuple[dict[str, Any], str | None]:
    relative = path.resolve().relative_to(root.resolve())
    result = git(root, "show", f"{reference}:{relative}")
    if result.returncode != 0:
        return {}, result.stderr.strip() or "artifact not present at reference"
    values, errors = parse_frontmatter(result.stdout)
    return values, "; ".join(errors) if errors else None


def validate_chain(feature_dir: Path, artifacts: dict[str, tuple[Path, dict[str, Any]]], root: Path | None, no_git: bool) -> list[str]:
    errors: list[str] = []
    if "spec" in artifacts and "intent" not in artifacts:
        errors.append(f"{feature_dir}: spec exists without intent")
    if "plan" in artifacts and "spec" not in artifacts:
        errors.append(f"{feature_dir}: plan exists without spec")

    dependencies = {
        "spec": (("intent", "intent_ref"),),
        "plan": (("intent", "intent_ref"), ("spec", "spec_ref")),
    }
    for artifact, deps in dependencies.items():
        if artifact not in artifacts:
            continue
        for upstream, ref_field in deps:
            if upstream not in artifacts:
                continue
            upstream_path, upstream_data = artifacts[upstream]
            current_path, current_data = artifacts[artifact]
            if upstream_data.get("status") != "accepted":
                errors.append(f"{current_path}: requires `{upstream}` status `accepted`")
            reference = current_data.get(ref_field)
            if no_git or not isinstance(reference, str) or not SHA_RE.fullmatch(reference):
                continue
            if root is None:
                errors.append(f"{current_path}: cannot verify `{ref_field}` outside a Git repository")
                continue
            resolved = resolve_commit(root, reference)
            if not resolved:
                errors.append(f"{current_path}: `{ref_field}` does not resolve to a commit")
                continue
            recorded, error = artifact_at_commit(root, upstream_path, resolved)
            if error:
                errors.append(f"{current_path}: cannot read `{upstream}` at `{ref_field}`: {error}")
            elif recorded.get("status") != "accepted":
                errors.append(f"{current_path}: `{ref_field}` does not contain an accepted `{upstream}`")
            latest = latest_artifact_commit(root, upstream_path)
            if latest and latest != resolved:
                errors.append(f"{current_path}: `{ref_field}` is stale; latest `{upstream}` commit is {latest}")

    if root and not no_git:
        for path, data in artifacts.values():
            if data.get("status") != "accepted":
                continue
            relative = path.resolve().relative_to(root.resolve())
            unstaged = git(root, "diff", "--quiet", "--", str(relative)).returncode
            staged = git(root, "diff", "--cached", "--quiet", "--", str(relative)).returncode
            if unstaged or staged:
                errors.append(f"{path}: accepted artifact has uncommitted changes; reset it to `draft`")
    return errors


def feature_dirs(target: Path) -> list[Path]:
    target = target.resolve()
    if target.is_file():
        return [target.parent]
    if any((target / name).is_file() for name in ARTIFACT_FILES.values()):
        return [target]
    sdlc = target / "docs" / "sdlc"
    if sdlc.is_dir():
        target = sdlc
    if not target.is_dir():
        return []
    return sorted(path for path in target.iterdir() if path.is_dir())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="project root, docs/sdlc, feature directory, or artifact")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable output")
    parser.add_argument("--no-git", action="store_true", help="skip commit and stale-reference checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.path)
    dirs = feature_dirs(target)
    if not dirs:
        errors = [f"{target}: no SDLC feature directories found"]
    else:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        root = git_root(target)
        errors: list[str] = []
        for directory in dirs:
            artifacts: dict[str, tuple[Path, dict[str, Any]]] = {}
            for artifact, filename in ARTIFACT_FILES.items():
                path = directory / filename
                if path.is_file():
                    values, artifact_errors = validate_artifact(path, schema)
                    artifacts[artifact] = (path, values)
                    errors.extend(artifact_errors)
            if not artifacts:
                continue
            errors.extend(validate_chain(directory, artifacts, root, args.no_git))

    result = {"ok": not errors, "errors": errors}
    if args.json_output:
        print(json.dumps(result, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print("AI-Native SDLC artifacts valid")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
