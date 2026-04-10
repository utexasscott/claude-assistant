---
name: journal
description: Use when writing a journal entry, adding to today's journal, logging something to the journal, updating a journal entry, or recording notes or observations for the day.
argument-hint: "[content or .tmp/file-path]"
metadata:
  visibility: public
---

**Personal configuration:** If `SKILL-personal.md` exists in `.claude/skills/journal/`, read it now before continuing. It contains user-specific names, section headings, narrative voice, and sharing destinations that override the generic defaults below.

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

*Named files (everything except `auto-generated.txt`):*
- Use Glob to list all files in `context/journal/raw/YYYY-MM-DD/` (excluding `.processed` and `auto-generated.txt`)
- Read `.processed` if it exists — it contains filenames already incorporated, one per line
- Exclude any file whose name appears in `.processed` from the working list

*`auto-generated.txt` (handled separately — never in `.processed`):*
- If `auto-generated.txt` exists in the raw folder, read it
- Find the last line matching `---[processed: HH:MM:SS]---`
- If found: extract only the content **after** that line — that is the new unprocessed content
- If not found: the entire file is unprocessed
- If the file doesn't exist, or all content is before the last marker (nothing new): skip it

*Pre-flight and stopping logic:*
- If no named files remain AND `auto-generated.txt` has no new content: reply "All raw files for YYYY-MM-DD have already been processed. Nothing new to add." and stop.
- Output one pre-flight line before reading anything: "Reading [N] file(s) from raw/YYYY-MM-DD/ — [file1], [file2], ...[+ auto-generated.txt (new content only)]. Writing to context/journal/YYYY-MM-DD.md. ([M] previously processed file(s) skipped.)" — omit the auto-generated clause if there's nothing new in it; omit the skipped clause if M=0.
- Read the listed files and the new portion of `auto-generated.txt`
- Proceed to Step 3.5 — do NOT create `auto-generated.txt`

**If `$ARGUMENTS` starts with `.tmp/` or ends with `.md` (file path):**
- Read content from that file path
- Proceed to Step 4 — do NOT create `auto-generated.txt`

**If content arrived as a ramble, conversation, or via agent detection (Cases 1 & 3):**
- Content is whatever the user said or the agent captured
- Proceed to Step 2a

### 2a. Detect AI conversation format

Scan the content for AI conversation structure: alternating speaker blocks with a named AI (Gemini, ChatGPT, Claude, GPT, etc.), explicit speaker labels ("[User]:", "Gemini:", etc.), or a consistent separator pattern (e.g., `--`) between turns.

**If detected:** Read `.claude/skills/journal/SKILL-ai_conversation.md` now. Its parsing and classification rules override the general categorization and prose-writing instructions in Steps 5–7. Complete the full turn-classification pass described in that file **before writing anything to the journal.**

**If not detected:** Continue to Step 3.

### 3. Write to raw file (Cases 1 & 3 only)

Save the raw input to `context/journal/raw/YYYY-MM-DD/auto-generated.txt`:
- If the file already exists, **append** to it with a blank line separator
- If the file does not exist, create it
- Write the content verbatim — no reformatting, no editorializing

This preserves the unfiltered source before any processing.

### 3.5. Interpret bracketed notes

Scan the collected content for any text in square brackets `[...]`. These are always directed at you — never part of the journal narrative. They serve one of three purposes; read each one and determine which applies:

| Type | How to recognize it | What to do |
|---|---|---|
| **Question** | Asks you to clarify something, check a fact, or confirm a detail | Stop. Ask the user before continuing. Wait for a response, then substitute the resolved content. |
| **Context / background** | Provides background information (who someone is, what something means, history) | Use it silently to inform your writing. Do not include the bracket text in the journal. |
| **Instruction** | Tells you to do something (read a file, create a file, look something up) | Execute it. Do not include the bracket text in the journal. |

If a bracket contains a question, stop and surface it before proceeding. Multiple questions can be batched in one ask. Context and instructions can be resolved without interrupting the user.

**Note:** When writing to the raw file (Step 3), always preserve the original bracket text verbatim — the raw file is the unfiltered source and should not be altered.

If no brackets are found, continue immediately.

### 4. Read the existing journal file (if it exists)

If `context/journal/YYYY-MM-DD.md` already exists, read it now. You need its current contents to make categorization and placement decisions.

### 5. Categorize the content into sections

Determine the best semantic category (or categories) for the content. Common sections (not exhaustive):

- `[Person]` — updates about a tracked individual's wellbeing, program, or interactions (see SKILL-personal.md for names and specific section labels)
- `Family` — updates about children, co-parent, extended family, or family dynamics
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

### 6a. Update the processed-files manifest (Case 2 only)

After writing the journal file, update tracking for each source type differently:

**Named files** → update `context/journal/raw/YYYY-MM-DD/.processed`:
- If the file does not exist, create it
- Append each newly processed filename, one per line (do not re-add filenames already present)
- Never include `.processed` or `auto-generated.txt` in this list

**`auto-generated.txt`** → append a timestamp marker to the file itself:
- Append a blank line followed by `---[processed: HH:MM:SS]---` (current time, 24-hour)
- This marks the boundary between what has been incorporated and any future content
- Never add `auto-generated.txt` to `.processed`

### 7. Quality: clean prose and logical order

The `.md` journal file is a polished record, not a raw transcript. When writing or reorganizing content, apply these standards:

**Chronological ordering within sections** — Unless there's a strong reason to do otherwise, arrange events in the order they happened. Don't leave "Back to that..." or "Now back to..." references in the output — weave displaced content into its proper place in the timeline.

**Clean up stream-of-consciousness artifacts** — Voice-to-text and rambled input often circles back, interrupts itself, or has filler phrases. When processing this into the journal:
- Move out-of-order content to its correct chronological position
- Remove explicit "I forgot to mention" or "going back to earlier" bridges — just place the content where it belongs
- Preserve the substance and voice, not the navigational asides

**Preserve all meaning** — Do not summarize, compress, or drop details. The goal is reorganization and light cleanup, not reduction.

**Use natural prose** — Write in flowing paragraphs within sections. Reserve bullet points for lists (action items, skill references, etc.) rather than narrative events.

**Resolution summaries for progressive reasoning** — When a section builds through a chain of analysis where the key conclusion or decision arrives late in the narrative, add a **Resolution** summary block immediately after the section heading, before the prose. Format it as a blockquote:

```
> **Resolution:** [2–4 sentences capturing the settled conclusion, clinical implication, or decision reached.]
```

Apply this when: the section is long and the payoff is at the end, the reasoning loops back multiple times before landing, or the section would be opaque to a first-time reader without knowing where it ends up. Skip it for short sections, purely narrative accounts (what happened), or sections where the conclusion is obvious from the first paragraph.

### 8. Update shared context

If `SKILL-personal.md` defines a sharing configuration, check whether the entry contains content relevant to each configured destination. If it does, create or update the shared context file at the path specified in `SKILL-personal.md`, following the format defined in `.claude/skills/context/SKILL-personal.md` Section 2.

**Important:** The shared entry must be derived from the polished journal file (`context/journal/YYYY-MM-DD.md`), never from raw source files. "Verbatim from the journal entry" means the cleaned, chronologically-ordered `.md` file — not the raw dictation. This ensures the shared entry inherits the polished prose and never contains navigational asides ("Back to that phone call...", "Now back to...") that belong only in the raw files.

If no sharing configuration is defined, or the entry contains no relevant content, skip this step.

**Do not update `context/profiles/` in this step.** Profile routing is handled by the background agents spawned in Step 9.

### 9. Confirm and offer

Reply with one short line confirming what was written, to which date's entry, and which section(s) were affected. Do not restate the content.

Then ask: "Run background analysis? (psychoanalysis + profiles) (y/n)"

If yes: spawn all three agents in parallel with `run_in_background: true`:

```
Agent 1 — psychoanalysis:
Task: "Run psychoanalysis for YYYY-MM-DD. Read all files in context/journal/raw/YYYY-MM-DD/ and follow your instructions."

Agent 2 — profile-updater:
Task: "Run profile update for YYYY-MM-DD. Read context/journal/YYYY-MM-DD.md and follow your instructions."

Agent 3 — biography-extractor:
Task: "Run biography extraction for YYYY-MM-DD. Read context/journal/YYYY-MM-DD.md and follow your instructions."
```

Confirm all three were spawned. Note that:
- Psychoanalysis writes to `context/psychoanalysis/scott_north/YYYY-MM-DD.md`
- Profile and biography proposals write to `.tmp/YYYY-MM-DD_profile_proposals.md` and `.tmp/YYYY-MM-DD_biography_proposals.md` for review

If no: do nothing. Run `/profile-update` to run profile agents manually.

---

## When the Agent Generates the Narrative

When a workflow instructs you to journal a conversation (rather than logging verbatim content), you are authoring the entry. Write it this way:

- **Third-person prose** — "The user talked about...", "The conversation turned to...", "They mentioned..." (see SKILL-personal.md for the user's name and preferred pronoun)
- **Capture texture and detail** — don't compress or summarize. If the user described a specific moment or exchange, write it with enough detail that it reads as a coherent account, not a summary.
- **Don't editorialize** — record what happened and what was said. Avoid interpreting motives or adding analysis unless it was spoken explicitly.
- **Capture all meaningful content** — significant updates or disclosures, emotional moments or shifts in tone, decisions made or being wrestled with, anything that would be meaningful to read back later.

---

## When Logging an AI Response

When the user asks to add an AI response to the journal (e.g., "add your response to the journal," "log that AI answer," "save what you said"), follow these rules:

**Section heading:** `## [Topic] — AI Response`

**Attribution callout:** Open the section with this exact callout, italicized:

> *⚠️ AI-generated response. The analysis below was produced by [AI Name], not the user. The user found it helpful and added it to the record, but it may contain errors, overreach, or clinically unverified claims. It should be read as a thinking tool, not ground truth.*

**Why this matters:** AI analysis and the user's own words are epistemically different. The user's thoughts are primary; AI responses are auxiliary thinking tools that may misrepresent facts, draw incorrect inferences, or introduce claims the user never made. The attribution callout ensures that when this entry is read back later, the distinction is clear and the AI-generated content is weighted appropriately.

**What to include:** The AI response text, faithfully reproduced. Do not editorialize, summarize, or clean it up beyond light formatting. The content should be recognizable as what was actually said.

**Shared context:** Do not propagate AI-attributed sections into shared context files (e.g., the shared journal). AI responses belong in the private journal only.

---

## Notes

- `context/journal/` is gitignored. Never commit journal files.
- The `raw/` subfolder follows the same gitignore and is also never committed.
- When logging verbatim content passed via a file path argument, write it as-is — no reformatting.
- When processing raw input (Cases 1 & 3), you write twice: once raw to `auto-generated.txt`, once cleaned to the `.md` file.
- Use `##` for category headings. Do not use `###` or deeper nesting unless the content itself calls for it.
- Separate sections with a blank line. Do not use `---` horizontal rules between sections.
