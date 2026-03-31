---
name: read-journal
description: Use when reading journal entries, reviewing recent journal, loading journal context, or checking what was written in the journal recently.
argument-hint: "[YYYY-MM-DD | number of days]"
metadata:
  visibility: public
---

## What This Skill Does

Reads recent journal entries from `context/journal/` and outputs their contents to the conversation. Called by workflows (like `life_update`) to load recent context before a session, or directly when the user wants to review past entries.

---

## Steps

### 1. Determine which dates to read

Check `$ARGUMENTS`:

| Condition | Dates to read |
|---|---|
| No argument | Today and yesterday |
| Argument is a date (e.g., `2026-03-25`) | Only that date |
| Argument is a number (e.g., `3`) | Today and the N−1 days before today (i.e., last N days) |

Use today's date from the `currentDate` context variable.

### 2. Read each journal file

For each date in the list:
- Construct the path: `context/journal/YYYY-MM-DD.md`
- Attempt to read the file
- If the file does not exist, silently skip it — do not mention missing files unless none were found at all

### 3. Output the contents

For each file that was found:
- Output a short header: `## Journal — YYYY-MM-DD`
- Output the full contents of the file below it
- Do not summarize, reformat, or editorialize the contents

### 4. Confirm

End with one short line stating which entries were found (e.g., "Loaded journal entries for 2026-03-25 and 2026-03-26."), or if none were found, note that no entries exist for the requested range.

---

## Notes

- `context/journal/` is gitignored. These files are personal and private.
- Do not modify any journal file contents when reading.
- If called by a workflow (not directly by the user), skip the confirmation line — just output the contents so the workflow can use them as context.
