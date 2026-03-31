---
name: git-push
description: Use when someone asks to push to GitHub, git push, commit and push, sync to GitHub, or run /git-push.
disable-model-invocation: true
argument-hint: "[optional commit message]"
---

## What This Skill Does

Stages, commits, and pushes this project to GitHub. On first run it initializes git and creates the private `personal-assistant` GitHub repo. Subsequent runs stage all changes, auto-generate a commit message, and push.

## Steps

### Step 1: Check setup

Run:
```
git -C . rev-parse --git-dir 2>/dev/null
```

- If this **fails** (no `.git` directory) → go to **First-Run Setup**
- If this **succeeds** → go to **Push Changes**

---

### First-Run Setup (one time only)

1. Run `git init`
2. Run `git branch -M main`
3. Run `git add .` (respects `.gitignore` — do NOT force-add anything)
4. Run `git commit -m "initial commit: set up personal assistant WAT framework"`
5. Run `gh repo create personal-assistant --private --source=. --remote=origin --push`
6. Report the GitHub repo URL shown in the output. Done.

If `gh` is not authenticated, tell the user to run `gh auth login` first and then try again.

---

### Push Changes (subsequent runs)

1. Run `git status --porcelain` to see what changed.
   - If output is empty, tell the user there's nothing to push and stop.

2. Run `git diff --stat HEAD` (or `git diff --cached --stat` if all changes are staged) to understand what changed.

3. Generate a concise commit message (one sentence, imperative mood, max ~72 chars) summarizing what changed.
   - If `$1` was provided as an argument, use that as the commit message instead.

4. Run `git add .`

5. Run `git commit -m "[your generated message]"`

6. Run `git push origin main`

7. Report: the commit message, commit hash (short), and number of files changed.

---

## Notes

- The `.gitignore` already excludes `.env`, `auth/`, `context/`, `.tmp/`, `workflows/_index.md`, `workflows/private/`. Never force-add these files.
- Never use `--no-verify` or `--force` on push. If push fails due to diverged history, report the error and ask the user how to proceed.
- Requires `gh` CLI installed and authenticated. Check with `gh auth status` if the command fails.
- If the GitHub repo already exists (re-running first-run setup), `gh repo create` will fail — fall back to just running `git remote add origin https://github.com/$(gh api user -q .login)/personal-assistant.git` then `git push -u origin main`.
