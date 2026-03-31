---
name: session-end
description: Use when ending a session, wrapping up work, syncing before closing, done for today, or finishing a work session.
disable-model-invocation: true
argument-hint: "[optional commit message]"
metadata:
  visibility: public
---

## What This Skill Does

Commits and pushes all changes to the private GitHub repo at the end of a session, then pushes any shared context to Google Drive for co-parenting coordination. The private repo is the backup; Drive is for sharing only.

## Steps

### Step 1: Check Git Status

Run `git status --porcelain`.

- If output is **empty**: skip Steps 2 and 3. Go directly to Step 4 and note "nothing to push" for the GitHub section.
- If output is **not empty**: continue to Step 2.

### Step 2: Security Review

Scope the scan to only the files that will be staged. From the `git status --porcelain` output:

1. Extract all file paths (the second column, after the two-character status code).
2. Filter OUT gitignored paths: `auth/`, `.env`, `.tmp/`. Everything else (including `context/`) is a committed path in the private repo.
3. If no files remain after filtering, note "Security scan: no tracked-path files changing" and skip to Step 3.
4. For Python files (`.py`), scan for:
   - Command injection (`subprocess` with `shell=True` + unsanitized input)
   - Path traversal (unvalidated file path args)
   - Hardcoded secrets/API keys
   - `eval`/`exec` with external input
   - YAML/pickle deserialization with untrusted data
   - HTML injection (f-string interpolation of external data into HTML)
5. For all other files (markdown, YAML, etc.), scan for hardcoded secrets/API keys only.
6. Only report findings with >80% confidence of real exploitability. Skip theoretical issues.
7. If findings exist, list them clearly and ask the user if they want to fix before pushing.
   - If the user says to continue despite findings, proceed to Step 3.
   - If the user wants to fix first, stop here.
8. If no findings, note "Security scan: clean" and continue.

### Step 3: Git Push

Follow all steps in `.claude/skills/git-push/SKILL.md` exactly.

- If an argument was provided, pass it as the commit message.
- Report the results.

### Step 4: Push to Public Repo

Follow all steps in `.claude/skills/push-public/SKILL.md` exactly.

- This syncs public-safe files to the `claude-assistant` public GitHub repo.
- If nothing changed, the skill will report "nothing to push" and exit cleanly.
- A public repo push failure does NOT invalidate the session end — report the error but continue.

### Step 5: Push Shared Context to Drive

Follow all steps in `.claude/skills/push/SKILL.md` exactly.

- This pushes co-parenting updates from `context/shared/` to Google Drive for Allison.
- If there is nothing to share, the push skill will report "nothing to push" and exit cleanly.
- A Drive push failure does NOT invalidate the session end — git is the backup, Drive is for sharing.

### Step 6: Summary

After all steps complete, give a brief combined summary:
- Security scan result (clean, skipped, or findings addressed)
- What was committed and pushed to GitHub (commit message + hash, or "nothing to push")
- What was pushed to the public repo ("nothing to push", or error details)
- What was pushed to Drive (files uploaded, "nothing to push", or error details)
- Confirm the session is cleanly synced.

## Notes

- Do not invoke this automatically. Only run when the user explicitly ends a session.
- Accepts an optional commit message argument passed through to git-push.
- Drive push failure is non-blocking — the session is still complete if git pushed successfully.
