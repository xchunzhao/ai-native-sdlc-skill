---
artifact: plan
feature: account-recovery-passkeys
author: eval-run
status: draft
created: 2026-09-03
intent_ref: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
spec_ref: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
risk: high
reviewers:
  - engineer
  - security-lead
  - tech-lead
accepted_by:
accepted_at:
---

# Plan — Passkey account recovery

## Files that change

| File | Change |
|---|---|
| `src/auth/recovery-controller.ts` | Apply indistinguishable initiation responses and consume single-use recovery tokens. |
| `src/auth/recovery-token-store.ts` | Add hashed, expiring token creation and atomic consumption. |
| `src/auth/passkey-service.ts` | Require the recovery challenge before registering the replacement credential. |
| `src/auth/recovery-controller.test.ts` | Cover known/unknown accounts, expiry, replay, revocation, and rate limits. |
| `e2e/account-recovery.spec.ts` | Exercise the accessible recovery flow and successful security notification. |

Paths must be confirmed against the target repository before acceptance; the supplied evaluation context contains no repository tree.

## Order of work

1. Confirm the existing recovery, notification, and passkey boundaries and replace any provisional paths above.
2. Implement atomic hashed-token creation and consumption with expiry and account/source rate-limit hooks.
3. Wire the recovery controller to the token store while preserving indistinguishable initiation behavior.
4. Gate replacement credential registration on the completed challenge, then revoke remaining tokens and emit the security notification.
5. Add unit and integration coverage; run the exact browser recovery flow with accessibility checks.
6. Review security evidence, enable behind `passkey_recovery`, and stage rollout from internal accounts to 5%, 25%, then 100%.

Steps 2 and the UI shell can proceed in parallel once the token and error contracts are fixed. Controller wiring depends on step 2; rollout depends on all proof obligations.

## Risks

- **Account takeover — low likelihood, critical blast radius:** require both verified recovery channel and passkey challenge; security lead blocks rollout.
- **Enumeration through response timing — medium likelihood, broad blast radius:** integration-test response shape and bounded timing distributions for known and unknown accounts.
- **Token replay race — medium likelihood, account-level blast radius:** consume atomically and test concurrent attempts.
- **Fallback exclusion — medium likelihood, affected-user blast radius:** measure abandonment and keep administrator-assisted recovery outside this rollout.

## Proof

- Unit tests verify token hashing, expiry, one-time atomic consumption, revocation, and rate-limit precedence.
- Integration tests verify indistinguishable known/unknown initiation responses and credential-registration gating.
- E2E verifies focus order, live-region errors, challenge completion, and security notification.
- Security lead reviews threat cases before the feature flag leaves internal accounts.
- Monitor recovery success, abandonment, replay rejection, rate limiting, and security alerts at each rollout gate.
- Disable `passkey_recovery` to stop new attempts; token records remain safely expiring and no schema rollback is required.

## Requirement traceability

| Requirement | Implementation step | Proof |
|---|---|---|
| FR-1 | Steps 2–4 | Integration and E2E recovery success |
| FR-2 | Step 3 | Known/unknown response and timing tests |
| FR-3 | Step 4 | Revocation and notification tests |
| FR-4 | Steps 2–5 | Expiry, replay, and rate-limit tests |
| SEC-1 | Steps 2 and 6 | Token-store tests and security review |
| NFR-1 | Step 5 | E2E accessibility verification |

## Build handoff

- **Tracking issue:** project tracker item for `account-recovery-passkeys`
- **Implementation owner:** authentication engineer
- **Required reviewers:** security lead, tech lead, accessibility lead
- **Parallel work groups and interface contracts:** token store and UI shell may proceed in parallel against the agreed token/error contract
- **Proof obligations:** listed in Proof; no rollout before security review
- **Rollout owner:** product owner
- **Deployment owner:** service owner
- **Completion evidence:** linked test output, browser verification, security approval, rollout metrics, and any accepted gap
