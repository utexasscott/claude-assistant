---
name: update-sheet
description: Use when pushing rows to a Google Sheet, appending new data to a sheet, updating sheet rows, or writing JSON data to a spreadsheet. Invokes update_sheet.py safely.
argument-hint: --sheet-id SHEET_ID --match-key "Column Name" --data .tmp/data.json
disable-model-invocation: true
---

## What This Skill Does

Guides the safe use of `tools/update_sheet.py` to append or update rows in any Google Sheet. Enforces a pre-flight check to prevent silent data corruption from match key collisions.

## How update_sheet.py Matches Rows

`update_sheet.py` uses the column specified by `--match-key` as its sole match key (case-insensitive, required argument).

- If the match key value already exists in the sheet → **updates that row in place**
- If the match key value is new → **appends a new row**
- All other columns are ignored for matching purposes

This means if two different rows share the same match key value, the second will silently overwrite the first. Ensure every match key value is unique across the entire sheet before pushing.

---

## Steps

### Step 1 — Read the current sheet

```
python tools/read_sheet.py --sheet-id SHEET_ID
```

Output: `.tmp/[sheet_name].json` (default) or specify with `--output`.

Extract all existing values for the match key column into memory. This is your **conflict reference list**.

Also verify the column headers at this point — they are the exact strings you must use as JSON keys.

### Step 2 — Prepare the new rows JSON

Write **only the new or changed rows** to a `.tmp/` file — not the full sheet.

**Always write JSON using Python, not shell heredoc.** Shell heredocs fail silently when data contains apostrophes (`'`) or other special characters. Use one of:

- The `Write` tool (for simple data)
- A helper `.py` script written via `Write`, then executed with `Bash`

Example helper pattern:
```python
import json
rows = [{ "Column Name": "...", ... }]
with open(".tmp/data.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)
print(f"Wrote {len(rows)} rows")
```

### Step 3 — Pre-flight conflict check

Before running the update, verify:

1. **No new entry conflicts with existing sheet rows** (case-insensitive match on the match key column)
2. **No two new entries share the same match key value** (they would overwrite each other)

```python
import json
new = json.load(open(".tmp/data.json"))
existing = json.load(open(".tmp/sheet.json"))
match_key = "Your Match Key Column"  # replace with actual column name

existing_keys = {r[match_key].strip().lower() for r in existing if match_key in r}

seen = {}
for row in new:
    key = row.get(match_key, "").strip().lower()
    if key in existing_keys:
        print(f"CONFLICT with existing: {row[match_key]}")
    if key in seen:
        print(f"DUPLICATE in new entries: {row[match_key]}")
    seen[key] = True
```

If conflicts exist, make the match key values unique before proceeding (e.g., prefix with a parent identifier).

### Step 4 — Push to the sheet

```
python tools/update_sheet.py --sheet-id SHEET_ID --match-key "Column Name" --data .tmp/data.json
```

Confirm the output shows `APPEND:` or `UPDATE:` lines as expected, and ends with `Done.`

---

## Notes

- The JSON keys must match the sheet column headers **exactly** — including spaces, capitalization, and special characters. If a key doesn't match a header, that column is silently left blank.
- `update_sheet.py` requires `auth/token_sheets.json` (Google OAuth). If missing, it will launch a browser auth flow.
- The `.tmp/` data file is only needed during the push. Clean it up afterward if it contains sensitive data.
- If the sheet has multiple tabs, use `--tab "Tab Name"` to target a specific one. Default is the first tab.
- Never push the full existing sheet back through `update_sheet.py` — it will re-match and re-write every row unnecessarily and risks overwriting data if any values changed.
