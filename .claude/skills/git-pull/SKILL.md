---
name: git-pull
description: Use when someone asks to pull from GitHub, git pull, sync from GitHub, get latest changes, or run /git-pull.
disable-model-invocation: true
---

## What This Skill Does

Pulls the latest changes from the remote `personal-assistant` GitHub repository into the local project.

## Steps

1. Check if the repo is initialized:
   ```
   git -C . rev-parse --git-dir 2>/dev/null
   ```
   - If this fails, tell the user the repo isn't set up yet and to run `/git-push` first. Stop here.

2. Run `git pull origin main`

3. Report what happened:
   - If already up to date, say so.
   - If changes were pulled, list the files changed and how many commits were fetched.

---

## Notes

- If there are merge conflicts, show the conflicting files and tell the user to resolve them manually. Never auto-resolve or discard changes.
- If the remote doesn't exist yet (no origin), tell the user to run `/git-push` first to set up the remote.
- If the pull fails for any other reason, show the full error output and suggest next steps.
