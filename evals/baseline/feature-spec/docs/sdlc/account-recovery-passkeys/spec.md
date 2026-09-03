---
artifact: spec
feature: account-recovery-passkeys
author: eval-run
status: draft
created: 2026-09-03
intent_ref: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
risk: high
reviewers:
  - product-owner
  - security-lead
  - accessibility-lead
accepted_by:
accepted_at:
---

# Spec — Passkey account recovery

## Requirements & design spec

### Functional requirements

- **FR-1:** An enrolled user can start recovery with a verified recovery email and complete a fresh passkey challenge before a new credential is registered.
- **FR-2:** Recovery never reveals whether an email belongs to an account; initiation returns the same response and timing class for known and unknown addresses.
- **FR-3:** A successful recovery revokes outstanding recovery tokens and notifies the account through its existing security-notification channel.
- **FR-4:** Failed, expired, replayed, and rate-limited recovery attempts produce defined, non-sensitive error states.

### Non-functional requirements

- **SEC-1:** Recovery tokens are single-use, expire after 15 minutes, are stored only as hashes, and are rate-limited by account and network source.
- **NFR-1:** The recovery screen and errors meet the project's WCAG 2.2 AA interaction and announcement conventions.

### Out of scope

Changing primary login, replacing the current email provider, and administrator-assisted identity proofing are excluded.

## Integration with existing code

Extend the existing recovery controller and token store rather than adding another authentication subsystem. The passkey registration service remains the only credential-creation boundary. The implementation plan must verify the concrete repository paths before naming changes.

## Policy compliance

### Brand

No new brand policy is implicated beyond existing account-security copy. Product review is required for final wording.

### Security

No repository security policy was supplied with the accepted intent. Manual review by the security lead is required for enumeration resistance, token lifecycle, rate limits, credential binding, revocation, and audit events.

### Compliance

Recovery email and security events are PII. Existing retention and access-control policy applies; no additional identity document is collected.

### UX

The flow uses existing form, focus, validation, and live-region patterns. Accessibility lead review is required for challenge fallback and error recovery.

## Areas of concern

- Security policy source unavailable (owner: security lead) — the spec must not claim security compliance until manual review is recorded.
- Recovery-email compromise (owner: product owner and security lead) — email possession alone is insufficient; the passkey challenge is mandatory.
- Users without a usable passkey-capable device (owner: product owner) — administrator-assisted recovery remains out of scope and needs a separate intent.
