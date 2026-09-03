# Artifact lifecycle

The artifact chain is a state machine, not a naming convention. `schemas/artifact.schema.json` defines frontmatter shape; `schemas/lifecycle.yaml` defines transitions and dependencies; `<skill-dir>/scripts/sdlc-check` enforces both against repository history.

## States

- `draft` — editable, not approved, and cannot unlock the next stage.
- `accepted` — approved by the named human at `accepted_at`; unlocks the next stage while its accepted revision remains current.
- `rejected` — declined; return it to `draft` before editing toward another review.
- `stale` — previously accepted, but its own content or an accepted dependency changed.
- `superseded` — permanently replaced; `superseded_by` identifies the replacement.

Allowed transitions are `draft → accepted|rejected`, `rejected → draft`, `accepted → stale|superseded`, and `stale → draft|superseded`. A semantic edit to an accepted artifact is never still accepted: reset it to `draft`, clear the acceptance fields, and obtain approval again.

## Revision linkage

A spec records the full Git commit of the accepted intent in `intent_ref`. A plan records both `intent_ref` and `spec_ref`. The referenced commit must contain the corresponding artifact with `status: accepted`.

If the latest commit touching an upstream artifact differs from the recorded reference, its dependants are stale:

- changed intent invalidates spec and plan;
- changed spec invalidates plan;
- changed accepted plan invalidates its build handoff.

Do not silently update a reference. Re-read the changed upstream artifact, reconcile the downstream document, reset the downstream status to `draft`, and send it through review again.

## Acceptance evidence

Only a human owner accepts an artifact. `accepted_by` and `accepted_at` are required for `accepted`, `stale`, and `superseded` artifacts so later states retain the original approval evidence. High-risk artifacts must name their additional reviewers in `reviewers`.

Run `<skill-dir>/scripts/sdlc-check <project-or-feature-path>` before advancing a stage or handing a plan to implementation.
