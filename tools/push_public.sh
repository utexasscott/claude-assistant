#!/usr/bin/env bash
# push_public.sh — Syncs public-safe files to the claude-assistant public repo.
# Usage: bash tools/push_public.sh ["optional commit message"]
#
# Public-safe content: tools/, workflows/public/, workflows/_example/,
# context_example/, whitelisted skills, and CLAUDE.md.
# CLAUDE-personal.md and everything else personal stays in the private repo.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_REMOTE="https://github.com/utexasscott/claude-assistant.git"
WORK_DIR="$REPO_ROOT/.tmp/claude-assistant"
COMMIT_MSG="${1:-Sync public-safe content from personal-assistant}"

# ── Private-only paths (never synced to public repo) ─────────────────────────
# context/                  — all personal data
# workflows/private/        — personal SOPs
# workflows/_index.md       — personal route table
# CLAUDE-personal.md        — personal extensions to agent instructions
# .claude/agents/           — agents are user-specific (contain personal names/paths)
# .claude/skills/*/SKILL-personal.md  — stripped automatically below
# .env, auth/               — credentials and tokens (gitignored)

# ── Public skills whitelist ────────────────────────────────────────────────────
PUBLIC_SKILLS=(
  check-email
  context
  excalidraw-diagram
  git-pull
  git-push
  gmail-draft
  journal
  morning-coffee
  onboarding
  plan-meals
  pull
  push
  read-journal
  recipes
  security-sweep
  session-end
  session-push
  session-start
  skill-builder
  update-sheet
  workflow-editor
  push-public
)

echo "── Preparing work directory ──────────────────────────────────────────────────"
if [ -d "$WORK_DIR/.git" ]; then
  echo "Pulling latest public repo..."
  # Skip pull if the remote has no commits yet (initial push)
  if git -C "$WORK_DIR" ls-remote --exit-code origin HEAD &>/dev/null; then
    git -C "$WORK_DIR" pull --ff-only
  else
    echo "Remote is empty — skipping pull."
  fi
else
  echo "Cloning public repo..."
  mkdir -p "$WORK_DIR"
  git clone "$PUBLIC_REMOTE" "$WORK_DIR"
fi

# Carry local git identity into the work dir (it may not have global config)
GIT_USER="$(git -C "$REPO_ROOT" config user.name)"
GIT_EMAIL="$(git -C "$REPO_ROOT" config user.email)"
git -C "$WORK_DIR" config user.name "$GIT_USER"
git -C "$WORK_DIR" config user.email "$GIT_EMAIL"

echo "── Clearing existing content (preserving .git) ───────────────────────────────"
find "$WORK_DIR" -mindepth 1 -not -path "$WORK_DIR/.git*" -delete

echo "── Copying public-safe directories ──────────────────────────────────────────"
# tools/
mkdir -p "$WORK_DIR/tools"
cp -r "$REPO_ROOT/tools/." "$WORK_DIR/tools/"

# workflows/public/ and workflows/_example/
mkdir -p "$WORK_DIR/workflows/public" "$WORK_DIR/workflows/_example"
cp -r "$REPO_ROOT/workflows/public/." "$WORK_DIR/workflows/public/"
cp -r "$REPO_ROOT/workflows/_example/." "$WORK_DIR/workflows/_example/"

# context_example/
if [ -d "$REPO_ROOT/context_example" ]; then
  mkdir -p "$WORK_DIR/context_example"
  cp -r "$REPO_ROOT/context_example/." "$WORK_DIR/context_example/"
fi

echo "── Copying whitelisted skills ────────────────────────────────────────────────"
mkdir -p "$WORK_DIR/.claude/skills"
for skill in "${PUBLIC_SKILLS[@]}"; do
  src="$REPO_ROOT/.claude/skills/$skill"
  if [ -d "$src" ]; then
    mkdir -p "$WORK_DIR/.claude/skills/$skill"
    cp -r "$src/." "$WORK_DIR/.claude/skills/$skill/"
    # Strip personal extension files — these are private and must not appear in the public repo
    find "$WORK_DIR/.claude/skills/$skill" -name "SKILL-personal.md" -delete
    echo "  + $skill"
  else
    echo "  ! $skill not found, skipping"
  fi
done

echo "── Copying CLAUDE.md ────────────────────────────────────────────────────────"
# CLAUDE.md is now public-safe by design. CLAUDE-personal.md stays private.
cp "$REPO_ROOT/CLAUDE.md" "$WORK_DIR/CLAUDE.md"

echo "── Writing public .gitignore ─────────────────────────────────────────────────"
cat > "$WORK_DIR/.gitignore" << 'GITIGNORE'
# ── Secrets & credentials ─────────────────────────────────────────────────────
.env
auth/

# ── Temporary processing files ─────────────────────────────────────────────────
.tmp/

# ── Personal context ───────────────────────────────────────────────────────────
# Populate your own from the templates in context_example/
context/

# ── Personal workflows and skills ─────────────────────────────────────────────
# Add your private workflows and personal skills here — keep them out of git
workflows/_index.md
workflows/private/

# ── Personal skill extensions ──────────────────────────────────────────────────
# SKILL-personal.md files extend public skills with user-specific config
**SKILL-personal.md

# ── OS / editor noise ──────────────────────────────────────────────────────────
.DS_Store
Thumbs.db
*.pyc
__pycache__/
.venv/
GITIGNORE

echo "── Committing and pushing ────────────────────────────────────────────────────"
git -C "$WORK_DIR" add -A

if git -C "$WORK_DIR" diff --cached --quiet; then
  echo "Nothing changed — public repo is already up to date."
  exit 0
fi

git -C "$WORK_DIR" commit -m "$COMMIT_MSG"
git -C "$WORK_DIR" push origin main

echo "── Done ──────────────────────────────────────────────────────────────────────"
echo "Public repo updated: $PUBLIC_REMOTE"
