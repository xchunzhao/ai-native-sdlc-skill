---
artifact: intent
feature: refund-flow-v2
author: eval-run
status: draft
created: 2026-09-01
risk: high
reviewers:
  - product-owner
  - finance-lead
  - tech-lead
accepted_by:
accepted_at:
---

# Intent — Refund flow v2 (own ledger, partial refunds, 12-month window)

## Problem

Refunds today run through a legacy Stripe integration that mis-records partial refunds and hard-caps the refund window at Stripe's 90-day limit. When CX issues a $20 refund against a $50 charge, the ledger entry is written for the full $50, so month-end reconciliation is broken — finance manually adjusts roughly **30 entries per month**. The 90-day cap also drives an ongoing stream of "why can't you refund me?" tickets from customers past that window, which CX has to escalate one-by-one. This is a recurring, quantified pain owned jointly by CX and Finance, not a hypothetical.

## Proposed outcome

- Partial refunds land in our ledger at the **actual refunded amount**, so month-end reconciliation runs clean with no manual adjustments (target: the ~30/month finance rework goes to zero).
- Customers past the 90-day Stripe window can still be made whole — via **store credit** issued from our own refund ledger — up to **12 months** from the original charge.
- CX can resolve a partial or late refund in a single flow in the admin surface, without escalating to finance.
- SOC2-relevant refund activity is fully auditable: who initiated, when, amount, original charge, method (cash-back vs. store credit), and outcome — every row traceable end-to-end.

## Affected users and systems

**Users**
- **CX agents** — primary operators; issue refunds and store credit from the React admin.
- **Finance / accounting** — consume the ledger for month-end reconciliation; biggest beneficiary of the fix.
- **Customers** — receive correct partial refunds and can be made whole in the 90-day–12-month window (via store credit).
- **Auditors** — will read the refund audit trail during the Q2 SOC2 audit.

**Systems** (Rails 7 monorepo + React admin)
- Legacy Stripe refund integration (to be superseded, at least for the ledger write path).
- New **refund ledger** (own service / module inside the Rails monorepo) — source of truth for refund amounts and state.
- **Store credit** subsystem (new or extended) for 90+ day cases.
- React admin refund UI (partial refund entry, store credit issuance, refund history view).
- Audit log / SOC2 evidence pipeline.
- Any downstream consumers of today's refund ledger entries (finance exports, reporting) — to be identified in spec.

## Constraints

**Hard**
- **SOC2 audit in Q2** — the audit trail for refunds (initiator, amount, timestamp, linkage to original charge, method) must be complete and immutable before audit fieldwork begins.
- Must not regress existing full-refund behavior for in-window (<90 day) cash refunds during rollout.
- No storing card data beyond what Stripe already tokenizes; refund ledger holds amounts + references, not PANs.
- Store-credit balances must be reconcilable against the ledger (no silent liability).

**Soft**
- Prefer staying inside the Rails 7 monorepo — no new services unless spec justifies it.
- Prefer extending the existing admin surface over introducing a new one for CX.
- Rollout should be reversible (feature flag or equivalent) given the finance blast radius.

## Open questions

- Do we keep Stripe as the money-movement rail for in-window cash refunds and only replace the **ledger** layer, or do we also swap the rail? (Scope-defining — spec must decide.)
- Where does the 12-month window start counting: original charge date, capture date, or invoice date? (Finance likely has an opinion.)
- What's the store-credit expiration policy, if any? Does unused store credit ever revert to a refund, escheat, or expire?
- Are partial refunds allowed to be issued in multiple installments against the same charge (e.g. $10 today, $15 next week against the same $50), and if so what's the aggregate cap — the original charge amount, or something lower?
- Does store credit require any managerial approval threshold (e.g. > $X), or is it fully CX-agent-authorized?
- How do we handle refunds on charges that were themselves partially disputed or already had a chargeback? (Edge case, but SOC2 auditors will ask.)
- What's the migration story for the ~30/month of currently mis-recorded ledger entries — do we retroactively correct historical rows, or only fix forward from cutover?
- Does the new ledger need to expose an API to downstream systems (finance exports, data warehouse), or is a DB read sufficient for now?
- Multi-currency: are all refunds in a single currency today, or does v2 need to handle FX at refund time?
- Tax handling on partial refunds — is tax refunded proportionally, and who owns that calculation?

