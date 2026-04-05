---
name: push
description: Use when someone asks to push shared context to Google Drive, share co-parenting updates, push context to Drive for sharing, or upload shared files to Drive.
disable-model-invocation: true
metadata:
  visibility: public
---

## What This Skill Does

Pushes shared context from `context/shared/` to its Google Drive destination for co-parenting coordination. This is **for sharing, not backup** — the private GitHub repo is the source of truth and backup. Only has work to do when journal entries contain child-relevant content that has been filtered into `context/shared/`.

## Steps

### Step 1: Check for shared content

Check whether `context/shared/` contains any person directories with files.

- If the directory is empty or contains no files: report "Shared context: nothing to push" and stop.
- If content exists: continue to Step 2.

### Step 2: Push each destination

Read `.claude/skills/context/SKILL-personal.md` Section 2 to get the list of destinations (local path + Drive folder name for each person).

For each destination defined there:

```
python tools/sync_context.py --direction push --source context/shared/[person] --drive-folder "[Drive folder path]"
```

Report which files were uploaded or updated for each destination.

### Step 3: Report results

Summarize what was pushed to which Drive folder(s), or report any errors with full detail.

## Notes

- One-way push: `context/shared/[person]/` → their corresponding Drive folder.
- Does **not** push all of `context/` — only the `shared/` subdirectory. The full context is in git.
- First run opens a browser OAuth window. Token is saved to `auth/token_drive.json`.
- If `auth/token_drive.json` is missing and a browser can't open, tell the user to run the tool manually in a terminal first to complete the OAuth flow.
- Existing Drive files are updated in place; new files are created. Nothing is deleted from Drive.
- Called automatically by `session-end` and `session-push` — no need to run manually unless you want an explicit sync.
