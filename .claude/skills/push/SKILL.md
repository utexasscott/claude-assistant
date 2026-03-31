---
name: push
description: Use when someone asks to push context to Google Drive, upload context to Drive, save context to Drive, or back up local context files.
disable-model-invocation: true
---

## What This Skill Does

Uploads all files from the local `context/` directory to the `Claude Agent Context` folder on Google Drive. Preserves subdirectory structure. Creates the Drive folder automatically if it doesn't exist. Use this after editing context files locally to keep Drive in sync.

## Steps

1. Run:
   ```
   python tools/sync_context.py --direction push
   ```
2. Report the results — how many files were uploaded or updated, and which ones.
3. If there are errors, show the full error message and advise next steps (see Notes).
4. If `context/shared/` contains any person directories, push each one to its corresponding shared Drive folder as defined in `context/context_policy.md` Section 2. Use `tools/sync_context.py` with `--source` and `--drive-folder` arguments, or upload manually via the Drive API tool. Report which destinations were pushed.

## Notes

- One-way push only: local `context/` → Drive. Does NOT pull Drive changes down first.
- Use `/update` to pull Drive changes to local before pushing if you suspect both sides have changed.
- First run opens a browser OAuth window. Token is saved to `auth/token_drive.json`.
- If `auth/token_drive.json` is missing and a browser can't open, tell the user to run the tool manually in a terminal first to complete the OAuth flow.
- Uploads everything in `context/` recursively, including all subdirectories.
- Existing Drive files are updated in place; new files are created. Nothing is deleted from Drive.
- Never invoke this automatically — only when explicitly requested.
