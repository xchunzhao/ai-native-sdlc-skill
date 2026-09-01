---
name: ai-native-sdlc
description: This skill should be used when the user starts new feature work and wants to follow the AI-native SDLC playbook (intent → spec → plan → build), or when a production signal (incident, metric breach, bug report) needs to be diagnosed and turned into an intent that re-enters the loop. Also use when the user says "let's write an intent for X", "spec this out", "plan mode for X", "diagnose this incident", "help me triage this alert", asks to bootstrap the SDLC structure in a project, or mentions "SDLC playbook" / "AI-native SDLC" / "intent.md" / "spec.md" / "plan.md" in a workflow context.
version: 0.1.0
---

# AI-Native SDLC

Based on Anthropic's [AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook). Every substantial change flows through three markdown artifacts before code is written:

| Stage | Artifact | Answers |
|---|---|---|
| 1 | `intent.md` | Why are we doing this? Who is it for? |
| 2 | `spec.md` | What does "done" look like? What policies constrain it? |
| 3 | `plan.md` | How will the code change? In what order? How do we prove it works? |

**Each stage ends by committing an artifact. The next stage begins by reading it.** The commit chain *is* the audit trail.

## Boundary with related skills

- `writing-plans` / `executing-plans` — a single-plan-document workflow with outputs in `docs/superpowers/plans/`. Different philosophy, different location. Do not confuse them with this skill. If the user is already using `writing-plans`, don't force them onto this one — they can coexist per project.
- `skill-creator`, `command-development`, `agent-development` — for building Claude Code tooling, not for feature planning.

This skill is about the **three-artifact regime**, its **gates**, and its **approval chain**. Outputs live at `docs/sdlc/<feature-slug>/`.

## First time in a project

If `docs/sdlc/README.md` does not exist in the current repo:

1. Run the bootstrap script from the repo root:
   ```
   bash <path-to-this-skill>/scripts/bootstrap.sh
   ```
   (Typical locations: `~/.claude/skills/ai-native-sdlc/scripts/bootstrap.sh` for Claude Code, `~/.codex/skills/ai-native-sdlc/scripts/bootstrap.sh` for Codex, or the equivalent skills directory for your agent.)
2. It seeds `docs/sdlc/README.md`, `docs/sdlc/_templates/`, and appends a section to `AGENTS.md` so **other agents** (Cursor, Codex, Aider, Windsurf) pick up the same spec.
3. The user should review the seeded README and commit: `sdlc: bootstrap docs/sdlc structure`.

If `docs/sdlc/README.md` already exists, skip bootstrapping and jump straight to the stage the user wants.

## The three commands

Each stage has a slash command that invokes the corresponding phase of this skill. The user can also just tell you what they want in natural language ("write an intent for the refund flow") — same effect.

### `/intent <feature-slug>` — draft `intent.md`

**Read** `references/intent-guide.md` before doing anything else. Then:

1. Confirm the slug (kebab-case, matches or will match branch name).
2. Ensure `docs/sdlc/<slug>/` exists.
3. Copy `docs/sdlc/_templates/intent.template.md` to `docs/sdlc/<slug>/intent.md`.
4. Fill sections through conversation with the user — one section at a time, using their words.
5. Update frontmatter (author, date, `status: draft`).
6. Suggest commit: `sdlc(<slug>): add intent.md`.
7. Remind the user: product owner reviews next; **merging = accepting = triggers spec stage**.

Detailed guidance, section-by-section coaching, and failure modes: [`references/intent-guide.md`](references/intent-guide.md).

### `/spec <feature-slug>` — draft `spec.md`

**Read** `references/spec-guide.md` before doing anything else. Then:

1. **Gate check:** open `docs/sdlc/<slug>/intent.md`, verify `status: accepted` in frontmatter. If not, stop and tell the user: "intent is still `draft`; product owner needs to merge it first."
2. Read the accepted intent fully. Open questions become spec obligations.
3. Load organizational policy skills (security, brand, compliance, UX) — see the guide for where to look.
4. Explore relevant code (`Grep`, `Read`, `Explore`) so "Integration with existing code" has real file paths.
5. Copy `docs/sdlc/_templates/spec.template.md` to `docs/sdlc/<slug>/spec.md`.
6. Draft in one pass, then critique. Every open question from intent must be answered here.
7. **Flag concerns honestly** in `Areas of concern`. Do not paper over policy conflicts.
8. Suggest commit: `sdlc(<slug>): add spec.md`.
9. Remind the user: product owner reviews; flagged concerns dispatched to policy owners; **accepting the spec triggers plan mode**.

Detailed guidance: [`references/spec-guide.md`](references/spec-guide.md).

### `/plan <feature-slug>` — draft `plan.md` in plan mode

**Read** `references/plan-guide.md` before doing anything else. Then:

1. **Gate check:** open `docs/sdlc/<slug>/spec.md`, verify `status: accepted`. If not, stop.
2. Re-read `intent.md` (for the *why*) and `spec.md` (for the *what*).
3. Enter plan mode. If your agent has a dedicated plan-mode tool (e.g. Claude Code's `EnterPlanMode`), call it — you get a scratchpad and are prevented from writing files until you exit. If not, operate in read-only exploration mode until the plan is ready to write.
4. Explore the code the spec named. Make sure every file path is real.
5. Draft the plan by talking to the engineer — propose, listen, refine.
6. Copy `docs/sdlc/_templates/plan.template.md` to `docs/sdlc/<slug>/plan.md`.
7. Fill sections. Especially: **Proof** must be specific (which tests, which manual verifications, which rollout gates, which monitoring).
8. Exit plan mode (Claude Code: `ExitPlanMode`; other agents: their equivalent) when the plan is complete.
9. Suggest commit: `sdlc(<slug>): add plan.md`.
10. Remind the user: engineer accepts; **high-risk plans need tech lead / architect signoff** — see the approval matrix; once accepted, implementation begins.

Detailed guidance: [`references/plan-guide.md`](references/plan-guide.md).

## Gate mechanics

Between stages, always check the previous artifact's `status:` field in frontmatter. Only proceed when `status: accepted`.

The user's "accept" action varies by team convention:
- Common: merging the artifact's PR flips `status` to `accepted` and lands it on main.
- Also common: editing `status: draft` → `status: accepted` in a follow-up commit on the same branch.

If unclear, ask the user which convention this repo uses; treat both as valid.

## Approval and escalation

Who reviews what, and when to escalate to tech lead / architect — see [`references/approval-matrix.md`](references/approval-matrix.md). Key rule: any change touching auth, payments, PII, migrations, external contracts, compliance surface, or post-mortem territory is high-risk. Name the escalation target in the artifact's PR description from the start.

## Handoff to build

After `plan.md` is `accepted`:
1. Implementation begins. Code, tests, review, merge follow the team's normal workflow — **not** this skill's job.
2. The implementation PR description **links back to** `docs/sdlc/<slug>/plan.md`.
3. If implementation reveals the plan was wrong, edit `plan.md`, get re-approval, then continue. Silent deviation breaks the audit trail.

## Starting from an incident (Maintain loop)

The three commands assume a fresh idea. When the starting point is a production signal instead — an incident, a metric breach, a user-reported bug — the skill still applies, but the entry is different: the agent **diagnoses read-only** and turns the diagnosis into an `intent.md` that re-enters the loop at Plan. **The agent does not fix code, deploy, or cross any review gate.** The fix goes through the normal spec → plan → build flow like any other change.

Slug convention for incidents: `incident-<YYYY-MM-DD>-<short-desc>` (e.g. `incident-2026-09-01-refund-500s`), which keeps them visually distinct from feature slugs in `docs/sdlc/`.

Full procedure, evidence requirements, and failure modes: [`references/maintain-guide.md`](references/maintain-guide.md).

## When to skip

Not everything needs three artifacts. Skip for typo fixes, dep bumps, docs edits with no policy implication, and reverts. Emergency hotfixes still need retrospective `intent.md` + `spec.md` within one business day. Full skip criteria in `docs/sdlc/README.md`.

If in doubt, write at least an `intent.md`. It's cheap, and the audit trail is worth more than the fifteen minutes.

## Updating this skill

Changing `SKILL.md`, any `references/*-guide.md`, or the `assets/*.template.md` files changes how every project using this skill will run. Treat those edits like code changes to a library:

1. **Before merging the change**, run a small regression by hand: pick 3–5 representative real cases (a feature intent, an incident intent, a spec with policy conflicts, a plan with a migration) and run the affected command against each. Look for behavior drift — has the guide's new wording pushed the agent toward vaguer intents? Does the spec now skip a section it used to fill?
2. **Note the outcome in the commit message** — "verified against: refund-flow, incident-2026-09-01, migration-tenants". This is your audit trail for the skill itself.
3. **If a change relaxes a rule** (e.g. removing a required section), be extra careful — the same case set should still produce artifacts you'd accept.

You do not need a formal eval harness for this. The point is to catch behavior drift before it ships to everyone using the skill, and to make the skill's own quality visible in git history.

## Files in this skill

- `SKILL.md` — this file
- `assets/project-README.md` — the agent-agnostic spec that gets copied to `docs/sdlc/README.md`
- `assets/{intent,spec,plan}.template.md` — the templates
- `assets/AGENTS.md.snippet` — appended to project `AGENTS.md`
- `references/intent-guide.md`, `spec-guide.md`, `plan-guide.md`, `maintain-guide.md` — stage-by-stage deep guidance
- `references/approval-matrix.md` — who reviews what, when to escalate
- `scripts/bootstrap.sh` — seeds `docs/sdlc/` structure and `AGENTS.md` into a project
