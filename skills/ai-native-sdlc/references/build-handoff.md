# Build handoff

Build handoff is the terminal output of this skill. It converts an accepted, current plan into an execution contract for the team's normal implementation workflow; it does not push, merge, deploy, or prescribe an agent roster.

## Preconditions

Before handoff:

1. Run `<skill-dir>/scripts/sdlc-check docs/sdlc/<slug>` successfully.
2. Confirm `plan.md` is `accepted`, its `intent_ref` and `spec_ref` are current, and no unresolved concern blocks implementation.
3. Confirm every requirement maps to an implementation step and proof obligation.
4. Confirm owners and required reviewers are named, especially for high-risk work.

## Required handoff data

The plan's `Build handoff` section names:

- tracking issue or work item;
- implementation owner;
- required reviewers;
- parallel work groups and their interface contracts;
- proof obligations;
- rollout and deployment owner;
- completion evidence expected from the implementation workflow.

The implementation PR or equivalent change record links the accepted `plan.md`. Completion evidence should state what was exercised, its observed result, and any accepted verification gap.

## Drift

If implementation reveals that the accepted plan is wrong, stop at the affected boundary. Reset the plan to `draft`, clear its acceptance fields, update it, and obtain approval again. If the required behavior changes, return to `spec.md`; if the intended outcome changes, return to `intent.md`. Silent deviation breaks the audit trail.
