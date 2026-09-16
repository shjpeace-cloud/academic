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

# Did anything that feeds the CV change? Noted before staging, because after
# `git add -A` the porcelain output no longer distinguishes them. The check
# itself runs after the push so a failure here can never cost a commit.
CV_TOUCHED=""
if git status --porcelain \
   | grep -qE 'data/publications\.json|\.claude/tools/build_cv\.py'; then
  CV_TOUCHED=1
fi

# Stage everything (tracked modifications + new untracked files).
git add -A >/dev/null 2>&1

# Commit. If pre-commit hooks fail, abort with a message.
if ! git commit -m "auto: changes from Claude Code session" \
    -m "Co-Authored-By: Claude <noreply@anthropic.com>" >/dev/null 2>&1; then
  echo '{"systemMessage":"auto-push: commit failed (no staged change or hook rejected). Skipped."}'
  exit 0
fi

# Is the published CV PDF behind the data it is built from? Only asked when
# something feeding it moved. Warning only -- regenerating the PDF needs Word,
# so it cannot happen here, and a stale CV must never block a push. Only the
# exit status is used; the script's own output carries quotes and dashes that
# would have to be escaped into JSON.
CV_NOTE=""
if [ -n "$CV_TOUCHED" ] && command -v python >/dev/null 2>&1; then
  if ! python .claude/tools/build_cv.py --check >/dev/null 2>&1; then
    CV_NOTE=" CV is stale: run 'python .claude/tools/build_cv.py --check'."
  fi
fi

# Push.
if git push origin main >/dev/null 2>&1; then
  SHORT=$(git log -1 --format=%h 2>/dev/null)
  echo "{\"systemMessage\":\"auto-pushed ${SHORT} to origin/main.${CV_NOTE}\"}"
else
  echo "{\"systemMessage\":\"auto-push: commit succeeded but push failed (run git push origin main manually).${CV_NOTE}\"}"
fi
