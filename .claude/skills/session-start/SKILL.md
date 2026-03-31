---
name: session-start
description: Use when starting a session, syncing before starting work, setting up on a new device, or beginning a work session.
disable-model-invocation: true
---

## What This Skill Does

Pulls the latest changes from the private GitHub repo at the start of a session. The private repo is the source of truth for all content, including personal context. Run this at the start of every session on any device.

## Steps

### Step 1: Git Pull

Follow all steps in `.claude/skills/git-pull/SKILL.md` exactly.

- If it succeeds (or is already up to date), continue to Step 2.
- If it fails for any reason, report the error and **stop here**. Do not proceed until the git issue is resolved.

### Step 2: Summary

Give a brief summary:
- What git pulled (or "already up to date")
- Confirm the session is ready.

## Notes

- The private repo (`origin`) contains everything: code, skills, workflows, and personal context.
- No Drive pull needed — context is now tracked in git.
- Do not invoke this automatically. Only run when the user explicitly starts a session.
