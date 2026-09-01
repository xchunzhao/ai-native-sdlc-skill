# Maintain Guide — writing `intent.md` from a production signal

Read this when a production signal — an incident, a metric breach, a bug report, a user complaint — is what starts the conversation, not a fresh product idea. Your job is to **diagnose** and turn the diagnosis into an `intent.md` that re-enters the workflow. **You do not fix the code, deploy, or cross any review gate.** The loop is: diagnosis → intent.md → spec.md → plan.md → build → deploy — same gates as everything else.

The point of this guide: the agent can go all the way up to the production gate, but never crosses it. Diagnosis is agent work; the fix goes through the normal loop.

## When this applies

- On-call gets paged; a user reports a bug; monitoring flags a metric drift; a support ticket reveals a systemic issue.
- A previous incident's fix needs a follow-up; a post-mortem action item hasn't landed.
- Anything where the starting point is "something is wrong in production" rather than "we want to build something new".

If the user is asking you to hotfix production directly, stop and tell them: emergency hotfixes are handled outside this skill; if they choose to hotfix, they must write a retrospective `intent.md` + `spec.md` within one business day (see `SKILL.md`'s "When to skip"). This guide is for the structural follow-up, not the hotfix itself.

## Order of operations

1. **Do not touch production code, config, or infrastructure.** Read-only diagnosis. If the user asks you to "just push a fix", refuse — the fix goes through the normal loop.
2. **Gather evidence.** Logs, metrics, traces, related tickets, recent deploys. Cite specific values, timestamps, and file paths. If you can only get partial evidence, name what's missing.
3. **Form a diagnosis.** A single paragraph: what is broken, when it started, and — if you have enough evidence — why. If you cannot determine *why* with the evidence available, say so and list what would tell you.
4. **Pick a slug.** Format: `incident-<YYYY-MM-DD>-<short-desc>` (e.g. `incident-2026-09-01-refund-500s`). This keeps incidents visually distinct from feature work in `docs/sdlc/`.
5. **Ensure the folder exists.** `docs/sdlc/<slug>/`.
6. **Read the intent template from this skill.** Do not copy it into the project. The template lives in this skill's `assets/intent.template.md`; load it with your agent's file-read tool, then write the filled version straight to `docs/sdlc/<slug>/intent.md`.
7. **Fill sections from the diagnosis** — see coaching below. `Problem` leads with the evidence.
8. **Update frontmatter.** Author = the diagnosing agent + the on-call handle. `status: draft`.
9. **Suggest a commit.** `sdlc(<slug>): add intent.md (incident diagnosis)`.
10. **Hand off.** Remind the user: this intent enters the same review loop as any other. The incident owner (usually tech lead or on-call) accepts; then spec drafts, then plan drafts, then code changes go through PR review. **The stages are not skipped because it's an incident.**

## Section-by-section coaching

### Problem
- Lead with the observable failure and its evidence: metric, timestamp, ticket ID, log excerpt.
- Bad: "the refund service is unstable."
- Good: "post-deploy 5xx rate on `POST /api/refunds` rose from 0.2% baseline to 4.1% at 2026-09-01T14:22Z; 87 affected users in the 30-min window; error class `LedgerTimeoutError` in `refund_service/ledger_client.py`."
- If evidence is thin, say so explicitly — "no logs older than 15 min retained; hypothesis based on error message class only."

### Proposed outcome
- The observable end state that closes the incident, not the fix design.
- Good: "5xx rate returns to <0.5% baseline and stays there for 24h under normal traffic."
- Wrong: "add a retry with exponential backoff" — that's the fix, and it belongs in `spec.md`, not here.

### Affected users and systems
- Number of affected users when known. Named systems: which services, which endpoints, which downstream dependencies.
- Include upstream dependencies too — even if the fix is likely downstream, the diagnosis names the upstream if it's involved. Otherwise the spec may be scoped wrong.

### Constraints
- Any rollback windows, deploy freezes, or SLA constraints that bound the fix's timing.
- Any data-integrity constraints ("cannot re-issue refunds — customer would be double-credited").
- Whether a hotfix path is being handled in parallel (and if so, this intent covers the follow-up structural fix, not the hotfix itself).

### Open questions
- What the diagnosis couldn't determine. These become spec-phase priorities.
- If root cause is uncertain, that's an open question — "is this caused by the deploy at 14:15 or the config change at 14:18?"
- Good open question: "does the retry belong in the client SDK or the service?" — it's a design decision the spec must resolve.

### Author + Status
- Author: diagnosing agent + on-call handle.
- Status stays `draft` until the incident owner accepts. Never mark `accepted` yourself.

## Common failure modes

- **Fixing on the spot.** Even a "one-line" change bypasses the audit trail. Diagnose and write; do not touch production.
- **Vague evidence.** "Users complained" without a ticket / count / timestamp is not evidence. Push back until you have concrete numbers, or say "no concrete evidence yet" in the intent.
- **Skipping the spec stage because "we know what to do".** No — the incident intent still triggers a spec. The spec is short if the fix is obvious, but it exists.
- **Writing the fix into `Proposed outcome`.** Outcome is what should be true; the fix is design (spec) or implementation (plan).
- **Silently dropping open questions.** If the diagnosis has uncertainty, name it. Hidden uncertainty is what caused the incident in the first place — don't repeat the pattern.
- **Widening scope without permission.** The intent covers the incident's structural fix, not a broader refactor you noticed while diagnosing. Adjacent findings go in `Open questions` or a separate intent.

## When to stop and hand off

- Evidence, diagnosis, and all required intent sections filled with real content.
- Frontmatter complete; slug follows `incident-<date>-<short-desc>` format.
- User has committed the file.
- Remind the user: **incident owner reviews and accepts; from that point the normal spec → plan → build flow runs. The agent does not proceed to the fix until the intent is accepted.**
