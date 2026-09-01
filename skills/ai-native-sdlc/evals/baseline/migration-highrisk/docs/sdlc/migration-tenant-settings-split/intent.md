---
artifact: intent
feature: migration-tenant-settings-split
author: eval-run
status: draft
created: 2026-09-01
---

# Intent — Split `tenants.settings` JSONB into a first-class `tenant_settings` table

> **High-risk escalation.** This work touches three of the trigger categories in the
> approval matrix at once: **PII surface** (`pii_export_policy`), a
> **schema migration + backfill** on a top-level tenant table, and **cross-team
> ownership** of individual keys inside the blob. Per the approval matrix, the
> intent PR is reviewed by the product owner, and the spec/plan PRs will require
> **tech lead (and architect, for the migration cutover strategy) signoff** in
> addition to the policy owners named below. Naming the escalation now so it is
> not surfaced late.

## Problem

Every setting a tenant owns lives inside a single `tenants.settings` JSONB column.
That column started with a handful of keys and has grown to **40+**. Any admin
dashboard query that filters or sorts by a settings key now falls back to a
JSONB GIN scan, and p99 latency on the admin dashboard is being driven by those
scans — the on-call rotation has been citing the admin dashboard as the top
p99 offender in weekly reviews. The blob has also become an ownership hazard:

- `settings.pii_export_policy` — governs what personally identifiable fields
  can leave the system in an export. **Owned by the compliance team**, who
  audit it quarterly.
- `settings.billing_defaults` — default currency, tax handling, invoice cadence.
  **Owned by the finance team.**
- `settings.feature_flags.*` — a sub-object written to by essentially every
  product team.

Because the three live under one column, we can't grant row/column-level
permissions per owner, we can't cleanly audit changes per key, and any team
writing to `feature_flags` is one bad merge away from clobbering a compliance
or finance key. The performance pain is what forced this onto the roadmap;
the ownership pain is what makes it worth doing properly.

## Proposed outcome

After this ships, the observable end state is:

- Admin dashboard p99 on settings-filtered queries drops off the top of the
  weekly latency review (target: back to the pre-blob baseline; exact number
  is a spec-stage question).
- Every settings key has a single, queryable owner recorded in the schema —
  compliance-owned keys are auditable independently of finance-owned keys and
  team-owned feature flags.
- Reads and writes against `pii_export_policy` produce a clean audit trail
  that the compliance team can pull without JSONB spelunking, satisfying their
  quarterly audit.
- No tenant experiences a settings-visible regression during or after the
  cutover (no lost values, no stale reads past a bounded cutover window).

_How_ we get there — dual-write vs. shadow-read vs. big-bang cutover, backfill
strategy, whether the old JSONB column stays as a read fallback, exact table
shape — is deliberately **out of scope for this intent** and will be decided
in `spec.md` / `plan.md`.

## Affected users and systems

**Users / roles who feel the change:**

- **Admin-dashboard operators** (internal) — direct beneficiaries of the p99
  improvement.
- **Compliance team** — new owners-of-record for the `pii_export_policy`
  surface; will review the migration and the resulting per-key audit story.
- **Finance team** — new owners-of-record for the `billing_defaults` surface.
- **Every product team writing `feature_flags`** — their write path changes;
  needs a coordinated cutover so no team is silently broken.
- **Tenants** — no user-visible change if we do this right; a settings-loss
  incident if we don't.

**Systems in scope (initial map; spec will confirm):**

- `tenants` table — source of the current JSONB column.
- Admin dashboard service — primary reader/query surface driving p99.
- Any service that writes `settings.feature_flags.*` — needs an inventory,
  which is itself a spec-stage task.
- Compliance export pipeline (reads `pii_export_policy`).
- Billing/invoicing service (reads `billing_defaults`).
- Migration + backfill tooling (new).

## Constraints

**Hard:**

- **Zero PII regression.** No path in which `pii_export_policy` is read from a
  stale source, defaulted, or silently dropped during cutover — compliance
  will veto anything that risks that.
- **No lost writes.** During cutover, any write accepted by the API must land
  in the new table (and the old column, if we run dual-write); no
  fire-and-forget.
- **Rollback plan required.** Migration is high-risk category; per the
  approval matrix we need a rollback story before the plan is accepted, not
  after.
- **Audit trail preserved.** Compliance's quarterly audit of
  `pii_export_policy` must be possible for the current quarter — the cutover
  cannot leave a gap that the auditors can't trace across.

**Soft (to confirm in spec):**

- Target the next sprint (as raised by the requester) — negotiable if the spec
  surfaces material risk that needs more runway.
- Prefer no new services / no new infra dependencies; solve inside the
  existing Postgres and the existing services if we can.

## Open questions

These are intentionally spec-stage questions. The intent does **not** try to
answer them; naming them here so the spec reviewer can see what's still open.

- **Ownership model.** How do we encode per-key ownership in the new schema so
  compliance and finance can review changes to their keys independently?
  (Separate tables per owner? One table with an `owner` column and per-owner
  RLS? A view layer per owner?)
- **PII surface boundary.** Should `pii_export_policy` live in a physically
  separate table (or even schema) from other settings, to make row-level
  security and compliance audit trivial? Compliance's answer here likely
  drives the shape of the whole migration.
- **Feature-flag writer inventory.** Which services write to
  `settings.feature_flags.*` today, and how do we coordinate their cutover
  without a flag day?
- **Cutover strategy.** Dual-write with shadow read, backfill-then-swap, or
  something else? What is the bounded window in which stale reads are
  tolerable, and what does compliance say about that window for
  `pii_export_policy`?
- **Backfill correctness.** How do we prove — not assert — that the backfill
  copied every key for every tenant, including keys we didn't know existed
  (schema-less JSONB will surprise us)?
- **Rollback.** If we detect corruption after cutover, can we roll back to the
  JSONB column, and for how long do we keep it live as a fallback?
- **Latency target.** What is the concrete p99 number we're committing to on
  the admin dashboard? Product owner + on-call to set.
- **Sequencing vs. the sprint.** Given the escalation footprint (compliance,
  finance, tech lead, architect), is one sprint realistic, or does the spec
  need to propose a phased plan?

## Author + Status

- **Author:** eval-run (drafted on behalf of the requesting engineer)
- **Status:** `draft` — flip to `accepted` when the product owner merges this
  artifact.
- **Reviewers (per approval matrix):**
  - **Primary:** product owner.
  - **Policy owners (surfaced now so spec can dispatch cleanly):**
    - **Compliance lead** — owner of `pii_export_policy`, PII surface, and the
      quarterly audit obligation.
    - **Finance lead** — owner of `billing_defaults`.
  - **Escalation (named up front, per the high-risk rule):** tech lead for the
    migration + cross-team-ownership surface; architect for the cutover
    strategy across services that write `feature_flags`.
