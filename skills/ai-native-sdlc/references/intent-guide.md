# Intent Guide — writing `intent.md` well

Read this when helping a user draft `intent.md`. Your job is to extract a clear problem statement from the user and shape it into the required sections, not to solutionize.

## Order of operations

1. **Confirm the feature slug.** Kebab-case, matches (or will match) the branch name. If the user hasn't picked one, propose 2–3 and let them choose.
2. **Ensure the folder exists.** `docs/sdlc/<slug>/` — create it if needed.
3. **Check for stage skip.** If the change fits the "When to skip" list in this skill's `SKILL.md` (typo, dep bump, docs edit, hotfix), tell the user and stop. Don't push heavyweight process onto trivial changes.
4. **Read the intent template from this skill.** Do not copy it into the project's `docs/sdlc/`. The template lives in this skill's `assets/intent.template.md`; use your agent's file-read tool to load it, then write the filled version straight to `docs/sdlc/<slug>/intent.md`. This keeps the skill as the single source of truth — when the template evolves, all projects inherit the change on the next session.
5. **Fill sections through conversation.** Ask the user one section at a time. Prefer their words over your paraphrase — they know the problem.
6. **Set frontmatter.** Author, date, risk, reviewers, `status: draft`; leave `accepted_by` and `accepted_at` empty.
7. **Suggest a commit.** `sdlc(<slug>): add intent.md`

## Section-by-section coaching

### Problem
- Push for the **user's** pain, not the engineering pain. "Our refund service is slow" is engineering framing. "Customers wait 8 minutes for a refund status update, then call support" is user framing.
- Get one piece of evidence: a ticket number, a metric, a quote. If the user can't cite anything, ask "how do we know this is real?"
- If the answer is "someone said we should", flag it — the intent may not be well-founded yet.

### Proposed outcome
- Ban feature lists. If the user says "add a refund button", ask "and then what changes for the customer?"
- The outcome should be **observable** — a metric moves, a support volume drops, a compliance box gets checked.
- Do not include how you'll build it. That's for the spec.

### Affected users and systems
- Users: named personas or roles, not "everyone". If it's genuinely everyone, say so.
- Systems: name the modules/services in the codebase. If you don't know the codebase yet, ask the user or run a quick `Grep`/`Read` pass.

### Constraints
- Distinguish hard from soft. "Must ship by Q4" is often soft; "must not store card numbers" is hard.
- Include the ones already implicit in the codebase (e.g. "single-region deploy, no new dependencies without approval").

### Open questions
- Actively **create** open questions. If the user says the intent is fully clear, that's usually a sign they haven't stress-tested it. Ask "what happens if X?" until you find at least one real question.
- Bad open question: "should we build this?" (that's what the intent itself is asking)
- Good open question: "do refunds under $50 need managerial approval, or is that a per-tenant setting?"

### Approval metadata
- Author is the initiator. If a monitoring agent drafted this, name the agent and the human incident owner.
- Risk follows `approval-matrix.md`; high-risk work names additional reviewers from the start.
- Status starts `draft`. A human product owner records `accepted_by` and `accepted_at` in the acceptance commit; never accept your own artifact.

## Common failure modes

- **Solutioning too early.** If the intent already names specific components ("a new endpoint at `/api/refund/v2`"), it's actually a spec. Push the specificity into the spec stage.
- **Vague outcome.** "Improve UX" is not an outcome. Ask "improved how? measured how?"
- **Missing evidence.** No ticket, no metric, no quote → intent may be premature.
- **Hidden constraint.** The user knows something (a legal requirement, a manager's mandate) but hasn't said it. Ask "is there anything that would cause this to be rejected outright?"

## When to stop and hand off

- All required sections contain real content, with no template prompts remaining
- Frontmatter passes `<skill-dir>/scripts/sdlc-check` structural validation
- The draft is committed
- Remind the user: the product owner reviews next; acceptance evidence and the accepted commit unlock spec.
