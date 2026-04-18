---
name: session-start
description: Use when starting a session, syncing before starting work, setting up on a new device, or beginning a work session.
disable-model-invocation: true
metadata:
  visibility: public
---

## What This Skill Does

Pulls the latest changes from the private GitHub repo at the start of a session. The private repo is the source of truth for all content, including personal context. Run this at the start of every session on any device.

## Steps

### Step 1: Git Pull

Follow all steps in `.claude/skills/git-pull/SKILL.md` exactly.

- If it succeeds (or is already up to date), continue to Step 2.
- If it fails for any reason, report the error and **stop here**. Do not proceed until the git issue is resolved.

### Step 2: Check for credentials.json (new machine gate)

Check whether `auth/credentials.json` exists.

- If it **exists**: skip this step, continue to Step 3.
- If it is **missing**: tell the user:
  > `auth/credentials.json` is not tracked in git — you need to copy it from your password manager before any Google API tools will work. Everything else (`.env`, OAuth token files) was pulled from the private repo automatically.

  This is non-blocking. Note it in the summary and continue.

### Step 3: Summary

Give a brief summary:
- What git pulled (or "already up to date")
- credentials.json status (present or missing with instructions)
- Confirm the session is ready.

## Notes

- The private repo (`origin`) contains everything: code, skills, workflows, personal context, `.env`, and `auth/token_*.json`. On a new machine, `session-start` is sufficient to restore all of this.
- `auth/credentials.json` is the one exception — it is gitignored and must be copied manually from a password manager (it's the OAuth Desktop App credential from Google Cloud Console).
- No Drive pull needed — context is tracked in git.
- Do not invoke this automatically. Only run when the user explicitly starts a session.
