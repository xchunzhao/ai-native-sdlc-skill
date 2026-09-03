# Regression check — ai-native-sdlc

Run the regression suite after changing the protocol, schemas, lifecycle guides, templates, bootstrap, checker, or approval rules:

```bash
python3 scripts/regression.py
```

The repository maintainer command is `scripts/regression.py`. It is self-contained and uses only the Python standard library plus an authenticated GitHub Copilot CLI or Claude CLI. `--backend auto` prefers Copilot when both are installed, avoiding dependence on a Claude gateway's model mapping.

## What the runner proves

For every case in `suite.json`, the runner:

1. Loads the current skill and the case-specific guide, approval matrix, and template.
2. Runs the case in an isolated, tool-free Claude process.
3. Rejects output that violates the case's deterministic structural contract.
4. Randomizes current/baseline as A/B and asks a fresh judge to compare them against `quality_criteria`.
5. Writes `report.md`, `report.json`, generated artifacts, and a skill snapshot to a timestamped cache directory.

Frozen baselines live under repository-root `evals/baseline/<case-id>/`. The runner loads the installable skill from `skills/ai-native-sdlc/`; generated run data remains outside both trees.

## Commands

```bash
python3 scripts/regression.py                         # full suite
python3 scripts/regression.py --case feature-intent   # one case
python3 scripts/regression.py --backend copilot       # select Copilot
python3 scripts/regression.py --backend claude        # select Claude
python3 scripts/regression.py --model gpt-5.4         # pin a supported model
python3 scripts/regression.py --jobs 1                # serialize model calls
python3 scripts/regression.py --json                  # machine-readable stdout
python3 scripts/regression.py --check                 # offline integrity check
python3 scripts/regression.py --workspace /tmp/runs   # override report location
```

`COPILOT_PATH`, `CLAUDE_PATH`, and `REGRESSION_MODEL` provide environment-level defaults for the corresponding CLI options.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Every case is STABLE or IMPROVEMENT |
| `1` | At least one case is a REGRESSION |
| `2` | Runner, suite, baseline, or model-backend failure |

Structural violations always count as REGRESSION. For structurally valid outputs:

- **REGRESSION** — current score is more than 0.5 below baseline.
- **STABLE** — the score difference is within 0.5.
- **IMPROVEMENT** — current score is more than 0.5 above baseline.

The blind winner remains in `report.json` as diagnostic evidence, but it does not override the ±0.5 stability band; doing so would turn ordinary judge variance into flaky regressions. Structural violations always bypass the band and fail immediately.

## Baseline promotion

Never promote solely because one run says IMPROVEMENT. First:

1. Re-run the full suite with the same pinned model.
2. Confirm every case is STABLE or IMPROVEMENT.
3. Inspect generated artifacts and structural results.
4. Copy only the reviewed winning artifacts into `baseline/<case-id>/`.
5. Update the baseline score table or comparison metadata if maintained.
6. Commit the baseline change separately so review can distinguish product instructions from evaluation-policy changes.

## Limits

- The suite covers three intent shapes plus a high-risk spec and plan. Gate transitions, skip routing, triggering, and Git staleness remain deterministic-test priorities before claiming complete lifecycle coverage.
- A model or CLI version change can move scores independently of a skill change. Pin `--model` for release decisions.
- Blind comparison evaluates artifact quality; deterministic checks enforce syntax and required sections. Neither substitutes for reviewing risky workflow-policy changes.
