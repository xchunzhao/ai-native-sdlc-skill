# AI-Native SDLC — Project Spec

This document defines how new feature work is planned and reviewed in this repository. It is **agent-agnostic**: Claude Code, Cursor, Codex CLI, Aider, Windsurf, and human engineers all follow the same rules by reading this file and the templates in `_templates/`.

Based on Anthropic's [AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook).

---

## The Core Idea

Every substantial change goes through three markdown artifacts before code is written:

| Artifact | Answers |
|---|---|
| `intent.md` | Why are we doing this? Who is it for? |
| `spec.md` | What does "done" look like? What policies constrain it? |
| `plan.md` | How will the code change? In what order? How do we prove it works? |

**Each stage ends by committing an artifact. The next stage begins by reading it.** The commit chain *is* the audit trail — who proposed it, what the agent produced, who approved it.

After `plan.md` is accepted, implementation begins. From that point forward, code is the source of truth.

---

## The Three Artifacts

Every feature lives in its own folder under `docs/sdlc/<feature-slug>/`. Use `kebab-case` slugs that match the branch name (e.g. `checkout-refund-flow`).

### `intent.md`

**Answers:** why we're doing this, and for whom.

**Written by:** the initiator (product, engineer, on-call responder) working with Claude or another agent. A monitoring/scanning agent may also auto-draft one when it detects an incident or opportunity.

**Reviewed by:** the product owner.

**Required sections:**
- `Problem` — the concrete user pain or business gap
- `Proposed outcome` — what the world looks like after this ships
- `Affected users and systems` — audience + systems in scope
- `Constraints` — hard limits (time, budget, compliance, technical)
- `Open questions` — what we don't know yet
- `Author + Status` — who wrote it, current state (`draft` / `accepted`)

**Accept action:** the product owner **merges** the PR containing `intent.md` (status flips to `accepted`). This triggers the requirements & design pass (`spec.md`).

### `spec.md`

**Answers:** what the thing should look like, and which policies it must respect.

**Written by:** Claude (or another agent), loading the organization's design/security/brand/compliance/UX skills to generate a spec that reflects real constraints. **The product owner does not draft `spec.md` themselves.**

**Reviewed by:** the product owner. Flagged concerns are dispatched to the relevant **policy owner** (security lead for auth concerns, brand for UX copy, etc.). High-risk work also loops in a **tech lead**.

**Required sections:**
- `Requirements & design spec` — the functional and UX definition of done
- `Integration with existing code` — where this hooks into current systems
- `Policy compliance` — how brand / security / compliance / UX constraints are satisfied, section by section
- `Areas of concern` — anything ambiguous, unresolved, or where policies conflict with each other (call these out explicitly, don't paper over)
- `Author + Status`

**Accept action:** the product owner marks the PR **accepted** (status flips). This triggers plan mode.

### `plan.md`

**Answers:** how the code will change, in what order, and how we'll prove it's right.

**Written by:** Claude in plan mode, in conversation with the engineer.

**Reviewed by:** the engineer. High-risk plans escalate to **tech lead / architect**.

**Required sections:**
- `Files that change` — enumerate the touched files and the nature of each change
- `Order of work` — sequence, with any dependencies between steps
- `Risks` — what could go wrong, what's fragile
- `Proof` — how we'll verify correctness (tests, manual checks, rollout gates, monitoring)
- `Author + Status`

**Accept action:** the engineer marks the plan **accepted**. Claude (or the engineer, or both) begins implementation.

---

## Approval Matrix

| Artifact | Writes | Reviews / Owns | Escalation |
|---|---|---|---|
| `intent.md` | Initiator + agent | Product owner | — |
| `spec.md` | Agent (loading org skills) | Product owner; policy owners for flagged concerns | Tech lead for high-risk |
| `plan.md` | Agent in plan mode + engineer | Engineer | Tech lead / architect for high-risk |

"High-risk" = touches auth, payments, PII, migrations, external contracts, or anything the team has previously written a post-mortem about. When in doubt, escalate.

---

## Naming & Commit Conventions

- Folder: `docs/sdlc/<feature-slug>/`
- Slug: `kebab-case`, matches the git branch name (e.g. branch `feat/checkout-refund` → slug `checkout-refund`)
- One commit per artifact transition, so the audit trail is legible in `git log`:
  - `sdlc(<slug>): add intent.md`
  - `sdlc(<slug>): accept intent.md` (status change)
  - `sdlc(<slug>): add spec.md`
  - `sdlc(<slug>): accept spec.md`
  - `sdlc(<slug>): add plan.md`
  - `sdlc(<slug>): accept plan.md`
- To reconstruct any decision: `git log --follow docs/sdlc/<slug>/` gives you the full chain, and each commit's author is the person who owned that transition.

**Status field:** each artifact's YAML frontmatter carries `status: draft` or `status: accepted`. The next stage must not begin until the prior artifact's status is `accepted` and the commit is on the main branch (or the working branch, if you run the full chain on one branch).

---

## Templates

Copy from `_templates/` when starting a new feature:

- `_templates/intent.template.md`
- `_templates/spec.template.md`
- `_templates/plan.template.md`

Each template has the required sections pre-stubbed with a one-line italic prompt describing what belongs there. Delete the prompts as you fill sections in.

---

## Agent Integration

Any coding agent can follow this spec by reading this file plus the templates. Specific integrations:

- **Claude Code** — install the personal skill at `~/.claude/skills/ai-native-sdlc/` and use `/intent <slug>`, `/spec <slug>`, `/plan <slug>`. The skill loads this file and enforces the gates automatically.
- **Cursor** — add `.cursor/rules/ai-sdlc.mdc` in the repo root with a one-line rule pointing at `docs/sdlc/README.md`. Cursor will read this spec as project context.
- **Codex CLI / Aider / Windsurf** — they read the repo-root `AGENTS.md` automatically. The bootstrapper appends a section pointing at this spec.
- **No agent** — a human engineer can copy templates and fill them in manually. The review flow is identical.

The point is that the *spec* is the same file everyone reads. The tools are just different ways to help fill it in.

---

## When to Skip This

Not every change needs the full three-artifact chain. Skip for:
- Typo fixes, dependency bumps, config nudges, docs edits with no policy implication
- Reverts of a recent change
- Emergency hotfixes (write a **retrospective** `intent.md` + `spec.md` within one business day)

If you're unsure, err toward writing an `intent.md` — it's cheap, and it becomes the artifact everyone else references. The cost of skipping when you shouldn't have (invisible decisions, forgotten context) is much higher than the cost of an extra 15 minutes of writing.

---

## Handoff to Build

Once `plan.md` is `accepted`:
1. Implementation begins. Code, tests, review, merge follow the team's normal workflow.
2. The PR description **links back to** `docs/sdlc/<slug>/plan.md`.
3. If implementation reveals the plan was wrong, don't silently deviate — edit `plan.md`, get re-approval, then continue. The audit trail must reflect reality.

From here on, code is the source of truth. The three markdown artifacts remain as the decision record.
