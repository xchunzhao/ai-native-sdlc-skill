# Approval Matrix — who reviews what, and when to escalate

Read this when you need to decide who reviews an artifact or whether to escalate.

## The matrix

| Artifact | Writes | Primary reviewer | Additional reviewers | Escalation trigger |
|---|---|---|---|---|
| `intent.md` | Initiator + agent | Product owner | — | — |
| `spec.md` | Agent (loading org skills) | Product owner | Policy owner per flagged concern | Tech lead if any high-risk area is touched |
| `plan.md` | Agent in plan mode + engineer | Engineer | — | Tech lead / architect if any high-risk area is touched |

## What counts as "high-risk"

Escalate when the work touches any of these:

- **Auth / identity** — changes to login, session, permission, or account boundary logic
- **Payments / money** — anything that moves value, records a charge, or interacts with a payment processor
- **PII / privacy** — creating, reading, or moving personally identifiable information across systems
- **Migrations** — schema changes, backfills, data reshuffling; anything that runs once and is hard to roll back
- **External contracts** — public API, partner integration, contractual SLA
- **Compliance surface** — anything touching SOC2, PCI, HIPAA, GDPR, or similar
- **Post-mortem territory** — any system the team has previously written a post-mortem about; that's evidence it can bite

If the change fits any of these, name a tech lead (or architect for cross-system implications) in the review list from the start. Do not wait for the reviewer to demand escalation.

## Policy owners (for spec.md `Areas of concern`)

The spec's flagged concerns get dispatched to whoever owns the relevant policy in the org. Common mappings:

| Concern type | Owner |
|---|---|
| Security / auth / secrets | Security lead / AppSec |
| Data privacy / PII / GDPR | Privacy lead / Legal |
| Brand tone / voice / visual identity | Brand / Design lead |
| UX interaction / accessibility | Design lead |
| Compliance (PCI, SOC2, HIPAA) | Compliance lead |
| Infrastructure / SRE / on-call impact | SRE / platform lead |

If the org doesn't have a named owner for a concern area, escalate to the tech lead — they'll route it or decide.

## When the initiator and reviewer are the same person

Common in small teams. The rule doesn't change: still write the artifact, still separate the "write" and "review" commits, still get a second pair of eyes even if informally. The audit trail is worth the extra minute.

## Escalation etiquette

- Tag the escalation target in the PR description of the artifact
- Cite the specific risk (auth change, migration, etc.) — don't just say "high-risk"
- Suggest a review timeframe. If none, the process stalls.
- If the escalated reviewer doesn't respond in that window, the initiator escalates one level further and the delay goes in the audit trail
