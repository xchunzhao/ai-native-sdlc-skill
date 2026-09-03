# Spec Guide — writing `spec.md` well

Read this when the user asks to draft `spec.md`. Translate the accepted `intent.md` into a design that reflects organizational policies. The product owner reviews the result; the agent drafts it.

## Order of operations

1. **Verify the gate.** Run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>`, verify intent is accepted and current, then record its full accepted commit as `intent_ref`. If the check fails, stop and resolve the lifecycle error.
2. **Read the intent fully.** Every section. Look for `Open questions` — those are things the spec must answer.
3. **Load organizational policy skills.** Look for skills, agent configs, or repo docs that encode brand / security / compliance / UX rules. Common places:
   - Your agent's personal skills directory (e.g. `~/.claude/skills/` for Claude Code, `~/.codex/skills/` for Codex) for skills covering these areas
   - Repo-level skills directory (e.g. `.claude/skills/`, `.codex/skills/`) or `docs/policies/`
   - `AGENTS.md` and its linked docs
   - CLAUDE.md files at repo root and in relevant subdirectories
   If the org has a **security-review**, **frontend-design**, or **compliance** skill, load it now.
4. **Explore relevant code.** Use `Grep`/`Read`/`Explore` to understand where this hooks in. The "Integration with existing code" section requires actual file paths.
5. **Read the spec template from this skill.** Do not copy it into the project. The template lives in this skill's `assets/spec.template.md`; use your agent's file-read tool to load it, then write the filled version straight to `docs/sdlc/<slug>/spec.md`.
6. **Draft in one pass, then critique.** Fill every section from your understanding, then re-read looking for gaps. Especially: does every open question from the intent get answered here?
7. **Flag concerns honestly in `Areas of concern`.** Do not paper over conflicts. If security says one thing and UX wants another, name both and identify the policy owners.
8. **Set frontmatter and commit.** Preserve `intent_ref`, classify risk, name reviewers, leave acceptance fields empty, and suggest `sdlc(<slug>): add spec.md`.

## Section-by-section guidance

### Requirements & design spec
- Concrete enough that an engineer could plan implementation from this alone. If your spec would leave the engineer asking "but what does it *look* like?" or "what's the exact API shape?", add more detail.
- Include payload examples inline for API changes. Include ASCII sketches or references to Figma / mockups for UI.
- **Out of scope** is not optional — bound the work explicitly so scope creep is visible.

### Integration with existing code
- Name real modules, real files, real functions. Do the exploration; don't hand-wave.
- If integration forces changes to adjacent code (e.g. a shared type gets extended), call it out. The engineer needs to know.
- If a new abstraction is needed, justify it. Prefer reusing what exists.

### Policy compliance
- One subsection per area (Brand, Security, Compliance, UX). Do all four even when short.
- Reference the specific guideline you loaded. "Follows the design system's `Button` primitive" is stronger than "matches brand".
- If a policy area doesn't apply, say so and why. Silence looks like an oversight.
- **If a policy area clearly applies but the org has no corresponding skill or doc loaded**, do not silently move on. Write "no <area> skill/doc detected — manual confirmation required from <role>" in the subsection, and add a matching entry in `Areas of concern` so the product owner routes it. Absence must be visible, not silent — the risk is a spec that reads "compliant" because no policy was checked.

### Areas of concern
- **This is the most important section.** It's where you're honest about ambiguity.
- Every open question from the intent that isn't fully resolved goes here.
- Every place two policies conflict — even mildly — goes here. Explicit conflicts get sent to the right policy owners; hidden conflicts blow up in code review or, worse, in production.
- Format: `- Concern (owner: <role>) — description`. The owner is who the product owner will loop in.

## When Claude should refuse to draft

- Intent is not `accepted` yet — direct user to fix that first.
- Intent is missing required sections — refuse to draft on a broken intent; help fix the intent first.
- The change is genuinely too small for this process (see "When to skip" in this skill's `SKILL.md`).

## Common failure modes

- **Skipping policy sections.** Every subsection under "Policy compliance" needs a real answer, even "N/A because <reason>".
- **Vague integration.** "Integrates with the checkout flow" — no. Name files. If you don't know, `Grep` or ask.
- **Suppressing concerns.** If you notice a policy conflict and don't write it down because "it's probably fine", you're doing the process wrong. The concern belongs in the doc; the resolution belongs to the policy owner.
- **Doing the plan.** The spec says *what* and *why*; the plan says *how* and *in what order*. If you find yourself listing files to change, stop — you're one stage ahead.

## When to stop and hand off

- All sections filled, no template prompts remaining
- Every intent open question is resolved or owned in `Areas of concern`
- Frontmatter includes the current accepted `intent_ref`, risk, and reviewers
- The draft is committed and `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>` succeeds
- Product owner reviews next; policy owners resolve flagged concerns; acceptance evidence unlocks plan.
