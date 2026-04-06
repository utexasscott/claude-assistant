# Agent Instructions

> **Personal extensions:** If `CLAUDE-personal.md` exists in this directory, **read it now** before continuing. It contains personal configuration and context rules that extend the generic instructions below.

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Skills (Claude Code Slash Commands)**
- Stored in `.claude/skills/[name]/SKILL.md` and invoked with `/skill-name`
- Reusable capability modules that extend your role as agent — think of them as named, documented subroutines
- When a skill exists for a task, invoke it rather than improvising the same logic from scratch
- Always invoke `/skill-builder` when creating or modifying any skill — never bypass it. This applies even mid-conversation: if the user says "you should always...", "from now on...", "next time...", or any feedback that would change a skill's behavior, pause and invoke `/skill-builder` before making any changes to a SKILL.md file.
- Always invoke `/context` before writing to any context profile file (i.e., any `context/` file outside of `context/journal/`) — it is a quality gate, not optional; journal entries are written directly by the `/journal` skill, which invokes `/context` only when updating profile files
- Always invoke `/read-journal` before responding whenever the user uses temporal language — "today," "yesterday," "this week," "recently," "earlier," or any specific date. This applies in all workflows, not just journal sessions. The journal is the ground truth for recent events; don't respond to time-relative questions without it.
- Update skills when their behavior needs to change — don't work around an outdated skill, fix it
- Skills are committed to the repo and must contain no sensitive data

**Session Sync**
- `/session-start` — pull latest from the private repo. Run at the start of every session on any device.
- `/session-end` — security scan + push to private repo + push to public repo + push shared Drive files. Run when done. Accepts an optional commit message.
- `/git-push` and `/git-pull` — underlying primitives available for ad-hoc use. Requires `gh` CLI authenticated (`gh auth login`).

**Sharing to Google Drive**
- Personal context is tracked in the private GitHub repo — Drive is used **for sharing only**, not backup
- `/push` — push `context/shared/` destinations to their Google Drive folders. Sharing destinations are defined in `.claude/skills/context/SKILL-personal.md`. Called automatically by session-end.
- Sharing destinations and Drive folder names are defined in `.claude/skills/context/SKILL-personal.md` Section 2
- Auth token: `auth/token_drive.json` (created on first run via browser OAuth flow)

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**0. Check for a matching workflow first**
Before doing anything else, read `workflows/_index.md` and find the workflow that matches the user's request. If one matches, read that workflow completely before taking any action. Do not improvise steps that a workflow already defines — even if the task seems obvious.

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.claude/
  skills/[name]/SKILL.md       # Claude Code slash commands — committed, no sensitive data.
.tmp/                          # Temporary files. Regenerated as needed. Gitignored.
auth/                          # Google OAuth — gitignored.
context/                       # All personal data — tracked in private repo; gitignored in public repo.
context_example/               # Shareable templates — committed to git, no personal data.
tools/                         # Python scripts for deterministic execution. Committed.
workflows/
  _index.md                    # Personal route table — gitignored in public repo.
  _example/                    # Example _index.md template — committed.
  public/                      # Shareable SOPs — committed to git, no sensitive data.
  private/                     # Sensitive SOPs — gitignored in public repo.
CLAUDE.md                      # Generic agent instructions — committed, public-safe.
CLAUDE-personal.md             # Personal extensions — committed to private repo only.
.env                           # API keys and credentials — NEVER committed.
```

**Core principle:** The private GitHub repo is the source of truth for all content, including personal context. Everything in `.tmp/` is disposable. Google Drive is used only for outbound sharing with specific people.

**Git safety:** The public repo contains no personal data, credentials, or sensitive context:
- `context/` — tracked in the private repo; gitignored in the public repo
- `context_example/` — committed; templates only, never fill in real data here
- `workflows/public/` — committed; must contain no personal details
- `workflows/private/` and `workflows/_index.md` — gitignored in the public repo
- `CLAUDE-personal.md` — committed to the private repo only; never included in public pushes
- `.env`, token files — never committed

Everything else — tools, public workflows, skills, and example templates — should be safe to commit and share at any time. Never put sensitive content in a committed path, even temporarily.

**What counts as personal data:** Proper nouns tied to a specific person — names of their children's schools, medical providers, therapy programs, team or club memberships, specific organizations, email addresses, and phone numbers. Generic role-based references are fine in public workflows (e.g., "school communications", "the user's work account"). Specific institution names are not — those belong in `context/`. When creating or editing a public workflow, run a quick scan for proper nouns before writing.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
