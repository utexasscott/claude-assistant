---
name: journal
description: Use when writing a journal entry, adding to today's journal, logging something to the journal, updating a journal entry, or recording notes or observations for the day.
argument-hint: "[content or .tmp/file-path or YYYY-MM-DD]"
metadata:
  visibility: public
---

**Personal configuration:** Read `SKILL-personal.md` in `.claude/skills/journal/` before continuing. It contains user-specific names, section headings, narrative voice, and sharing destinations.

---

## What This Skill Does

Creates or appends to a daily journal entry at `context/journal/YYYY-MM-DD.md`. Organizes content into well-structured, logically-ordered sections. Maintains raw source files in `context/journal/raw/YYYY-MM-DD/` for voice-to-text input and external AI conversations.

File reading and writing is delegated to the `journal-writer` agent to protect the main context window from large raw files. This skill handles orchestration only: date resolution, pre-flight, metadata, and background analysis.

---

## Input Sources

| Source | Description | Raw file? |
|---|---|---|
| **Ramble / direct input** | User speaks or types thoughts directly in conversation | Yes → `auto-generated.txt` |
| **Read raw files** | User asks to process files from `context/journal/raw/YYYY-MM-DD/` | No (files already exist) |
| **Agent-detected** | Another workflow determines something should be journaled | Yes → `auto-generated.txt` |

---

## Steps

### 1. Determine the target date

- Default: today's date in `YYYY-MM-DD` format.
- If `$ARGUMENTS` contains a date (e.g., `2026-03-25`), use that date instead.
- **Active window (past 10 days):** journal file at `context/journal/YYYY-MM-DD.md`, raw folder at `context/journal/raw/YYYY-MM-DD/`
- **Archived (older than 10 days):** journal file at `context/journal/archive/YYYY-MM-DD.md`, raw folder at `context/journal/archive/raw/YYYY-MM-DD/`

### 2. Identify input source and run pre-flight

**Case 2 — processing raw files** (user says "process" or "read raw files"):

- Glob all files in `context/journal/raw/YYYY-MM-DD/` (excluding `.processed` and `auto-generated.txt`)
- Read `.processed` if it exists — filenames already incorporated, one per line
- Determine new named files: everything not in `.processed`
- Check `auto-generated.txt` for new content: the section after the last `---[processed: HH:MM:SS]---` marker (or all content if no marker)
- **Stop condition:** If no new named files AND no new auto-generated content, reply "All raw files for YYYY-MM-DD have already been processed. Nothing new to add." and stop.
- Output one pre-flight line: `"Reading [N] file(s) from raw/YYYY-MM-DD/ — [file1], [file2], ...[+ auto-generated.txt (new content only)]. Writing to context/journal/YYYY-MM-DD.md. ([M] previously processed file(s) skipped.)"` — omit clauses that don't apply.
- **Do not read file contents.** The journal-writer agent handles that.

**Cases 1 & 3 — ramble or agent-detected content:**

- Write the content verbatim to `context/journal/raw/YYYY-MM-DD/auto-generated.txt` (append with a blank line separator if the file already exists; create it if not). Write verbatim — no reformatting.
- Treat the situation as Case 2 from here: the file is now in the working set.

**File path argument** (`$ARGUMENTS` starts with `.tmp/` or ends with `.md`):

- Note the file path — no raw file handling needed.
- Input type = C (verbatim file content); pass the path to the agent.

### 3. Resolve header metadata

Resolve these three values before spawning the writer agent. Do not read any raw journal files to do this.

- **Day of week:** Compute from the target date.
- **Location:** Read `context/locations.md`. Scan each entry's `**Scott's stays:**` sub-bullets for a date range containing the target date (start ≤ target AND end > target OR no end date). Use the `##` heading of the matching entry. If no match: `[location unknown]`.
- **With:** Check the most recent prior journal entry's `**With:**` header field (within the past 3 days). If not found or older than 3 days: ask the user — "Who are you currently staying with?" — and wait. See SKILL-personal.md for guidance on who counts as "with."

If the existing journal file already has a complete metadata line (all three fields populated), carry those values forward unchanged — no need to re-resolve.

### 4. Spawn the journal-writer agent

Spawn the `journal-writer` agent (foreground, not background) with this handoff. Substitute all bracketed values:

```
## Journal Writer Handoff

**Date:** YYYY-MM-DD
**Day:** [weekday]
**Location:** [location name from locations.md, or "[location unknown]"]
**With:** [names or "alone"]

**Input type:** [A = raw files / B = narrative (auto-generated.txt) / C = file path]

**New files to process:**
- [full path to each new named file, one per line]
(none — if no new named files)

**auto-generated.txt:** [new content exists / no new content / does not exist]

**File path (Type C only):** [path, or omit]

**Already-processed files (skip):** [list, or "none"]

**Existing journal:** [exists at context/journal/YYYY-MM-DD.md / does not exist]
```

Pass only this structured handoff — the journal-writer agent reads its own instructions. Do not add writing guidelines, style instructions, or format rules to the handoff.

Wait for the agent to complete before proceeding. Do not proceed to Step 5 until it finishes.

### 5. Handle agent output flags

Review the agent's output for flags before reporting to the user:

- **`⚠️ QUESTION REQUIRED: [...]`** — Surface the question to the user. Wait for their answer. Re-invoke the `journal-writer` agent with the same handoff plus a `## Resolved bracket questions` section containing the answer. Repeat until no question flags remain.
- **`⚠️ LOCATION CHANGE DETECTED: [...]`** — Invoke `/locations` to record the move. After `/locations` completes, edit the journal header's `**Location:**` field to reflect the actual location on the target date.

If no flags: proceed immediately.

### 6. Confirm and offer background analysis

Reply with one short line confirming what was written, to which date's entry, and which section(s) were affected. Do not restate the content.

Then ask: "Run background analysis? (psychoanalysis + profiles) (y/n)"

If yes: spawn all three agents in parallel with `run_in_background: true`:

```
Agent 1 — psychoanalysis (subagent_type: "psychoanalysis"):
"Run psychoanalysis for YYYY-MM-DD. Read all files in context/journal/raw/YYYY-MM-DD/ and follow your instructions."

Agent 2 — profile-updater (subagent_type: "profile-updater"):
"Run profile update for YYYY-MM-DD. Read context/journal/YYYY-MM-DD.md and follow your instructions."

Agent 3 — biography-extractor (subagent_type: "biography-extractor"):
"Run biography extraction for YYYY-MM-DD. Read context/journal/YYYY-MM-DD.md and follow your instructions."
```

Confirm all three were spawned. Notes:
- Psychoanalysis writes to `context/psychoanalysis/scott_north/YYYY-MM-DD.md`
- Profile proposals write to `.tmp/YYYY-MM-DD_profile_proposals.md`
- Biography proposals write to `.tmp/YYYY-MM-DD_biography_proposals.md`

If no: do nothing. Run `/profile-update` to run profile agents manually.

---

## Notes

- `context/journal/` is gitignored. Never commit journal files. The `raw/` subfolder follows the same rule.
- Use `##` for category headings. Do not use `###` or deeper nesting unless the content calls for it.
- Separate sections with a blank line. Do not use `---` horizontal rules between sections.
