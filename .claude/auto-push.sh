#!/usr/bin/env bash
# Auto-commit + push for the academic site repo.
# Invoked by the Stop hook in .claude/settings.json after every Claude turn.
# Behavior: if there are uncommitted changes, stage all, commit with a generic
# message, and push to origin/main. Outputs a systemMessage so the result shows
# in the Claude Code UI. Silent if there is nothing to push.

set -u

# cd into repo root (one level up from .claude/). Works regardless of where
# the hook is invoked from (per-project Claude session or the parent-folder
# multi-project router at OneDrive/GitHub/.claude/auto-push-router.sh).
cd "$(dirname "$0")/.." 2>/dev/null || { echo '{"systemMessage":"auto-push: repo path not found, skipping."}'; exit 0; }

# No changes (tracked or untracked)? Exit silently.
if [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

# Stage everything (tracked modifications + new untracked files).
git add -A >/dev/null 2>&1

# Commit. If pre-commit hooks fail, abort with a message.
if ! git commit -m "auto: changes from Claude Code session" \
    -m "Co-Authored-By: Claude <noreply@anthropic.com>" >/dev/null 2>&1; then
  echo '{"systemMessage":"auto-push: commit failed (no staged change or hook rejected). Skipped."}'
  exit 0
fi

# Push.
if git push origin main >/dev/null 2>&1; then
  SHORT=$(git log -1 --format=%h 2>/dev/null)
  echo "{\"systemMessage\":\"auto-pushed ${SHORT} to origin/main.\"}"
else
  echo '{"systemMessage":"auto-push: commit succeeded but push failed (run git push origin main manually)."}'
fi
