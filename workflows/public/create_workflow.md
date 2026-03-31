# Workflow: Create a New Workflow

## Objective
Design and write a new workflow file that fits the WAT framework conventions. Capture the intent, define the steps clearly, build or verify all required tools, confirm all environment variables are in place, and register it in the index — so the workflow is fully ready to run the first time it's triggered.

## When to Run
When the user wants to add a new repeatable process to the WAT system — whether it's a new daily routine, a new data pipeline, a new research or planning task, or any other recurring activity they want formalized.

---

## Required Inputs
- A description of the desired workflow (what it does, what triggers it, what it should produce)
- Any known constraints, tools, or services involved

No credentials or environment variables are required for this workflow itself.

---

## Steps

### Step 1 — Clarify intent

Before drafting anything, make sure you have clear answers to these questions. Ask the user for any that aren't already answered:

1. **What is this workflow for?** What task or process does it automate or define?
2. **What triggers it?** When should this workflow be run — on a schedule, on demand, in response to an event?
3. **What are the inputs?** What data, files, credentials, or user-provided context does it need?
4. **What are the outputs?** What does success look like — a file, a calendar event, a cloud update, a decision?
5. **Are there known edge cases?** Things that might go wrong or vary from run to run?
6. **Public or private?** Will this workflow contain any personal data, names, account details, or sensitive context — or is it fully generic?
   - **Public** (`workflows/public/`) — committed to git; must contain zero personal data; safe to share as-is
   - **Private** (`workflows/private/`) — gitignored; may contain personal details, account info, or sensitive context
   - When in doubt, default to **private**. Do not guess. This must be answered before Step 3.

Don't move to Step 2 until the objective, expected outputs, and public/private classification are unambiguous.

---

### Step 2 — Check for duplicates and existing tools

Before drafting:

1. Read `workflows/_index.md` — confirm no existing workflow already covers this.
2. Scan `tools/` — note which existing scripts are relevant to this workflow. The draft should reference these by name.

If a duplicate exists, surface it to the user and ask whether they want to extend the existing workflow instead of creating a new one.

---

### Step 3 — Draft the workflow (agent step)

Write the workflow using the standard structure:

```
# Workflow: [Name]

## Objective
[One paragraph. What this does and why.]

## When to Run
[Trigger or schedule.]

## Required Inputs
[List of files, credentials, env vars, or user-provided context.]

## Required Tools
[List each tool by filename and one line describing what it does.]
- `tools/script_name.py` — [what it does and what it outputs]

## Required Environment Variables (.env)
[Only if applicable. List variable names and what they represent.]

## Steps

### Step 1 — [Name]
[What happens. Whether it's a tool call or an agent step. Exact command if tool-based. What it produces.]

Edge cases:
- [What could go wrong and how to handle it]

---

[Repeat for each step.]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Known Constraints & Notes
[Rate limits, auth quirks, timing assumptions, or anything non-obvious.]

## Improvement Log
<!-- Date — what changed and why -->
```

**Conventions to follow:**
- Steps that run Python scripts use `Run: python tools/script_name.py [args]` and specify the output file.
- Steps handled by the agent (reasoning, synthesis, presenting options) are labeled **(Agent Step)** and spell out the logic explicitly — don't say "figure it out," say what to look for and how to decide.
- Edge cases are inline under the step that triggers them, not consolidated at the bottom (unless there are many — then use a table under `## Edge Cases`).
- Avoid vague language like "as needed" or "handle appropriately." Every step should be specific enough that following it produces a consistent result.

**Before presenting: run a personal data check (public workflows only)**

If the workflow is classified as public, review the draft for anything that could identify a real person to an outside reader:

- Names of specific schools, medical providers, therapy programs, or activity organizations
- Full names of real people
- Email addresses, phone numbers, or account identifiers
- Scouting pack numbers, sports team names, or club names tied to a specific person
- Hardcoded values that belong in `.env` or `context/`

For any match:
- Replace the specific name with a role-based description (e.g., "school communications" instead of the school name), OR
- Move the values to an appropriate `context/` file and reference it: `# See context/[file].md for personal values`

A workflow can reference personal categories (e.g., "school communications") without naming specific institutions. When in doubt, move it to context.

Present the draft to the user and ask:
> "Does this capture what you had in mind? Anything to adjust before I write the file?"

Do not proceed to Step 4 until the draft is approved.

---

### Step 4 — Audit and build required tools

Walk every tool listed in the `## Required Tools` section of the approved draft:

1. For each tool, check whether it exists in `tools/`:
   - **Exists**: Read it and confirm it covers the required functionality. Note any mismatches (wrong output format, missing args, etc.). Surface gaps to the user before editing any existing tool.
   - **Does not exist**: Draft and create it now. Follow existing tool conventions:
     - Docstring at the top: tool name, what it does, usage, output file
     - `argparse` for CLI args
     - `load_dotenv()` for env vars
     - Output to `.tmp/` as JSON or plaintext
     - Print a clear success or error message on completion

2. If a tool requires OAuth on first run (Google APIs, etc.), note this explicitly and add it to the new workflow's `## Known Constraints & Notes` section.

3. If a tool requires external API credentials you don't have context for, create a stub with clear `# TODO:` markers and document what's needed in the workflow.

4. Summarize to the user:
   - Which tools already existed and were verified
   - Which tools were created
   - Which tools (if any) need manual review or edits before running

---

### Step 5 — Audit environment variables

Read `.env` and compare it against the `## Required Environment Variables` section of the draft:

1. Check whether `.env` exists at all. If it's missing, flag this prominently — no tool will run without it. Do not proceed with the audit.

2. For each required variable, report its status:
   - ✓ **Set** — key exists and has a non-empty, non-placeholder value
   - ⚠ **Placeholder** — value matches the `.env.example` default (e.g., `you@gmail.com`, empty string)
   - ✗ **Missing** — key is not present in `.env`

3. Treat `VAR=` (empty value) the same as missing.

4. If any tool in the workflow uses Google OAuth, check whether the required credential and token files exist:
   - `credentials.json` — must exist before any OAuth flow can run
   - `token_*.json` — generated on first auth run; note if absent so the user knows to expect an auth prompt

5. Do NOT write to `.env` automatically. Report the gaps clearly and tell the user what values are needed and where to find them.

6. If all variables are set and credentials are in place, confirm the workflow is ready to run.

---

### Step 6 — Write the file and update the index

Once the draft is approved and Steps 4–5 are complete:

1. Write the workflow file to the correct path based on the public/private classification confirmed in Step 1:
   - **Public**: `workflows/public/[filename].md`
   - **Private**: `workflows/private/[filename].md`

   Use a short, lowercase, underscore-separated filename that matches the workflow name (e.g., `sync_inventory.md`).

2. Update `workflows/_index.md`:
   - If `_index.md` does not exist, create it by copying `workflows/_example/_index.md`, then clear its example rows (keep the header and column definitions only).
   - Add a row for the new workflow, using the full relative path:

```
| `workflows/public/[filename].md`  | [trigger phrases that should route here] |
| `workflows/private/[filename].md` | [trigger phrases that should route here] |
```

Use 3–5 natural-language trigger phrases — the kinds of things the user might actually say to kick this workflow off.

Confirm when both files are written.

---

## Success Criteria
- [ ] Workflow intent is unambiguous before drafting begins
- [ ] No duplicate workflow exists (or user has chosen to extend instead)
- [ ] Draft reviewed and approved by user before writing
- [ ] All required tools exist and are verified (or created)
- [ ] All required environment variables are set, or gaps reported clearly to the user
- [ ] Workflow file written to `workflows/`
- [ ] `_index.md` updated with the new entry

## Known Constraints & Notes
- Do not create or overwrite workflow files without explicit user approval of the draft first (Step 3 gate).
- Do not edit existing tools without surfacing the change to the user first.
- Do not write to `.env` — report gaps only.
- Filenames should be descriptive but concise. Avoid dates or version numbers in filenames.
- This workflow is itself an example of the format it defines — treat it as a reference.

## Improvement Log
<!-- 2026-03-01 — Added Step 4 (audit/build required tools), Step 5 (audit env vars), Required Tools section to draft template, and expanded Success Criteria to cover readiness verification -->
