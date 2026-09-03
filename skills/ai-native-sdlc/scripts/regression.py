#!/usr/bin/env python3
"""Run the ai-native-sdlc regression suite against its frozen baseline."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = SKILL_ROOT / "evals"
DEFAULT_SUITE = EVALS_ROOT / "suite.json"
DEFAULT_WORKSPACE = Path(
    os.environ.get(
        "XDG_CACHE_HOME",
        Path.home() / ".cache",
    )
) / "ai-native-sdlc-regression"
VERDICT_ORDER = {"IMPROVEMENT": 0, "STABLE": 1, "REGRESSION": 2, "ERROR": 3}


class RegressionError(RuntimeError):
    """A configuration or execution failure, distinct from a regression."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    structural_passed: bool
    structural_errors: tuple[str, ...]
    baseline_score: float | None
    current_score: float | None
    winner: str
    verdict: str
    reason: str
    output_path: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ai-native-sdlc cases against the frozen baseline.",
    )
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--backend", choices=("auto", "copilot", "claude"), default="auto")
    parser.add_argument("--copilot-path", default=os.environ.get("COPILOT_PATH", "copilot"))
    parser.add_argument("--claude-path", default=os.environ.get("CLAUDE_PATH", "claude"))
    parser.add_argument("--model", default=os.environ.get("REGRESSION_MODEL", ""))
    parser.add_argument("--case", action="append", dest="cases", help="Run only this case id; repeatable.")
    parser.add_argument("--jobs", type=int, default=3, help="Concurrent model calls (default: 3).")
    parser.add_argument("--check", action="store_true", help="Validate suite and frozen baselines without model calls.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print the JSON report.")
    return parser.parse_args(argv)


def load_suite(path: Path) -> dict[str, Any]:
    try:
        suite = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegressionError(f"cannot read suite {path}: {exc}") from exc
    if not isinstance(suite.get("cases"), list) or not suite["cases"]:
        raise RegressionError("suite must contain a non-empty cases array")
    ids = [case.get("id") for case in suite["cases"]]
    if any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise RegressionError("every case needs a non-empty id")
    if len(ids) != len(set(ids)):
        raise RegressionError("case ids must be unique")
    return suite


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["output must start with YAML frontmatter (`---`) on line 1"]
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, ["YAML frontmatter is not closed with `---`"]
    values: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {number} is not `key: value`")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            errors.append(f"frontmatter line {number} has an empty key")
            continue
        values[key] = value.strip().strip("\"'")
    return values, errors


def validate_structure(text: str, structure: dict[str, Any]) -> list[str]:
    frontmatter, errors = parse_frontmatter(text)
    for key in structure.get("required_frontmatter", []):
        if not frontmatter.get(key):
            errors.append(f"missing required frontmatter field `{key}`")
    for key, expected in structure.get("frontmatter_equals", {}).items():
        actual = frontmatter.get(key)
        if actual != expected:
            errors.append(f"frontmatter `{key}` must be `{expected}`, got `{actual}`")
    headings = {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }
    for heading in structure.get("required_headings", []):
        if heading not in headings:
            errors.append(f"missing required heading `## {heading}`")
    for pattern in structure.get("forbidden_patterns", []):
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            errors.append(f"forbidden pattern matched: `{pattern}`")
    return errors


def baseline_path(case: dict[str, Any]) -> Path:
    relative = case.get("baseline_path")
    if not isinstance(relative, str) or not relative:
        raise RegressionError(f"case {case['id']} needs baseline_path")
    path = EVALS_ROOT / "baseline" / case["id"] / relative
    if not path.is_file():
        raise RegressionError(f"baseline missing for {case['id']}: {path}")
    return path


def skill_context(case: dict[str, Any]) -> str:
    files = case.get("context_files", ["SKILL.md"])
    sections: list[str] = []
    for relative in files:
        path = SKILL_ROOT / relative
        if not path.is_file():
            raise RegressionError(f"context file missing for {case['id']}: {relative}")
        sections.append(f"===== {relative} =====\n{path.read_text(encoding='utf-8').rstrip()}")
    return "\n\n".join(sections)


def resolve_backend(args: argparse.Namespace) -> tuple[str, str]:
    candidates = (
        [("copilot", args.copilot_path), ("claude", args.claude_path)]
        if args.backend == "auto"
        else [(args.backend, getattr(args, f"{args.backend}_path"))]
    )
    for backend, executable in candidates:
        resolved = shutil.which(executable)
        if resolved:
            return backend, resolved
    requested = ", ".join(executable for _, executable in candidates)
    raise RegressionError(f"no supported model CLI found: {requested}")


def run_model(
    backend: str,
    executable: str,
    prompt: str,
    *,
    system_prompt: str,
    model: str,
) -> str:
    if backend == "copilot":
        command = [
            executable,
            "-p",
            f"{system_prompt}\n\n{prompt}",
            "-s",
            "--no-custom-instructions",
            "--disable-builtin-mcps",
            "--available-tools=",
        ]
    elif backend == "claude":
        command = [
            executable,
            "-p",
            "--safe-mode",
            "--no-session-persistence",
            "--permission-mode",
            "dontAsk",
            "--tools",
            "",
            "--output-format",
            "text",
            "--system-prompt",
            system_prompt,
            prompt,
        ]
    else:
        raise RegressionError(f"unsupported backend: {backend}")
    if model:
        command.extend(["--model", model])
    try:
        completed = subprocess.run(
            command,
            cwd=SKILL_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RegressionError(f"{backend} invocation failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no error output"
        raise RegressionError(f"{backend} exited {completed.returncode}: {detail}")
    output = completed.stdout.strip()
    if not output:
        raise RegressionError(f"{backend} returned an empty response")
    return output + "\n"


def generation_prompt(case: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You are evaluating a local agent skill in an isolated regression run. "
        "Follow the complete skill bundle below. Do not use tools and do not modify files. "
        "Return only the requested artifact content: begin with YAML frontmatter on line 1, "
        "include no preamble, commentary, or Markdown fence.\n\n"
        + skill_context(case)
    )
    prompt = (
        f"Produce the artifact requested by this case.\n\n"
        f"QUALITY CRITERIA:\n{case['quality_criteria']}\n\n"
        f"USER REQUEST:\n{case['prompt']}"
    )
    return system, prompt


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise RegressionError("judge did not return a JSON object")
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise RegressionError(f"judge returned invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise RegressionError("judge response must be a JSON object")
    return value


def judge_case(
    case: dict[str, Any],
    current: str,
    baseline: str,
    *,
    backend: str,
    executable: str,
    model: str,
) -> tuple[float, float, str, str]:
    current_is_a = bool(random.SystemRandom().getrandbits(1))
    output_a, output_b = (current, baseline) if current_is_a else (baseline, current)
    system = (
        "You are a strict blind regression judge. Compare two candidate artifacts against the rubric. "
        "Do not infer which is newer. Return ONLY JSON with keys winner (A, B, or TIE), "
        "a_score, b_score (numbers 0..10), a_summary, and b_summary. Each summary must describe "
        "that output's decisive strengths or weaknesses without comparing it to the other output."
    )
    prompt = (
        f"RUBRIC:\n{case['quality_criteria']}\n\n"
        f"OUTPUT A:\n{output_a}\n\n"
        f"OUTPUT B:\n{output_b}"
    )
    result = parse_json_object(
        run_model(backend, executable, prompt, system_prompt=system, model=model)
    )
    winner = str(result.get("winner", "")).upper()
    if winner not in {"A", "B", "TIE"}:
        raise RegressionError(f"judge winner must be A, B, or TIE; got {winner!r}")
    try:
        a_score = float(result["a_score"])
        b_score = float(result["b_score"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RegressionError("judge scores must be numeric") from exc
    if not (0 <= a_score <= 10 and 0 <= b_score <= 10):
        raise RegressionError("judge scores must be between 0 and 10")
    a_summary = str(result.get("a_summary", "")).strip()
    b_summary = str(result.get("b_summary", "")).strip()
    if not a_summary or not b_summary:
        raise RegressionError("judge must return non-empty a_summary and b_summary")
    if current_is_a:
        reason = f"Current: {a_summary} Baseline: {b_summary}"
        return a_score, b_score, winner, reason
    mapped_winner = {"A": "B", "B": "A", "TIE": "TIE"}[winner]
    reason = f"Current: {b_summary} Baseline: {a_summary}"
    return b_score, a_score, mapped_winner, reason


def classify_verdict(current_score: float, baseline_score: float, winner: str) -> str:
    del winner  # Kept in the report for transparency; score band drives the stable verdict.
    delta = current_score - baseline_score
    if delta < -0.5:
        return "REGRESSION"
    if delta > 0.5:
        return "IMPROVEMENT"
    return "STABLE"


def select_cases(suite: dict[str, Any], requested: list[str] | None) -> list[dict[str, Any]]:
    cases = suite["cases"]
    if not requested:
        return cases
    by_id = {case["id"]: case for case in cases}
    unknown = sorted(set(requested) - by_id.keys())
    if unknown:
        raise RegressionError(f"unknown case id(s): {', '.join(unknown)}")
    return [by_id[case_id] for case_id in requested]


def validate_baselines(cases: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for case in cases:
        text = baseline_path(case).read_text(encoding="utf-8")
        for error in validate_structure(text, case.get("structure", {})):
            failures.append(f"{case['id']}: {error}")
    return failures


def make_run_dir(workspace: Path, suite: dict[str, Any]) -> Path:
    timestamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
    skill_hash = hashlib.sha256((SKILL_ROOT / "SKILL.md").read_bytes()).hexdigest()[:8]
    run_dir = workspace.expanduser().resolve() / f"{timestamp}-{skill_hash}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "skill-snapshot").mkdir()
    for relative in suite.get("snapshot_files", ["SKILL.md"]):
        source = SKILL_ROOT / relative
        target = run_dir / "skill-snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return run_dir


def run_case_generation(
    case: dict[str, Any],
    run_dir: Path,
    backend: str,
    executable: str,
    model: str,
) -> tuple[dict[str, Any], str, Path]:
    system, prompt = generation_prompt(case)
    output = run_model(backend, executable, prompt, system_prompt=system, model=model)
    case_dir = run_dir / case["id"]
    case_dir.mkdir(parents=True, exist_ok=True)
    output_path = case_dir / "current.md"
    output_path.write_text(output, encoding="utf-8")
    return case, output, output_path


def write_report(
    run_dir: Path,
    suite: dict[str, Any],
    args: argparse.Namespace,
    results: list[CaseResult],
) -> dict[str, Any]:
    overall = max((result.verdict for result in results), key=VERDICT_ORDER.get)
    report = {
        "suite": suite.get("suite_name", "ai-native-sdlc"),
        "created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "backend": args.backend,
        "model": args.model or "default",
        "skill_root": str(SKILL_ROOT),
        "run_dir": str(run_dir),
        "overall": overall,
        "cases": [
            {
                "id": result.case_id,
                "structural_passed": result.structural_passed,
                "structural_errors": list(result.structural_errors),
                "baseline_score": result.baseline_score,
                "current_score": result.current_score,
                "winner": result.winner,
                "verdict": result.verdict,
                "reason": result.reason,
                "output": str(result.output_path),
            }
            for result in results
        ],
    }
    (run_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# AI-Native SDLC Regression",
        "",
        f"Overall: **{overall}**",
        "",
        "| Case | Structure | Baseline | Current | Verdict |",
        "|---|---|---:|---:|---|",
    ]
    for result in results:
        baseline = "—" if result.baseline_score is None else f"{result.baseline_score:.2f}"
        current = "—" if result.current_score is None else f"{result.current_score:.2f}"
        structure = "PASS" if result.structural_passed else "FAIL"
        lines.append(
            f"| {result.case_id} | {structure} | {baseline} | {current} | {result.verdict} |"
        )
    lines.extend(["", "## Findings", ""])
    for result in results:
        lines.append(f"- **{result.case_id}:** {result.reason}")
        for error in result.structural_errors:
            lines.append(f"  - {error}")
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def print_report(report: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    print("AI-Native SDLC Regression\n")
    print(f"{'Case':32} {'Structure':10} {'Baseline':>8} {'Current':>8}  Verdict")
    for case in report["cases"]:
        baseline = "—" if case["baseline_score"] is None else f"{case['baseline_score']:.2f}"
        current = "—" if case["current_score"] is None else f"{case['current_score']:.2f}"
        structure = "PASS" if case["structural_passed"] else "FAIL"
        print(f"{case['id']:32} {structure:10} {baseline:>8} {current:>8}  {case['verdict']}")
    print(f"\nOverall: {report['overall']}")
    print(f"Report: {report['run_dir']}/report.md")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        suite = load_suite(args.suite.resolve())
        cases = select_cases(suite, args.cases)
        baseline_failures = validate_baselines(cases)
        if baseline_failures:
            raise RegressionError("invalid frozen baseline:\n- " + "\n- ".join(baseline_failures))
        if args.check:
            print(f"Suite OK: {len(cases)} case(s); all frozen baselines satisfy structural contracts.")
            return 0
        if args.jobs < 1:
            raise RegressionError("--jobs must be at least 1")
        backend, executable = resolve_backend(args)
        args.backend = backend
        run_dir = make_run_dir(args.workspace, suite)
        generated: list[tuple[dict[str, Any], str, Path]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.jobs, len(cases))) as pool:
            futures = [
                pool.submit(run_case_generation, case, run_dir, backend, executable, args.model)
                for case in cases
            ]
            for future in concurrent.futures.as_completed(futures):
                generated.append(future.result())

        results: list[CaseResult] = []
        judge_inputs: list[tuple[dict[str, Any], str, Path, list[str]]] = []
        for case, output, output_path in generated:
            errors = validate_structure(output, case.get("structure", {}))
            if errors:
                results.append(
                    CaseResult(
                        case["id"], False, tuple(errors), None, None, "B", "REGRESSION",
                        "Current output violates the structural contract.", output_path,
                    )
                )
            else:
                judge_inputs.append((case, output, output_path, errors))

        def judge_one(item: tuple[dict[str, Any], str, Path, list[str]]) -> CaseResult:
            case, output, output_path, errors = item
            baseline = baseline_path(case).read_text(encoding="utf-8")
            current_score, baseline_score, winner, reason = judge_case(
                case,
                output,
                baseline,
                backend=backend,
                executable=executable,
                model=args.model,
            )
            verdict = classify_verdict(current_score, baseline_score, winner)
            return CaseResult(
                case["id"], True, tuple(errors), baseline_score, current_score,
                winner, verdict, reason, output_path,
            )

        if judge_inputs:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.jobs, len(judge_inputs))) as pool:
                futures = [pool.submit(judge_one, item) for item in judge_inputs]
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
        order = {case["id"]: index for index, case in enumerate(cases)}
        results.sort(key=lambda result: order[result.case_id])
        report = write_report(run_dir, suite, args, results)
        print_report(report, args.json_output)
        return 1 if report["overall"] == "REGRESSION" else 0
    except RegressionError as exc:
        print(f"regression infrastructure error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
