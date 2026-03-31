# Workflow: Security Sweep

## Objective
Audit all committed files for accidentally included personal information. Identify names, institutions, organizations, or other personal details that should live in `context/` instead of public committed paths. Remediate findings by moving data to context files and updating references.

## When to Run
- On demand when you suspect a committed file contains personal details
- After adding any new file to a committed path (`workflows/public/`, `.claude/skills/`, `tools/`, `context_example/`, `CLAUDE.md`, `README.md`)
- Periodically as a routine hygiene check before pushing to GitHub

## Required Inputs
None. This workflow operates on the repository itself.

---

## Steps

### Step 1 — Identify files to sweep

This workflow operates in one of two modes:

**On-demand mode** (default — invoked directly or as a routine hygiene check):
Run: `git ls-files`
Returns every file currently tracked by git. Filter to committed paths only (see list below).

**Pre-push mode** (invoked from session-end or git-push, when only changed files should be reviewed):
Run: `git status --porcelain` and `git diff --name-only HEAD`
Combine results to get the set of files being added or modified in the upcoming commit. Filter to committed paths only (see list below). If both commands return nothing, there is nothing to scan — confirm "Pre-push scan: nothing to commit, scan skipped" and stop.

**Committed paths to sweep (both modes):**
- `workflows/public/`
- `.claude/skills/`
- `context_example/`
- `tools/`
- `CLAUDE.md`
- `README.md`

Exclude gitignored paths — `context/`, `workflows/private/`, `auth/`, `.env`, `.tmp/` — personal data is expected and acceptable there.

Edge cases:
- If the filtered file list is empty in pre-push mode, confirm "No files in committed paths are changing — security scan skipped" and stop.
- If `git ls-files` or `git status` shows unexpected files in committed paths, flag them before proceeding — they may have been accidentally staged.

---

### Step 2 — Sweep for personal data (Agent Step)

Read each file in the committed paths listed above. Flag any instance of:

**High-risk — always flag:**
- Names of schools, medical providers, treatment programs, or activity organizations tied to a specific person
- Full names of real people (first + last, or a nickname that uniquely identifies someone)
- Email addresses or phone numbers belonging to real people
- Scouting pack numbers, sports team names, or club names that identify a specific person's activities
- Account or service names that reveal personal usage patterns

**Medium-risk — flag and review:**
- First names used as personal identifiers in a context that reveals private details
- Specific business names that would reveal the user's identity if combined with other public info
- Hardcoded values in tools that belong in `.env` or `context/`

**Not personal data — skip:**
- Generic templates and placeholder text (in `context_example/`)
- Technical names: API service names, Python packages, tool filenames
- Geographic references at city level or above ("Austin TX" is fine)
- Role references without names ("user's child", "work account", "school communications")

Write a findings table:

```
| File | Line | Content | Risk | Proposed Fix |
|------|------|---------|------|-------------|
| workflows/public/example.md | 42 | Specific School Name | High | Move to context/file.md, replace with generic reference |
```

If no findings: confirm "No personal data found in committed paths" and stop.

---

### Step 3 — Review findings with user

Present the findings table and proposed fixes. For each item, propose one of:

- **Move to context**: Extract to an appropriate `context/` file and update the source to use a generic reference or a comment pointing to context
- **Generalize**: Replace the specific name/value with a role-based description (e.g., replace [school name] with `school communications`)
- **Dismiss**: If the user confirms it's intentional public data (rare — most proper nouns are personal)

Do not make any changes until the user reviews and approves each proposed fix.

---

### Step 4 — Remediate (Agent Step)

For each confirmed finding:

**If moving to context:**
1. Identify the correct `context/` file (e.g., `context/email_triage_rules.md` for email-related rules, a family file for person-specific details)
2. Read the target file, or create it if it doesn't exist
3. Add the personal data in the appropriate section with a brief label
4. Update the source file: replace the specific name with a generic description and add a comment like `# See context/[file].md for personal values`
5. Confirm both edits before writing

**If generalizing:**
1. Replace the specific name with a role-based placeholder
2. If the specific names are needed to make the workflow useful, add a note in `## Known Constraints & Notes` directing the user to fill in their own values in context

After all remediations, run: `git diff` to show the full diff of changes made.

---

### Step 5 — Verify

For each originally flagged term, confirm removal:

Run: `git ls-files | xargs grep -rn "[flagged term]"`

If any instance remains in a committed path, surface it and ask the user how to handle it.

Re-read each modified file to confirm no new personal data was introduced during editing.

---

## Success Criteria
- [ ] All committed files swept for personal data
- [ ] Findings table presented and reviewed by user
- [ ] All confirmed findings remediated (moved to context or generalized)
- [ ] Source files updated with generic references or context pointers
- [ ] No flagged terms remain in committed paths
- [ ] `git diff` reviewed by user before any push

## Known Constraints & Notes
- This workflow only covers committed files. Gitignored paths (`context/`, `.env`, `auth/`, `workflows/private/`) are excluded by design — personal data is expected there.
- The sweep in Step 2 is an agent step and depends on pattern recognition. It may miss subtle PII (e.g., a business name that indirectly identifies the user). Treat findings as a floor, not a ceiling.
- When creating `context/` files to store extracted data, follow the naming conventions in `context/` — lowercase, underscores, grouped by topic.
- This workflow does not replace the public/private classification check in `create_workflow.md`. That check happens at authoring time. This workflow catches anything that slipped through.

## Improvement Log
- 2026-03-03 — Workflow created. Triggered by personal organization names (school and activity names) found in `workflows/public/check_email.md`.
- 2026-03-27 — Added pre-push mode to Step 1. Scopes the sweep to only files being committed rather than all tracked files. Prevents unnecessary scanning when no relevant files are changing.
