#!/usr/bin/env bash
# Bootstrap the AI-Native SDLC structure into the current project.
#
# Usage:
#   bootstrap.sh [<project-dir>]
#
# What it does (idempotent):
#   1. Creates docs/sdlc/ with README.md and _templates/
#   2. Appends a section to AGENTS.md (or creates it) pointing at docs/sdlc/README.md
#   3. Skips anything that already exists — safe to re-run

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS="$SKILL_DIR/assets"

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

SDLC_DIR="$PROJECT_DIR/docs/sdlc"
TEMPLATES_DIR="$SDLC_DIR/_templates"
AGENTS_MD="$PROJECT_DIR/AGENTS.md"

echo "Bootstrapping AI-Native SDLC in: $PROJECT_DIR"

mkdir -p "$TEMPLATES_DIR"

# --- README (spec source of truth) ---
if [[ -f "$SDLC_DIR/README.md" ]]; then
  echo "  skip: docs/sdlc/README.md already exists"
else
  cp "$ASSETS/project-README.md" "$SDLC_DIR/README.md"
  echo "  wrote: docs/sdlc/README.md"
fi

# --- Templates ---
for tpl in intent.template.md spec.template.md plan.template.md; do
  if [[ -f "$TEMPLATES_DIR/$tpl" ]]; then
    echo "  skip: docs/sdlc/_templates/$tpl already exists"
  else
    cp "$ASSETS/$tpl" "$TEMPLATES_DIR/$tpl"
    echo "  wrote: docs/sdlc/_templates/$tpl"
  fi
done

# --- AGENTS.md ---
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
echo "  1. Review $SDLC_DIR/README.md and $AGENTS_MD, edit anything project-specific."
echo "  2. Commit: sdlc: bootstrap docs/sdlc structure"
echo "  3. Start your first feature: /intent <feature-slug>"
