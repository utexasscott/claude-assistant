# Workflow: Security Sweep

## Objective

Audit files for two distinct threats, depending on what is being swept:

1. **Credential leak** — secrets or API keys accidentally committed to git (applies to any committed file in the private repo)
2. **Personal data leak** — PII or user-specific proper nouns in files that get synced to the public repo

These threats have different scopes and must be checked separately.

## The Dual-Repo Structure

This project uses two GitHub repos:

| Repo | Purpose | What goes there |
|------|---------|-----------------|
| **Private repo** (personal-assistant) | Source of truth; all personal context | Everything, including `context/`, `CLAUDE-personal.md`, private workflows, agents |
| **Public repo** (claude-assistant) | Shareable skeleton | Whitelisted skills, public workflows, tools, CLAUDE.md, context_example/ |

The sync from private → public is done by `tools/push_public.sh`, which:
- Copies only whitelisted skills (see `PUBLIC_SKILLS` array in that script)
- Copies `tools/`, `workflows/public/`, `workflows/_example/`, `context_example/`, `CLAUDE.md`
- Strips all `SKILL-personal.md` files automatically
- Does NOT copy `.claude/agents/`, `context/`, `workflows/private/`, `CLAUDE-personal.md`

**Agents are private by design.** `.claude/agents/` is not synced to the public repo. Agent files may contain user-specific names and paths — that is expected and acceptable.

## Sweep Modes

### Brief mode (pre-push)
Scope: only files that are staged or modified and about to be committed.
Purpose: fast pre-commit gate, called automatically by session-end.
Source files: `git status --porcelain` + `git diff --name-only HEAD`

### Thorough mode (full audit)
Scope: all files currently tracked by git.
Purpose: periodic hygiene check or ad-hoc review of the full repo state.
Source files: `git ls-files`

---

## Steps

### Step 1 — Identify files to sweep

**If brief mode:**
Run: `git status --porcelain` and `git diff --name-only HEAD`
Combine and deduplicate the file paths. If both return nothing, output "Brief scan: nothing staged or modified — scan skipped" and stop.

**If thorough mode:**
Run: `git ls-files`

From the file list, split into two buckets:

**Bucket A — Private-repo-only paths** (credential scan only):
- `context/`
- `workflows/private/`
- `workflows/_index.md`
- `CLAUDE-personal.md`
- `.claude/agents/`
- `.claude/skills/*/SKILL-personal.md`

**Bucket B — Public-repo paths** (both credential scan AND personal data scan):
- `workflows/public/`
- `workflows/_example/`
- `context_example/`
- `tools/`
- `.claude/skills/` (excluding SKILL-personal.md files, which go in Bucket A)
- `CLAUDE.md`
- `README.md`

Skip gitignored paths entirely — they are never committed: `auth/`, `.env`, `.tmp/`

If both buckets are empty after filtering, confirm "Scan: no relevant files — skipped" and stop.

---

### Step 2 — Credential scan (all files in both buckets)

For every file in Bucket A and Bucket B:

**For Python files (`.py`), flag:**
- `subprocess` with `shell=True` and unsanitized input (command injection)
- Unvalidated file path arguments (path traversal)
- Hardcoded secrets, API keys, or tokens
- `eval`/`exec` with external input
- YAML/pickle deserialization with untrusted data
- f-string interpolation of external data into HTML (HTML injection)

**For all other files, flag:**
- Hardcoded secrets, API keys, tokens, or passwords
- `.env`-style `KEY=VALUE` patterns with real values

Only report findings with >80% confidence of being real credentials, not placeholder examples or template variables.

---

### Step 3 — Personal data scan (Bucket B only)

Read each file in Bucket B. Flag any instance of:

**High-risk — always flag:**
- Full names of real people (first + last, or a nickname that uniquely identifies someone)
- Names of schools, medical providers, treatment programs, or activity organizations tied to a specific person
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
- The public repo URL itself (`github.com/...`)

---

### Step 4 — Present findings

Always present results as a findings table, even if empty:

```
## Credential Findings

| File | Line | Content | Risk | Proposed Fix |
|------|------|---------|------|-------------|
| tools/example.py | 12 | api_key = "sk-abc123" | High | Move to .env, load via os.environ |

## Personal Data Findings (public-path files only)

| File | Line | Content | Risk | Proposed Fix |
|------|------|---------|------|-------------|
| workflows/public/example.md | 42 | Specific School Name | High | Generalize to "the user's school" |
```

If a bucket is clean, write "No findings" under that section header.

After presenting findings, propose one of the following for each item:
- **Generalize** — replace the specific name/value with a role-based description
- **Move to context** — extract to an appropriate `context/` file and replace with a generic reference or a comment pointing to context
- **Move to SKILL-personal.md** — if it's a config value that belongs with a specific skill
- **Move to .env** — for hardcoded credentials or API keys
- **Dismiss** — if the user confirms it's intentional public data (rare)

Do not make any changes until the user reviews and approves each proposed fix.

---

### Step 5 — Remediate (if approved)

For each confirmed finding:

**If generalizing:**
Replace the specific name with a role-based placeholder. If the value is needed to make the workflow useful, add a note directing users to supply their own value via `context/` or `SKILL-personal.md`.

**If moving to context:**
1. Identify or create the correct `context/` file
2. Add the personal data in the appropriate section with a brief label
3. Update the source file: replace the specific name with a generic description and add a comment like `# See context/[file].md for personal values`

**If moving to .env:**
1. Add the variable to `.env` (never commit this file)
2. Update the script to use `os.environ.get("VAR_NAME")` or equivalent

After all remediations, run `git diff` and show the full diff for review.

---

### Step 6 — Verify

For each originally flagged term, confirm removal:

Run: `git ls-files | xargs grep -rn "[flagged term]"` (thorough mode)
Or: check only the modified files (brief mode)

If any instance remains in a committed path, surface it and ask the user how to handle it.

---

### Step 7 — Identify public promotion candidates (thorough mode only)

Skip this step entirely in brief mode.

For each file in **Bucket A** (private-only paths), assess whether it could be safely promoted to Bucket B (public-synced) with little or no changes. A file is a promotion candidate if ALL of the following are true:

1. The PII scan found no personal data in it
2. The content is generic and reusable — it would be useful to someone else running this framework
3. It is not an agent file (`.claude/agents/`) — agents are inherently user-specific and should never be promoted

For skill files (`.claude/skills/*/SKILL.md`) that are candidates:
- Proposed action: set `metadata.visibility: public` and add to `PUBLIC_SKILLS` in `tools/push_public.sh`

For workflow files in `workflows/private/` that are candidates:
- Proposed action: move to `workflows/public/` and update any references

Present as a separate section after the findings table:

```
## Public Promotion Candidates

| File | Type | Reason it qualifies | Proposed action |
|------|------|--------------------|----|
| .claude/skills/foo/SKILL.md | skill | No personal data; generic workflow | Add to PUBLIC_SKILLS; set visibility: public |
| workflows/private/bar.md | workflow | No personal data; generic SOP | Move to workflows/public/ |
```

If no candidates: write "No promotion candidates found."

Do not promote anything automatically. The user must confirm each candidate before any changes are made.

---

## Success Criteria
- [ ] Credential scan run on all committed files in scope
- [ ] Personal data scan run on all public-path files in scope
- [ ] Findings table presented to user
- [ ] All confirmed findings remediated
- [ ] No flagged terms remain in public-path files
- [ ] `git diff` reviewed before any push
- [ ] (thorough only) Promotion candidates table presented to user

## Known Constraints & Notes
- Gitignored paths (`context/`, `.env`, `auth/`, `.tmp/`) are excluded — personal data is expected and acceptable there
- `.claude/agents/` is private-only and not synced to the public repo — agent files may contain user-specific names by design; flag credentials but not personal references in these files
- The credential scan is pattern-based and may miss obfuscated secrets. Treat findings as a floor, not a ceiling.
- This workflow does not replace the public/private classification check at authoring time. That check happens when creating new workflows or skills. This workflow catches anything that slipped through.

## Improvement Log
- 2026-03-03 — Workflow created. Triggered by personal organization names found in a public workflow.
- 2026-03-27 — Added pre-push mode to Step 1. Scopes sweep to only files being committed.
- 2026-04-06 — Full rewrite. Added dual-repo structure context, renamed modes to brief/thorough, split credential scan from personal data scan, added Bucket A/B classification, clarified agent file handling. Added Step 7: public promotion candidates (thorough mode only).
