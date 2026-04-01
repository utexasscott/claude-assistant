---
name: journal
description: Use when writing a journal entry, adding to today's journal, logging something to the journal, updating a journal entry, or recording notes or observations for the day.
argument-hint: "[content or .tmp/file-path]"
metadata:
  visibility: public
---

## What This Skill Does

Creates or appends to a daily journal entry at `context/journal/YYYY-MM-DD.md`. Organizes content into well-structured, logically-ordered sections. Maintains raw source files in `context/journal/raw/YYYY-MM-DD/` for voice-to-text input and external AI conversations. Called by the user directly or invoked by workflows that need to log output to the journal.

---

## Input Sources

There are three ways content arrives:

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
- Target journal file: `context/journal/YYYY-MM-DD.md`
- Target raw folder: `context/journal/raw/YYYY-MM-DD/`

### 2. Identify the input source and collect content

**If the user asked to read raw files (Case 2):**
- Read the specified file(s) from `context/journal/raw/YYYY-MM-DD/`
- If no specific file is named, read all files in that folder
- Proceed to Step 4 — do NOT create `auto-generated.txt`

**If `$ARGUMENTS` starts with `.tmp/` or ends with `.md` (file path):**
- Read content from that file path
- Proceed to Step 4 — do NOT create `auto-generated.txt`

**If content arrived as a ramble, conversation, or via agent detection (Cases 1 & 3):**
- Content is whatever the user said or the agent captured
- Proceed to Step 3

### 3. Write to raw file (Cases 1 & 3 only)

Save the raw input to `context/journal/raw/YYYY-MM-DD/auto-generated.txt`:
- If the file already exists, **append** to it with a blank line separator
- If the file does not exist, create it
- Write the content verbatim — no reformatting, no editorializing

This preserves the unfiltered source before any processing.

### 4. Read the existing journal file (if it exists)

If `context/journal/YYYY-MM-DD.md` already exists, read it now. You need its current contents to make categorization and placement decisions.

### 5. Categorize the content into sections

Determine the best semantic category (or categories) for the content. Common sections (not exhaustive):

- `Myla` — updates about Myla's program, mental health, behavior, or interactions with her
- `Family` — updates about other children, ex-spouse, extended family, or family dynamics
- `Health` — gym, physical health, sleep, personal wellness
- `Relationships` — dating, friendships, social connection, intimacy
- `Work / Projects` — professional work, the personal assistant project, business matters
- `Reflection` — introspective thoughts, emotional processing, mindset observations
- `Morning Brief` — output from the morning workflow
- `Email` — draft or sent correspondence captured for reference
- Any other label that clearly fits

If the content already has a section heading (e.g., `## Morning Brief`), use that — do not assign a different one.

A single input may contain content that belongs in multiple sections. Split it accordingly.

### 6. Write or update the journal file

**First: assess whether the existing file needs restructuring.**

If the existing file has unstructured or monolithic content (e.g., a single `## Life Update` blob mixing multiple topics), restructure it into proper `## [Category]` sections before placing the new content. Preserve every word — only reorganize.

**Then place new content using the first rule that matches:**

| Situation | Action |
|---|---|
| **File does not exist** | Create the file with `# YYYY-MM-DD` header and `## [Category]` section(s) |
| **No matching section in existing file** | Append a new `## [Category]` section at the end |
| **Matching section exists AND new content updates or supersedes existing** (corrected count, changed status, reversed decision) | Edit the existing section in place |
| **Matching section exists AND new content is additive** (new events, new thoughts, additional detail) | Append within or directly after the existing section |

**Merge vs. append judgment:**
- *Update in place* when new content renders existing text stale or incorrect.
- *Append within section* when new content is a new event, thought, or additional context.
- When in doubt, append within the section.

### 7. Quality: clean prose and logical order

The `.md` journal file is a polished record, not a raw transcript. When writing or reorganizing content, apply these standards:

**Chronological ordering within sections** — Unless there's a strong reason to do otherwise, arrange events in the order they happened. Don't leave "Back to that..." or "Now back to..." references in the output — weave displaced content into its proper place in the timeline.

**Clean up stream-of-consciousness artifacts** — Voice-to-text and rambled input often circles back, interrupts itself, or has filler phrases. When processing this into the journal:
- Move out-of-order content to its correct chronological position
- Remove explicit "I forgot to mention" or "going back to earlier" bridges — just place the content where it belongs
- Preserve the substance and voice, not the navigational asides

**Preserve all meaning** — Do not summarize, compress, or drop details. The goal is reorganization and light cleanup, not reduction.

**Use natural prose** — Write in flowing paragraphs within sections. Reserve bullet points for lists (action items, skill references, etc.) rather than narrative events.

### 8. Update shared context

After writing, check whether the entry contains content about the children: Myla, Davis, Arlo, or Kayleigh. If it does, create or update `context/shared/allison/journal/YYYY-MM-DD.md` following the format in `context/context_policy.md` Section 2.

If the entry contains no child-relevant content, skip this step.

### 9. Confirm

Reply with one short line confirming what was written, to which date's entry, and which section(s) were affected. Do not restate the content.

---

## When the Agent Generates the Narrative

When a workflow instructs you to journal a conversation (rather than logging verbatim content), you are authoring the entry. Write it this way:

- **Third-person prose** — "Scott talked about...", "The conversation turned to...", "He mentioned..."
- **Capture texture and detail** — don't compress or summarize. If Scott described a specific moment or exchange, write it with enough detail that it reads as a coherent account, not a summary.
- **Don't editorialize** — record what happened and what was said. Avoid interpreting motives or adding analysis unless it was spoken explicitly.
- **Capture all meaningful content** — significant updates or disclosures, emotional moments or shifts in tone, decisions made or being wrestled with, anything that would be meaningful to read back later.

---

## Notes

- `context/journal/` is gitignored. Never commit journal files.
- The `raw/` subfolder follows the same gitignore and is also never committed.
- When logging verbatim content passed via a file path argument, write it as-is — no reformatting.
- When processing raw input (Cases 1 & 3), you write twice: once raw to `auto-generated.txt`, once cleaned to the `.md` file.
- Use `##` for category headings. Do not use `###` or deeper nesting unless the content itself calls for it.
- Separate sections with a blank line. Do not use `---` horizontal rules between sections.
