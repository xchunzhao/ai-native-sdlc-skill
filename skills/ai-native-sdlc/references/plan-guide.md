# Plan Guide — writing `plan.md` well

Read this when the user asks to draft `plan.md`. This stage runs in plan mode: a conversation with the engineer that ends in a reviewable implementation plan and, after human acceptance, a build handoff.

## Order of operations

1. **Verify the gate.** Run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>`, verify spec and intent are accepted and current, and record their full commits as `intent_ref` and `spec_ref`.
2. **Read spec and intent fully.** Unresolved concerns become plan risks; keep the intended outcome fresh while planning implementation.
3. **Enter plan mode.** Use the host's plan mode when available; otherwise remain read-only until writing the final plan.
4. **Explore the code.** Read every integration point named by the spec and verify every planned path.
5. **Draft with the engineer.** Propose, listen, and refine rather than presenting a one-shot plan.
6. **Write the plan from the skill template.** Include requirement traceability and complete build-handoff ownership; do not copy the template into the project.
7. **Commit the draft.** Suggest `sdlc(<slug>): add plan.md`.

## Section-by-section guidance

### Files that change
- Enumerate real paths. If you haven't verified a path exists, `Read` or `Grep` first.
- For each: what changes (add function, extend type, wire route, add test). Not a full diff — a sentence of intent per file.
- **Pattern shortcuts:** if 30 test files get the same one-line change, describe the pattern once and cite 2–3 representative paths. Don't list all 30.
- If a new file is added, say what belongs in it, one line.

### Order of work
- Sequence is not just aesthetics — it protects against half-broken intermediate states.
- Data model migrations run first, so subsequent code can rely on them.
- Feature-flagged code paths land before wiring, so nothing goes live before review.
- Note dependencies explicitly. "Step 3 depends on step 1 being deployed; can be parallel with step 2."
- If the sequence has parallel branches (e.g. two engineers on two subsystems), draw it plainly.

### Risks
- Include the engineer's "gut feel" risks alongside your own. Ask them: "what would you regret not naming?"
- For each risk, three things: likelihood, blast radius, mitigation.
- Blast radius matters more than likelihood — a rare event with a large blast is worse than a common event you'll notice immediately.
- Migration risks, external-contract risks, and race conditions are frequently under-called. Look for them explicitly.

### Proof
- **Not just "add tests".** Be specific: which tests, at what level, testing what.
- Unit tests verify functions; integration tests verify contracts; e2e tests verify user flows. Say which layer catches which failure mode.
- Manual verification: if a step can't be automated, write the exact click-path with expected outputs.
- Rollout gates: feature flag name, staged rollout %, kill switch. If none of those apply, say so and why.
- Monitoring: name the metric, the alert, the dashboard. If none exist and this change needs one, add "wire the metric" as a step in Order of work.
- Rollback plan: how would you detect a bad deploy? How do you undo it?

## When plan mode should push back

- The spec is silent on something you must decide. Don't invent — go back to the spec, or the engineer, or (if it's a policy question) the product owner.
- The engineer wants to skip verification steps. Push back: what evidence will convince us this is right?
- The engineer wants to bundle unrelated cleanup. Push back: separate PR, separate plan, or explicit note in "Files that change" that this is unrelated cleanup you're piggybacking.

## Common failure modes

- **Files list without changes.** Every file needs its "what changes" phrase. A bare list is useless in review.
- **Order that ignores dependencies.** Migrations after code, or wiring before feature-flag guards. Draw the dependency graph mentally.
- **Vague proof.** "Add tests" is not proof. Which tests, testing what, verifying which behavior.
- **No rollback thinking.** If the plan doesn't say how you'd back out, the plan isn't done.
- **Plan drifting into spec territory.** If you find yourself re-negotiating what the feature is, stop — go back to the spec stage.

## When to stop and hand off

- All sections contain concrete content
- Every accepted spec requirement maps to an implementation step and proof
- Owners, required reviewers, and tracking item are named
- `intent_ref` and `spec_ref` match the current accepted commits
- The draft is committed and `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>` succeeds
- Engineer acceptance records `accepted_by` and `accepted_at`; high-risk plans obtain tech lead or architect signoff before build handoff.
