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

On first use in a project, the skill creates an empty `docs/sdlc/` and appends an `## AI-Native SDLC` section to `AGENTS.md`. That section tells every agent in the repo (Cursor, Aider, Windsurf, and any tool that reads `AGENTS.md`) **what to read, what to generate, the gate strategy, and the artifact frontmatter schema**. Workflow rules and artifact templates stay in this skill — the project never carries a copy that could drift.

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
├── assets/                  # source of truth for templates and the AGENTS.md snippet
│   ├── intent.template.md   # read from here every session — NEVER copied into projects
│   ├── spec.template.md
│   ├── plan.template.md
│   └── AGENTS.md.snippet    # appended to project AGENTS.md by bootstrap.sh
└── scripts/
    └── bootstrap.sh         # per-project one-time: mkdir docs/sdlc + append AGENTS.md
```

---

## What gets created in a target project

After the skill's first run (or after invoking `scripts/bootstrap.sh` directly):

```
<your-project>/
├── AGENTS.md                        # appended with the SDLC section (read/generate/gate/format)
└── docs/sdlc/                       # empty until the first feature or incident
    └── <feature-slug>/              # one folder per feature or incident
        ├── intent.md
        ├── spec.md
        └── plan.md
```

**No `README.md` or `_templates/` in the project.** Those live only in the skill (single source of truth) so skill updates propagate on the next session without a rebootstrap.

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
