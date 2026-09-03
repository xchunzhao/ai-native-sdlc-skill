---
name: ai-native-sdlc
description: This skill should be used when substantial feature work needs an auditable intent → spec → plan → build-handoff chain, or when a production signal needs read-only diagnosis before re-entering that chain. Also use for requests to write intent.md, spec.md, or plan.md; validate or bootstrap the SDLC structure; assess policy or approval gates; or prepare an accepted plan for implementation.
license: MIT
metadata:
  version: "0.2.0"
---

# AI-Native SDLC

Based on Anthropic's [AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook). Every substantial change flows through three markdown artifacts before code is written:

| Stage | Artifact | Answers |
|---|---|---|
| 1 | `intent.md` | Why are we doing this? Who is it for? |
| 2 | `spec.md` | What does "done" look like? What policies constrain it? |
| 3 | `plan.md` | How will the code change? In what order? How do we prove it works? |

**Each stage ends with a committed artifact and human acceptance. The next stage records the accepted upstream commit.** The Git-backed chain is the audit trail; `<skill-dir>/scripts/sdlc-check` verifies that it remains current.

## Boundary with related skills

- `writing-plans` / `executing-plans` — a single-plan-document workflow with outputs in `docs/superpowers/plans/`. Different philosophy, different location. Do not confuse them with this skill. If the user is already using `writing-plans`, don't force them onto this one — they can coexist per project.
- `skill-creator`, `command-development`, `agent-development` — for building Claude Code tooling, not for feature planning.

This skill owns the **three-artifact governance regime**, its gates, approval chain, and the final build handoff. Implementation, merge, and deployment belong to the team's normal execution workflow. Outputs live at `docs/sdlc/<feature-slug>/`.

## First time in a project

Run bootstrap when the project's `AGENTS.md` does not contain an `AI-NATIVE-SDLC:START` managed marker, or when that marker reports an older skill version:

1. Run `<path-to-this-skill>/scripts/bootstrap` from the project root (or pass the project directory explicitly). Use `python <path-to-this-skill>/scripts/bootstrap.py` on hosts without a POSIX shell.
2. Bootstrap creates `docs/sdlc/` and installs or upgrades a versioned, managed AI-Native SDLC block in `AGENTS.md`.
3. Content outside the managed markers is project-owned and must remain untouched. Workflow docs and templates remain in this skill as the single source of truth.
4. Review and commit the project change as `sdlc: bootstrap AI-Native SDLC v0.2.0`.

If the managed block is current, continue directly to the requested stage.

## Stage entry points

Users can request any stage in natural language. Host-specific slash commands are optional adapters and are not shipped by this framework-neutral skill.

### Intent — draft `intent.md`

**Read** `references/intent-guide.md` before doing anything else. Then:

1. Confirm the slug (kebab-case, matches or will match branch name).
2. Ensure `docs/sdlc/<slug>/` exists.
3. Read the intent template from this skill's `assets/intent.template.md` and write a filled version to `docs/sdlc/<slug>/intent.md`. **Do not copy the template into the project's `docs/sdlc/`** — the skill is the single source of truth for templates.
4. Fill sections through conversation with the user — one section at a time, using their words.
5. Set author, date, risk, reviewers, `status: draft`, and leave acceptance fields empty.
6. Suggest commit: `sdlc(<slug>): add intent.md`.
7. Product owner acceptance records `accepted_by` and `accepted_at` in a separate commit; only then may spec begin.

Detailed guidance, section-by-section coaching, and failure modes: [`references/intent-guide.md`](references/intent-guide.md).

### Spec — draft `spec.md`

**Read** `references/spec-guide.md` before doing anything else. Then:

1. **Gate check:** run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>`, verify `intent.md` is accepted, and record its full commit SHA as `intent_ref`. If not, stop.
2. Read the accepted intent fully. Open questions become spec obligations.
3. Load organizational policy skills (security, brand, compliance, UX) — see the guide for where to look.
4. Explore relevant code (`Grep`, `Read`, `Explore`) so "Integration with existing code" has real file paths.
5. Read the spec template from this skill's `assets/spec.template.md` and write a filled version to `docs/sdlc/<slug>/spec.md`. **Do not copy the template into the project.**
6. Draft in one pass, then critique. Every open question from intent must be answered here.
7. **Flag concerns honestly** in `Areas of concern`. Do not paper over policy conflicts.
8. Suggest commit: `sdlc(<slug>): add spec.md`.
9. Product owner acceptance records the acceptance fields; flagged concerns go to policy owners before plan begins.

Detailed guidance: [`references/spec-guide.md`](references/spec-guide.md).

### Plan — draft `plan.md` in plan mode

**Read** `references/plan-guide.md` before doing anything else. Then:

1. **Gate check:** run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>`, verify `spec.md` is accepted, and record the accepted intent/spec commits as `intent_ref` and `spec_ref`.
2. Re-read `intent.md` (why) and `spec.md` (what).
3. Enter plan mode. If your agent has a dedicated plan-mode tool (e.g. Claude Code's `EnterPlanMode`), call it — you get a scratchpad and are prevented from writing files until you exit. If not, operate in read-only exploration mode until the plan is ready to write.
4. Explore the code the spec named. Make sure every file path is real.
5. Draft the plan by talking to the engineer — propose, listen, refine.
6. Read the plan template and write `docs/sdlc/<slug>/plan.md` without copying the template into the project.
7. Fill every section, including specific proof, requirement traceability, and build handoff ownership.
8. Exit plan mode when the plan is complete.
9. Suggest commit: `sdlc(<slug>): add plan.md`.
10. Engineer acceptance records the acceptance fields; high-risk plans require tech lead or architect signoff before build handoff.

Detailed guidance: [`references/plan-guide.md`](references/plan-guide.md).

## Gate and revision mechanics

Read [`references/artifact-lifecycle.md`](references/artifact-lifecycle.md). A status label alone is insufficient: accepted artifacts require acceptance evidence, and downstream artifacts pin the full accepted upstream commit. Any semantic edit resets the edited artifact to `draft`; changing intent makes spec and plan stale, and changing spec makes plan stale.

Run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>` before advancing a stage. Do not update stale references mechanically: reconcile the downstream artifact with the changed decision, then obtain approval again.

## Approval and escalation

Who reviews what, and when to escalate to tech lead / architect — see [`references/approval-matrix.md`](references/approval-matrix.md). Key rule: any change touching auth, payments, PII, migrations, external contracts, compliance surface, or post-mortem territory is high-risk. Name the escalation target in the artifact's PR description from the start.

## Handoff to build

After `plan.md` is accepted and `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>` succeeds, follow [`references/build-handoff.md`](references/build-handoff.md). The plan must map requirements to implementation steps and proof, name owners and reviewers, and link the tracking item. The implementation change links the accepted plan.

If implementation reveals drift, stop at the affected boundary. Reset and re-approve plan, spec, or intent at the level where the decision changed. This skill never pushes, merges, or deploys.

## Starting from an incident (Maintain loop)

When work starts from a production signal, the agent diagnoses read-only and produces an incident `intent.md` that re-enters the chain at the intent stage. It does not fix code, deploy, or cross a review gate; an accepted plan hands the fix to the normal implementation workflow.

Slug convention for incidents: `incident-<YYYY-MM-DD>-<short-desc>` (e.g. `incident-2026-09-01-refund-500s`), which keeps them visually distinct from feature slugs in `docs/sdlc/`.

Full procedure, evidence requirements, and failure modes: [`references/maintain-guide.md`](references/maintain-guide.md).

## When to skip

Not everything needs three artifacts. Skip for typo fixes, dep bumps, docs edits with no policy implication, and reverts. Emergency hotfixes still need retrospective `intent.md` + `spec.md` within one business day.

If in doubt, write at least an `intent.md`. It's cheap, and the audit trail is worth more than the fifteen minutes.


## Files in this skill

- `SKILL.md` — boundaries, stage flow, gates, and handoff
- `schemas/` — machine-readable artifact shape and lifecycle rules
- `assets/` — artifact templates and the managed `AGENTS.md` block
- `references/*-guide.md` — stage guidance
- `references/artifact-lifecycle.md`, `approval-matrix.md`, `build-handoff.md` — governance contracts
- `scripts/bootstrap` + `bootstrap.py` — managed project bootstrap and upgrade
- `scripts/sdlc-check` + `check.py` — deterministic artifact and revision-chain validation
- `LICENSE` — terms that travel with copied installations
