# AI-Native SDLC Skill

A reusable agent skill that runs Anthropic's AI-Native SDLC loop — **intent → spec → plan → build → maintain** — with human approval gates at every handoff. The agent goes all the way up to the production gate, and never crosses it.

Framework-neutral: works in Claude Code, Codex, and any agent that follows the SKILL.md convention.

Based on Anthropic's [AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook).

---

## What it does

Every substantial change flows through three markdown artifacts before code is written:

| Artifact | Answers |
|---|---|
| `intent.md` | Why are we doing this? Who is it for? |
| `spec.md` | What does "done" look like? What policies constrain it? |
| `plan.md` | How will the code change? In what order? How do we prove it works? |

Each artifact is committed to git and gated on human approval (frontmatter `status: accepted`). **The commit chain is the audit trail.**

When a production signal — an incident, a metric drift, a bug report — starts the conversation instead of a fresh idea, the skill runs a **read-only diagnosis** and turns the diagnosis into an `intent.md` that re-enters the loop. The fix still goes through the normal spec → plan → build flow; the agent never patches production directly.

---

## Install

Clone this repo, then copy the skill folder into your agent's skills directory.

### Claude Code

Personal (available in every session):
```bash
cp -R skills/ai-native-sdlc ~/.claude/skills/
```

Team-shared, per project (skill ships with the repo, everyone gets it on clone):
```bash
cp -R skills/ai-native-sdlc <your-project>/.claude/skills/
```

### Codex

```bash
cp -R skills/ai-native-sdlc ~/.codex/skills/
```

### Other skill-compatible agents

Copy `skills/ai-native-sdlc/` into whatever skills directory your agent reads. The SKILL.md format is agent-agnostic.

---

## Use it

Once installed, the skill activates automatically when you start feature work or triage a production signal. **You do not need a slash command**:

> "I want to add SSO to the admin dashboard — let's start with the intent."

> "We're seeing 5xx spikes on the refund endpoint since this morning's deploy. Help me diagnose."

On first use in a project, the skill scaffolds `docs/sdlc/` (README + templates) and appends a section to `AGENTS.md` so **other agents in the same repo** (Cursor, Aider, Windsurf, and any tool that reads `AGENTS.md`) follow the same workflow.

If you prefer explicit slash commands, Claude Code exposes `/intent <slug>`, `/spec <slug>`, `/plan <slug>`.

---

## Structure

```
skills/ai-native-sdlc/
├── SKILL.md                 # entrypoint: hard rules, three-command flow, maintain loop
├── references/              # on-demand deep guides
│   ├── intent-guide.md
│   ├── spec-guide.md
│   ├── plan-guide.md
│   ├── maintain-guide.md    # production signal → intent.md flow
│   └── approval-matrix.md   # who reviews what, when to escalate
├── assets/                  # templates copied into target projects
│   ├── intent.template.md
│   ├── spec.template.md
│   ├── plan.template.md
│   ├── AGENTS.md.snippet    # cross-agent trigger, appended to project AGENTS.md
│   └── project-README.md    # copied as docs/sdlc/README.md
└── scripts/
    └── bootstrap.sh         # idempotent scaffold into a target project
```

---

## What gets created in a target project

After the skill's first run (or after invoking `scripts/bootstrap.sh` directly):

```
<your-project>/
├── AGENTS.md                        # appended with SDLC pointer for non-Claude agents
└── docs/sdlc/
    ├── README.md                    # agent-agnostic project spec
    ├── _templates/
    │   ├── intent.template.md
    │   ├── spec.template.md
    │   └── plan.template.md
    └── <feature-slug>/              # one folder per feature or incident
        ├── intent.md
        ├── spec.md
        └── plan.md
```

Incident work uses the slug convention `incident-<YYYY-MM-DD>-<short-desc>` to stay visually distinct from feature slugs.

---

## When to skip

Not everything needs three artifacts. Skip for typo fixes, dep bumps, docs edits with no policy implication, and reverts. **Emergency hotfixes still need a retrospective `intent.md` + `spec.md` within one business day** — the audit trail must reflect reality.

If in doubt, write at least an `intent.md`. It's cheap, and the audit trail is worth more than fifteen minutes.

---

## Contributing

Changes to `SKILL.md`, `references/*-guide.md`, or `assets/*.template.md` change how every project using this skill runs. Treat those edits like library changes:

1. Before merging, run a small regression by hand: pick 3–5 representative real cases (feature intent, incident intent, spec with policy conflicts, plan with a migration) and verify the affected command still behaves as intended.
2. Note the verified cases in the commit message.

See `skills/ai-native-sdlc/SKILL.md` (`## Updating this skill`) for the full rationale.

Issues and pull requests welcome.

---

## Credits

Based on Anthropic's [AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook).

## License

MIT — see [LICENSE](LICENSE).
