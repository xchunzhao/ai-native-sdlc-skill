---
artifact: intent
feature: incident-2026-09-01-checkout-500s
author: eval-run
status: draft
created: 2026-09-01
risk: high
reviewers:
  - incident-owner
  - tech-lead
accepted_by:
accepted_at:
---

# Intent — Checkout 500s during flash-sale coupon campaign (P1, 2026-09-01)

> **This intent is a diagnosis, not a fix.** It re-enters the AI-native SDLC loop at the
> normal `spec.md` → `plan.md` → build stages. No production code, config, or
> infrastructure has been changed as a result of writing this document. The temporary
> mitigation (ops disabling the flash-sale coupon at 14:47 UTC) is out of scope for this
> artifact; this intent covers the structural follow-up.

## Problem

Between **14:02 UTC and 14:47 UTC on 2026-09-01**, the checkout endpoint returned HTTP
500s intermittently to real customers (P1 incident). Evidence:

- **Sentry** — traceback consistently points at `CouponService#apply`, raising a nil /
  `NoMethodError`-class failure on `code.expires_at`. This indicates a code path in
  `CouponService#apply` that dereferences `code.expires_at` without first checking that
  `code` was successfully loaded (i.e. the lookup returned `nil` and the caller did not
  guard against it).
- **Datadog** — latency on the `coupons-db` read replica spiked starting **13:58 UTC**,
  three minutes after the marketing team's flash-sale campaign went live at **13:55 UTC**,
  and roughly four minutes before checkout errors began surfacing at 14:02 UTC.
- **Deploy timeline** — no application deploy since the previous morning. The proximate
  trigger is therefore not a code change; it correlates with the flash-sale campaign
  going live and the coupons-db read-replica degrading under the resulting load.
- **Mitigation** — ops disabled the flash-sale coupon at 14:47 UTC and checkout errors
  stopped, which is consistent with the flash-sale coupon (and its lookup traffic
  against the degraded replica) being on the failing path.

**Working hypothesis (to be confirmed in spec):** the flash-sale campaign drove a burst
of coupon lookups against `coupons-db`'s read replica; replica latency degraded and some
coupon reads either timed out or returned no row; `CouponService#apply` treated the
missing row as if the record existed and called `code.expires_at` on `nil`, raising
inside the checkout request and surfacing as a 500. The incident stopped when the
underlying coupon was disabled, not because the defect was fixed — the same class of
failure will recur the next time a coupon lookup returns nil under load.

## Proposed outcome

- Checkout 500 rate returns to and stays at baseline (pre-13:58 UTC levels) for at least
  24h under normal traffic **and** under a comparable flash-sale event.
- A missing / unreadable coupon record can never cause a 5xx on checkout; the customer
  experiences the coupon as invalid (or the checkout proceeds without it, per product
  decision made in spec), never as a failed order.
- The next flash-sale campaign can go live without a coupons-db read-replica latency
  spike large enough to cascade into checkout errors — or, if such a spike is
  unavoidable, checkout degrades gracefully rather than 500-ing.

Explicitly **not** part of the outcome: any specific fix (nil-guard, retry, circuit
breaker, cache, replica sizing). Those are design decisions for `spec.md` / `plan.md`.

## Affected users and systems

- **Users:** every customer attempting checkout between 14:02 and 14:47 UTC on
  2026-09-01 who hit the failing branch — exact impacted-order count TBD from
  order-service and Sentry event volume (see open questions).
- **Systems in scope for diagnosis:**
  - `CouponService#apply` (site of the nil dereference on `code.expires_at`).
  - The checkout request path that calls `CouponService#apply` (error propagation and
    HTTP status mapping).
  - `coupons-db` read replica (latency spike; whether reads are timing out, returning
    empty, or being routed off the replica).
  - The flash-sale coupon lookup path — application-level caching, if any.
- **Upstream / adjacent (named so scope is honest, not necessarily to be fixed):**
  - Marketing's flash-sale campaign tooling — it is the traffic source that exposed the
    defect; a change in how campaigns are launched (warmup, staged rollout) may or may
    not be part of the fix.
  - Ops runbook for disabling a coupon — worked as mitigation; may inform spec's
    rollback story.

## Constraints

- **Audit trail must remain intact.** No code, config, or infra change is made in this
  intent; the fix goes through the normal spec → plan → build → review flow.
- **Data integrity.** Any spec-phase design that reprocesses or retries checkout must
  not double-charge, double-apply a coupon, or issue duplicate orders. Coupons are
  redemption-limited (assumption to confirm in spec) — a naive retry could over-redeem.
- **Customer-visible behavior on invalid coupon** is a product decision, not a purely
  technical one: silently drop the coupon vs. surface "coupon invalid" vs. fail the
  order. Spec must name the product owner.
- **No deploy freeze known**, but any fix that changes checkout behavior is
  payments-adjacent and therefore high-risk under the approval matrix — expect tech
  lead / architect signoff on `plan.md`.
- **Mitigation is fragile.** The flash-sale coupon remains disabled; leaving it
  disabled indefinitely is a business cost. This bounds how long the incident can sit
  in `draft` before spec work must start.

## Open questions

- What exactly does the `coupons-db` read replica return during the latency spike —
  timeouts, empty result sets, or stale reads? (Determines whether the fix is a
  nil-guard, a timeout handler, a retry, or all three.)
- Is `code` in `CouponService#apply` nil because the DB call returned no row, because
  the ORM raised and was rescued upstream, or because the code path constructs it
  optimistically before validating? (Requires reading `CouponService#apply` and its
  callers — spec-phase work.)
- How many orders / customers actually failed checkout between 14:02 and 14:47 UTC?
  (Needed for blast-radius reporting and to prioritize a customer-comms follow-up.)
- Should invalid / unresolvable coupons cause checkout to fail loudly, drop silently,
  or fall back to no-discount? (Product decision, owner to be named in spec.)
- Is the flash-sale coupon lookup path cache-eligible, and would caching have prevented
  the replica hot-spot? (Design option for spec, not a foregone conclusion.)
- Was the read-replica latency spike caused purely by campaign volume, or is there a
  slow query / missing index on the coupon lookup? (Datadog query profiler + `EXPLAIN`
  in spec phase.)
- Are there other services reading from the same `coupons-db` replica that also
  degraded but didn't surface as user-visible errors? (Bounds whether the fix is
  checkout-local or platform-wide.)
- Do we need a retrospective post-mortem doc separate from this SDLC chain, or does the
  intent → spec → plan chain serve as the post-mortem record for this team?

