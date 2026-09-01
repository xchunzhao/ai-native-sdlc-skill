# Plan Guide — writing `plan.md` well

Read this when the user runs `/plan <feature-slug>`. This stage runs in **plan mode** — a conversation between Claude and the engineer that ends with an accepted implementation plan.

## Order of operations

1. **Verify the gate.** Open `docs/sdlc/<slug>/spec.md` and check `status: accepted`. If not, stop and tell the user "spec is `draft`; needs product owner acceptance first."
2. **Read the spec fully.** Every section, especially "Areas of concern" — unresolved concerns become plan risks.
3. **Also re-read intent.md.** You want the *why* fresh in your head while planning the *how*.
4. **Enter plan mode.** If your agent has a dedicated plan-mode tool (Claude Code's `EnterPlanMode`, or an equivalent in your agent), call it — this gives you a scratchpad and prevents accidental writes until you explicitly exit. If your agent has no such tool, operate in read-only exploration mode: read files, don't write anything, only produce the plan document at the end.
5. **Explore the code.** Use `Read`, `Grep`, `Explore` subagents to understand every file the spec's "Integration with existing code" section named. If the spec was vague, this is where you get concrete.
6. **Draft the plan by talking to the engineer.** Not in one shot. Propose a section, ask if the engineer sees issues, refine. This is the point of plan mode.
7. **Read the plan template from this skill and write to place.** Do not copy the template into the project. The template lives in this skill's `assets/plan.template.md`; load it with your agent's file-read tool, then write the filled version straight to `docs/sdlc/<slug>/plan.md`.
8. **Write the plan.** Exit plan mode (in Claude Code, `ExitPlanMode`) when the plan is complete.
9. **Suggest a commit.** `sdlc(<slug>): add plan.md`

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

- All sections filled with concrete content
- Engineer has reviewed and agrees with the sequence, risks, and proof approach
- Frontmatter complete
- File committed
- Remind the user: **engineer accepts (marks `status: accepted`); high-risk plans need tech lead / architect signoff first; once accepted, implementation begins.**
