---
artifact: plan
feature: <feature-slug>
author: <engineer-name>
status: draft
created: <YYYY-MM-DD>
intent_ref: <accepted-intent-commit-sha>
spec_ref: <accepted-spec-commit-sha>
risk: <low|medium|high>
reviewers: []
accepted_by:
accepted_at:
---

# Plan — <feature name>

_Prerequisite: `spec.md` in this folder must be `status: accepted` before this plan is drafted._

## Files that change

_Enumerate the touched files. For each, one line on the nature of the change. If a pattern repeats across many files, describe the pattern once and list a few representative paths — do not enumerate every line number._

| File | Change |
|---|---|
| `path/to/file.ts` | _e.g. add `RefundService.processRefund` calling the ledger client_ |
| `path/to/other.ts` | _e.g. wire the new endpoint into the router_ |

## Order of work

_The sequence in which changes are made, and any dependencies between steps. If some steps can be done in parallel, say so. If a step must land before another can begin (e.g. a migration precedes a code change), call it out._

1. _Step 1 — what and why_
2. _Step 2 — what and why_
3. _..._

## Risks

_What could go wrong. What's fragile. What might we have missed? Include the "unknown unknowns" the engineer flagged during plan mode — better to name them than pretend they aren't there._

- _Risk 1 — likelihood, blast radius, mitigation_
- _Risk 2 — likelihood, blast radius, mitigation_

## Proof

_How we'll verify the change is correct. Not just "add tests" — name the specific verifications:_
- _Which unit / integration / e2e tests are added or modified_
- _Manual verification steps (with expected outputs)_
- _Rollout gates (feature flag, staged rollout, kill switch)_
- _Monitoring / alerts that must exist before this is considered done_
- _How we'd detect and roll back a bad deploy_

## Requirement traceability

| Requirement | Implementation step | Proof |
|---|---|---|
| `<requirement-id>` | <ordered step> | <specific automated or manual evidence> |

Every requirement in the accepted spec must map to implementation work and proof. A work item without a requirement is scope expansion; a requirement without proof is not ready for handoff.

## Build handoff

- **Tracking issue:** <issue or work-item URL>
- **Implementation owner:** <name or role>
- **Required reviewers:** <names or roles>
- **Parallel work groups and interface contracts:** <groups, dependencies, and stable boundaries>
- **Proof obligations:** <tests, smoke checks, rollout gates, and monitoring evidence>
- **Rollout owner:** <name or role>
- **Deployment owner:** <name or role>
- **Completion evidence:** <what the implementation workflow must report>

_Handoff is valid only while this plan and its referenced intent/spec revisions remain current. See `references/build-handoff.md`._
