#!/usr/bin/env bash
# Bootstrap the AI-Native SDLC structure into the current project.
#
# Usage:
#   bootstrap.sh [<project-dir>]
#
# What it does (idempotent):
#   1. Creates docs/sdlc/ (where feature/incident folders will live)
#   2. Appends a section to AGENTS.md (or creates it) telling agents:
#      - to read the ai-native-sdlc skill (workflow rules + templates)
#      - what to generate in this project (docs/sdlc/<slug>/)
#      - gate strategy (frontmatter status)
#      - artifact frontmatter schema
#   3. Skips anything that already exists — safe to re-run
#
# What it deliberately does NOT do:
#   - Copy README/workflow docs into the project — those live in the skill, single source of truth
#   - Copy artifact templates into the project — agents read them from the skill directly
#
# The invariant: the skill is the spec; the project holds only project-local
# artifacts (the produced intent.md / spec.md / plan.md) and a pointer in
# AGENTS.md. Skill updates are picked up automatically on the next session.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS="$SKILL_DIR/assets"

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

SDLC_DIR="$PROJECT_DIR/docs/sdlc"
AGENTS_MD="$PROJECT_DIR/AGENTS.md"

echo "Bootstrapping AI-Native SDLC in: $PROJECT_DIR"

# --- Ensure docs/sdlc/ exists ---
if [[ -d "$SDLC_DIR" ]]; then
  echo "  skip: docs/sdlc/ already exists"
else
  mkdir -p "$SDLC_DIR"
  echo "  wrote: docs/sdlc/ (empty; feature folders will be created here)"
fi

# --- AGENTS.md: append or create ---
SNIPPET_MARKER="## AI-Native SDLC"
if [[ -f "$AGENTS_MD" ]]; then
  if grep -q "^$SNIPPET_MARKER" "$AGENTS_MD"; then
    echo "  skip: AGENTS.md already has AI-Native SDLC section"
  else
    printf '\n' >> "$AGENTS_MD"
    cat "$ASSETS/AGENTS.md.snippet" >> "$AGENTS_MD"
    echo "  appended: AGENTS.md (added AI-Native SDLC section)"
  fi
else
  # New file — write a minimal header plus the snippet
  {
    echo "# AGENTS.md"
    echo
    echo "Project-level guidance for coding agents. Read before starting work."
    cat "$ASSETS/AGENTS.md.snippet"
  } > "$AGENTS_MD"
  echo "  wrote: AGENTS.md"
fi

echo
echo "Done. Next steps:"
echo "  1. Review $AGENTS_MD, edit anything project-specific."
echo "  2. Commit: sdlc: bootstrap docs/sdlc structure"
echo "  3. Start your first feature: tell your agent to write an intent, or use /intent <slug> in Claude Code."
