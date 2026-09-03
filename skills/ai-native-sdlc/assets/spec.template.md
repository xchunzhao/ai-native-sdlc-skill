---
artifact: spec
feature: <feature-slug>
author: <agent-name-or-handle>
status: draft
created: <YYYY-MM-DD>
intent_ref: <accepted-intent-commit-sha>
risk: <low|medium|high>
reviewers: []
accepted_by:
accepted_at:
---

# Spec — <feature name>

_Prerequisite: `intent.md` in this folder must be `status: accepted` before this spec is drafted._

## Requirements & design spec

_The functional definition of "done". User-facing behavior, UI/UX, API surface, data model changes, edge cases. Concrete enough that an engineer could sketch the plan from this alone. Include mockups or example payloads inline (or link out) where visual clarity matters._

### Functional requirements

- _Requirement 1_
- _Requirement 2_

### Non-functional requirements

_Performance targets, availability, latency budgets, error handling expectations._

### Out of scope

_Bound the work explicitly. Anything the reader might reasonably assume is in scope but is not._

## Integration with existing code

_Where this hooks into the current codebase. Name the modules, services, or endpoints. Call out any refactoring the change forces on adjacent code. If a new abstraction is needed, justify it against existing patterns._

## Policy compliance

_How this satisfies each policy area. Do one subsection per area. If a policy doesn't apply, say so explicitly and why — don't just omit._

### Brand

_Copy tone, visual identity, product voice. Reference the brand guidelines the agent loaded._

### Security

_AuthN/AuthZ, data handling, threat surface, secrets management. Reference the security policy the agent loaded._

### Compliance

_PII, PCI, GDPR, SOC2, regional regulations. Reference the compliance rules the agent loaded._

### UX

_Accessibility (WCAG level), interaction patterns, error states. Reference the UX guidelines the agent loaded._

## Areas of concern

_The most important section. Call out ambiguities, unresolved trade-offs, and — especially — places where two policies conflict with each other. Do not paper over conflicts. Name them so the product owner can dispatch each one to the right policy owner._

- _Concern 1 (owner: <role>) — description_
- _Concern 2 (owner: <role>) — description_
