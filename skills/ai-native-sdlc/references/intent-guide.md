# Intent Guide — writing `intent.md` well

Read this when helping a user draft `intent.md`. Your job is to extract a clear problem statement from the user and shape it into the required sections, not to solutionize.

## Order of operations

1. **Confirm the feature slug.** Kebab-case, matches (or will match) the branch name. If the user hasn't picked one, propose 2–3 and let them choose.
2. **Ensure the folder exists.** `docs/sdlc/<slug>/` — create it if needed.
3. **Check for stage skip.** If the change fits the "when to skip" list in `docs/sdlc/README.md` (typo, dep bump, docs edit, hotfix), tell the user and stop. Don't push heavyweight process onto trivial changes.
4. **Copy the template.** `cp docs/sdlc/_templates/intent.template.md docs/sdlc/<slug>/intent.md`
5. **Fill sections through conversation.** Ask the user one section at a time. Prefer their words over your paraphrase — they know the problem.
6. **Update frontmatter.** Author, date, `status: draft`.
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

### Author + Status
- Author = the initiator. If a scanning/monitoring agent drafted this, note the agent + the human it's for.
- Status starts `draft`. Never mark `accepted` yourself — that's the product owner's action, expressed by merging.

## Common failure modes

- **Solutioning too early.** If the intent already names specific components ("a new endpoint at `/api/refund/v2`"), it's actually a spec. Push the specificity into the spec stage.
- **Vague outcome.** "Improve UX" is not an outcome. Ask "improved how? measured how?"
- **Missing evidence.** No ticket, no metric, no quote → intent may be premature.
- **Hidden constraint.** The user knows something (a legal requirement, a manager's mandate) but hasn't said it. Ask "is there anything that would cause this to be rejected outright?"

## When to stop and hand off

- All required sections filled with real content (not `_italic stub prompts_`)
- Frontmatter complete
- User has committed the file
- Remind the user: **product owner reviews next; merging the PR = accepting = triggers spec stage.**
