---
name: session-push
description: Use when someone asks to sync mid-session, checkpoint their work, push without ending the session, or do a mid-session save.
disable-model-invocation: true
argument-hint: [optional commit message]
---

## What This Skill Does

Syncs both Google Drive and GitHub as a mid-session checkpoint. Use this to save progress without ending the session. Pushes personal context to Drive first, then commits and pushes code to GitHub.

## Steps

### Step 1: Drive Push

Follow all steps in `.claude/skills/push/SKILL.md` exactly.

- If it succeeds, continue to Step 2.
- If it fails for any reason, report the error and **stop here**. Do not run Step 2 until the Drive issue is resolved.

### Step 2: Security Review

Run a security scan on all Python files in `tools/`:

1. Use Glob to find all `.py` files in `tools/`
2. Read each file and scan for: command injection (`subprocess` with `shell=True` + unsanitized input), path traversal (unvalidated file path args), hardcoded secrets/API keys in committed files, `eval`/`exec` with external input, YAML/pickle deserialization with untrusted data, HTML injection (f-string interpolation of external data into HTML)
3. Only report findings with >80% confidence of real exploitability. Skip theoretical issues, env var attacks, and anything in `.tmp/` (gitignored).
4. If findings exist, list them clearly and ask the user if they want to fix before pushing. If no findings, note "Security scan: clean" and continue.

- If the user says to continue despite findings, proceed to Step 3.
- If the user wants to fix findings first, stop here.

### Step 3: Git Push

Follow all steps in `.claude/skills/git-push/SKILL.md` exactly.

- If an argument was provided, pass it as the commit message.
- Report the results.

### Step 4: Update Memory

Update `last_edit` in `C:\Users\utexa\.claude\projects\c--wamp-www-personal-assistant\memory\MEMORY.md` to the current datetime (ISO 8601 format, e.g. `2026-03-25T14:30:00`).

### Step 5: Summary

After all steps complete successfully, give a brief combined summary:
- What was pushed to Drive (files uploaded or "nothing new")
- What was committed and pushed to GitHub (commit message + hash, or "nothing to push")
- Confirm the checkpoint is saved. The session continues.

## Notes

- Order is intentional: personal context first, then code.
- Never run Step 2 if Step 1 failed — don't push code if context is out of sync.
- Do not invoke this automatically. Only run when the user explicitly asks.
- Accepts an optional commit message argument passed through to git-push.
- This is a mid-session sync, not a session end. Do not say "session complete" or imply work is done.
