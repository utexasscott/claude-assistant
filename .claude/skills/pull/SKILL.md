---
name: pull
description: Use when someone asks to pull context from Google Drive, sync context from Drive, update local context, or refresh context files from Drive.
disable-model-invocation: true
---

## What This Skill Does

Downloads all files from the `Claude Agent Context` folder on Google Drive into the local `context/` directory. Preserves subdirectory structure. Use this at the start of a session on a new machine, or after editing context files directly in Google Drive.

## Steps

1. Run:
   ```
   python tools/sync_context.py --direction pull
   ```
2. Report the results — how many files were downloaded, and which ones.
3. If there are errors, show the full error message and advise next steps (see Notes).

## Notes

- One-way pull only: Drive → local `context/`. Does NOT push local changes back.
- Use `/push` to send local edits back to Drive.
- First run opens a browser OAuth window. Token is saved to `auth/token_drive.json`.
- If `auth/token_drive.json` is missing and a browser can't open, tell the user to run the tool manually in a terminal first to complete the OAuth flow.
- If the Drive folder `Claude Agent Context` doesn't exist yet, the tool creates it (empty pull).
- Never invoke this automatically at workflow start — only when explicitly requested.
