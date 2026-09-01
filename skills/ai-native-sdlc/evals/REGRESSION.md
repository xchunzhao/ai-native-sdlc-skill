# Regression check — ai-native-sdlc

**Purpose:** After changing `SKILL.md`, `references/*`, or `assets/*.template.md`, run this to know whether the change is a **regression, no-change, or improvement** — without a human eyeballing markdown.

## Paths

- **Skill root:** `~/.claude/skills/ai-native-sdlc/`
- **This eval suite (ships with the skill):** `~/.claude/skills/ai-native-sdlc/evals/`
  - `suite.json` — frozen prompts + quality criteria per case
  - `baseline/` — frozen artifacts + comparator verdicts (the ceiling to beat / floor to not fall below)
  - `REGRESSION.md` — this file
- **Scratch workspace (do NOT commit into the skill):** `~/.claude/skills/ai-native-sdlc-workspace/`
  - `iteration-N/` — each run's outputs, verdicts, and skill snapshots

Rationale: the eval **contract** (prompts, rubric, baseline) travels with the skill and is version-controlled together with any change it evaluates. Concrete run data is ephemeral and lives outside.

## Baseline (frozen 2026-09-01, iteration-1)

Scores are LLM-judge overall_score on a 1–10 scale, blind vs. a no-skill baseline.

| case | with_skill | without_skill | why with_skill won |
|---|---|---|---|
| feature-intent | 9.4 | 8.7 | Stays at intent-level; baseline leaks into design (names ledger model, mandates append-only) |
| incident-maintain | 9.67 | 9.67 | Tiebreak: skill produces an intent-shaped artifact that mechanically re-enters the loop |
| migration-highrisk | 10 | 8 | Skill opens with approval-matrix escalation naming tech lead / architect; baseline never invokes it |

## When to run

- Any edit to `SKILL.md`, `references/*.md`, `assets/*.template.md`, `scripts/bootstrap.sh`
- Before merging changes upstream
- To pick between two candidate SKILL.md drafts

## Trigger

Say to any capable agent:

> "Run the ai-native-sdlc regression check."

Agent follows the procedure below.

## Procedure (for the agent)

### 1. Determine iteration number

```
ls ~/.claude/skills/ai-native-sdlc-workspace/iteration-* 2>/dev/null
```

Pick the next unused N. `iteration-1` is reserved forever as the origin — never overwrite.

### 2. Snapshot the current skill

```
mkdir -p ~/.claude/skills/ai-native-sdlc-workspace/iteration-N
cp -r ~/.claude/skills/ai-native-sdlc ~/.claude/skills/ai-native-sdlc-workspace/iteration-N/skill-snapshot
```

Reason: SKILL.md changes between runs. The snapshot documents exactly what was evaluated.

### 3. Run the 3 cases against the current skill

Read `~/.claude/skills/ai-native-sdlc/evals/suite.json` for prompts + `artifact_path` + `quality_criteria`.

Spawn 3 subagents in a **single `task` batch** (one call, three items in `tasks[]`). Each item:

- Reads `skill://ai-native-sdlc` (SKILL.md) plus files that guide points to
- Working root: `~/.claude/skills/ai-native-sdlc-workspace/iteration-N/<case-id>/outputs/`
- Produces the artifact at `<working-root>/<case.artifact_path>`
- Frontmatter: `status: draft`, `author: eval-run`, `date: <today>`
- Does NOT run `bootstrap.sh`, tests, or validation

### 4. Blind-judge new vs. baseline

Spawn 3 comparator subagents in **one `task` batch**. Each item:

- Reads the comparator protocol at `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/agents/comparator.md`
- Compares:
  - **new:** `~/.claude/skills/ai-native-sdlc-workspace/iteration-N/<case-id>/outputs/<artifact_path>`
  - **baseline:** `~/.claude/skills/ai-native-sdlc/evals/baseline/<case-id>/<artifact_path>`
- **You (the orchestrator) MUST randomize A/B per case** — flip a coin for each; keep the mapping locally so you can decode, but tell each comparator only "compare A vs B" with no hint which is which
- Rubric anchor: `case.quality_criteria` from `suite.json`
- Writes: `~/.claude/skills/ai-native-sdlc-workspace/iteration-N/<case-id>/regression.json`

### 5. Emit `iteration-N/verdict.md`

Path: `~/.claude/skills/ai-native-sdlc-workspace/iteration-N/verdict.md`.

Table: case × baseline score × new score × delta × verdict × judge's one-line reasoning.

Per-case verdict:
- **REGRESSION** — new < baseline by >0.5, OR judge picks baseline
- **STABLE** — |Δ| ≤ 0.5 AND judge calls TIE or ambiguous
- **IMPROVEMENT** — new > baseline by >0.5 AND judge picks new

Overall verdict: worst per-case verdict.

Print `verdict.md` inline in chat. **If any REGRESSION, quote the judge's `weaknesses` for that case verbatim** — that's actionable feedback for what to fix in SKILL.md.

### 6. If IMPROVEMENT, offer to promote

Ask user: "iteration-N wins on {cases}. Promote to baseline?"

If yes:

```
cd ~/.claude/skills/ai-native-sdlc/evals
rm -rf baseline
mkdir baseline
for case in <cases>; do
  mkdir -p baseline/<case-id>
  cp -r ~/.claude/skills/ai-native-sdlc-workspace/iteration-N/<case-id>/outputs/* baseline/<case-id>/
  cp ~/.claude/skills/ai-native-sdlc-workspace/iteration-N/<case-id>/regression.json baseline/<case-id>/comparison.json
done
```

Then update this file's baseline score table.

Otherwise: leave baseline alone. Iteration-N stays in workspace for reference.

## Cost + time

- Step 3: 3 subagents × ~1–2 min = ~2 min wall
- Step 4: 3 subagents × ~1–2 min = ~2 min wall
- Total: **~5 min from "go" to verdict**

## Limits — read before trusting the number

1. **LLM-judge noise ±0.5.** Same output judged twice by two comparator instances can differ by ~0.5 on the 10-scale. STABLE band is ±0.5 for that reason. Deltas smaller than that are noise, not signal.

2. **Prompt overfitting.** The 3 prompts in `suite.json` are fixed. A skill change that helps only these 3 may not generalize. If a change looks like a big win, spot-check with an ad-hoc 4th prompt before promoting.

3. **Baseline drift.** Every promotion moves the baseline forward. `iteration-1/` under the workspace stays as the fixed origin — never overwrite. If several promotions later you want to know "how far have we come since day 1", judge the current baseline against `iteration-1/` outputs.

4. **Doesn't test triggering.** This measures artifact quality when the skill IS used, not whether Claude decides to use it on ambiguous prompts. Triggering is a separate axis (and for this skill, mostly obviated by the `/intent /spec /plan` slash commands that ship alongside).

5. **Doesn't test `bootstrap.sh` or gate mechanics.** Procedural side-effects, out of scope here — verify by hand.

## Upstream gap

This procedure lives in the skill because `skill-creator` doesn't ship a first-class regression-check wrapper. It has the primitives (comparator, aggregate_benchmark) but no `scripts/regression_check.py` that binds them into "iteration-N vs frozen baseline → verdict". Every skill that cares about quality ends up hand-rolling this. Worth upstreaming.
