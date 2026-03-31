---
name: journal
description: Use when writing a journal entry, adding to today's journal, logging something to the journal, updating a journal entry, or recording notes or observations for the day.
argument-hint: "[content or .tmp/file-path]"
metadata:
  visibility: public
---

## What This Skill Does

Creates or appends to a daily journal entry at `context/journal/YYYY-MM-DD.md`. Organizes content into semantic sections so the journal reads as structured notes rather than a rambling stream. Called by the user directly or invoked by workflows that need to log output to the journal.

---

## Steps

### 1. Determine the target date

- Default: today's date in `YYYY-MM-DD` format.
- If `$ARGUMENTS` contains a date (e.g., `2026-03-25`), use that date instead.
- Target file: `context/journal/YYYY-MM-DD.md`

### 2. Determine the content to write

Check `$ARGUMENTS`:

| Condition | Action |
|---|---|
| Argument starts with `.tmp/` or ends with `.md` | Read content from that file path |
| Argument is non-empty text (not a file path) | Use it directly as the content |
| No argument provided | Ask the user: "What would you like to add to today's journal?" |

If reading from a file: read the full contents of the file.

### 3. Read the existing journal file (if it exists)

If `context/journal/YYYY-MM-DD.md` already exists, read it now. You need its current contents to make the categorization decision in step 4.

If the file does not exist, proceed to step 5 (new file).

### 4. Categorize the new content

Determine the best semantic category for the new content. Use your judgment based on the topic. Common categories (not exhaustive):

- `Myla` — updates about Myla's program, mental health, behavior, or your interactions with her
- `Family` — updates about other children, ex-spouse, extended family, or family dynamics
- `Health` — gym, physical health, sleep, personal wellness
- `Relationships` — dating, friendships, social connection, intimacy
- `Work / Projects` — professional work, the personal assistant project, business matters
- `Reflection` — introspective thoughts, emotional processing, mindset observations
- `Morning Brief` — output from the morning workflow
- `Email` — draft or sent correspondence captured for reference
- Any other label that clearly fits the content

If the content already has a section heading (e.g., `## Morning Brief`), use that as the category — do not assign a different one.

### 5. Decide how to write the content

**First: assess whether the existing file needs restructuring.**

If the existing file has unstructured or monolithic content (e.g., a single blob section like `## Life Update` that mixes multiple topics), restructure it into proper `## [Category]` sections before placing the new content. Preserve every word — only reorganize, do not rewrite or summarize.

Then place the new content using the first rule that matches:

| Situation | Action |
|---|---|
| **File does not exist** | Create the file with `# YYYY-MM-DD` header and a `## [Category]` section |
| **No matching section in existing file** | Append a new `## [Category]` section at the end of the file |
| **Matching section exists AND new content updates or supersedes existing content** (e.g., a corrected count, a changed status, a reversed decision) | Edit the existing section in place to incorporate the update |
| **Matching section exists AND new content is additive** (new events, new thoughts, additional detail) | Append the new content within or directly after the existing section, not at the bottom of the file |

**Merge vs. append judgment:**
- *Update in place* when the new content renders the existing text stale or incorrect (e.g., self-harm count changed, program status changed, a decision was reversed).
- *Append within section* when the new content is a new event, new thought, or additional context — it doesn't invalidate what's already there.
- When in doubt, append within the section rather than modifying existing text.

### 6. Confirm

Reply with one short line confirming what was written, to which date's entry, and which section was affected. Do not restate the content.

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
- When logging verbatim content (passed in via `$ARGUMENTS` or a file), write it as-is — no reformatting or editorializing.
- When editing an existing section, preserve surrounding content exactly. Only touch what needs to change.
- Use `##` for category headings. Do not use `###` or deeper nesting unless the content itself calls for it.
- Separate sections with a blank line. Do not use `---` horizontal rules between sections.
