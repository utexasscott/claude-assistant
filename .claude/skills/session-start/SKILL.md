---
name: session-start
description: Use when starting a session, syncing before starting work, setting up on a new device, or beginning a work session.
disable-model-invocation: true
---

## What This Skill Does

Syncs both GitHub and Google Drive at the start of a session. Runs git-pull first to get the latest code, then pulls personal context from Drive. Stops and reports if either step fails.

## Steps

### Step 1: Git Pull

Follow all steps in `.claude/skills/git-pull/SKILL.md` exactly.

- If it succeeds (or is already up to date), continue to Step 2.
- If it fails for any reason, report the error and **stop here**. Do not run Step 2 until the git issue is resolved.

### Step 2: Drive Pull

Follow all steps in `.claude/skills/pull/SKILL.md` exactly.

- Report the results.
- If it fails, report the error and advise next steps.

### Step 3: Summary

After both steps complete successfully, give a brief combined summary:
- What git pulled (or "already up to date")
- What Drive pulled (files downloaded or "nothing new")
- Confirm the session is ready.

## Notes

- Order is intentional: code first, then personal context.
- Never run Step 2 if Step 1 failed — a failed git pull may indicate a conflict that affects context too.
- Do not invoke this automatically. Only run when the user explicitly starts a session.
