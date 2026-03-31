---
name: session-end
description: Use when ending a session, wrapping up work, syncing before closing, done for today, or finishing a work session.
disable-model-invocation: true
argument-hint: "[optional commit message]"
---

## What This Skill Does

Syncs both Google Drive and GitHub at the end of a session. Pushes personal context to Drive first, then commits and pushes code to GitHub. Stops and reports if either step fails.

## Steps

### Step 1: Drive Push

Follow all steps in `.claude/skills/push/SKILL.md` exactly.

- If it succeeds, continue to Step 2.
- If it fails for any reason, report the error and **stop here**. Do not run Step 2 until the Drive issue is resolved.

### Step 2: Check Git Status

Run `git status --porcelain`.

- If output is **empty**: skip Steps 3 and 4. Go directly to Step 5 and note "nothing to push" for the GitHub section.
- If output is **not empty**: continue to Step 3.

### Step 3: Security Review

Scope the scan to only the files that will be staged. From the `git status --porcelain` output:

1. Extract all file paths (the second column, after the two-character status code).
2. Filter to only files in committed paths: `tools/`, `.claude/skills/`, `workflows/public/`, `workflows/private/`, `workflows/_index.md`, `context_example/`, `CLAUDE.md`, `CLAUDE-personal.md`, `README.md`. Skip anything in gitignored paths (`context/`, `auth/`, `.env`, `.tmp/`).
3. If no files remain after filtering, note "Security scan: no committed-path files changing" and skip to Step 4.
4. Read each remaining file and scan for:
   - Command injection (`subprocess` with `shell=True` + unsanitized input)
   - Path traversal (unvalidated file path args)
   - Hardcoded secrets/API keys
   - `eval`/`exec` with external input
   - YAML/pickle deserialization with untrusted data
   - HTML injection (f-string interpolation of external data into HTML)
5. Only report findings with >80% confidence of real exploitability. Skip theoretical issues.
6. If findings exist, list them clearly and ask the user if they want to fix before pushing.
   - If the user says to continue despite findings, proceed to Step 4.
   - If the user wants to fix first, stop here.
7. If no findings, note "Security scan: clean" and continue.

### Step 4: Git Push

Follow all steps in `.claude/skills/git-push/SKILL.md` exactly.

- If an argument was provided, pass it as the commit message.
- Report the results.

### Step 5: Summary

After all steps complete, give a brief combined summary:
- What was pushed to Drive (files uploaded or "nothing new")
- Security scan result (clean, skipped, or findings addressed)
- What was committed and pushed to GitHub (commit message + hash, or "nothing to push")
- Confirm the session is cleanly synced.

## Notes

- Order is intentional: personal context first, then code.
- Never run Step 2 if Step 1 failed — don't push code if context is out of sync.
- Do not invoke this automatically. Only run when the user explicitly ends a session.
- Accepts an optional commit message argument passed through to git-push.
