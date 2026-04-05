# Workflow: Onboarding

## Objective
Walk a new user through the full WAT framework setup — collect personal context, configure the environment, authenticate Google APIs, and verify everything works. When complete, the user should be able to run any public workflow immediately.

## When to Run
Once, when a user first clones the repository. Can be re-run to update context or fix broken auth.

## Required Inputs
- None upfront — this workflow gathers everything interactively

## Steps

---

### Step 1 — Assess Current State (Agent Step)

Before asking any questions, check what already exists:

- `.env` — does it exist? If yes, is it still a copy of `.env.example` (unfilled)?
- `auth/credentials.json` — does it exist?
- `auth/` token files — do any exist?
- `context/` — are there any filled profile files (non-example)?
- `context/objectives/personal_goals.md` — does it exist and contain real content?
- `workflows/_index.md` — does it exist?

Tell the user what's already set up and what we'll be doing. Then proceed section by section. **Don't front-load all the questions at once** — go phase by phase, explain what each section is for, then ask.

---

### Step 2 — Google Cloud Setup (Agent Step, skip if `auth/credentials.json` exists)

If `auth/credentials.json` is missing, guide the user through creating it:

Explain to the user:
> The WAT framework uses Google APIs to read your calendar, email, and optionally Google Keep. You'll need a Google Cloud project with OAuth credentials to authorize access. This takes about 5 minutes and you only do it once.

Walk them through these steps (provide this as a numbered list they can follow):

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com) and sign in with the Google account you'll be using.
2. Create a new project (or use an existing one). Name it something like `morning-coffee` or `wat-framework`.
3. In the left sidebar, go to **APIs & Services → Library**. Search for and enable each of these APIs:
   - **Gmail API**
   - **Google Calendar API**
   - **Google Sheets API** (needed for any workflows that read/write spreadsheets)
4. Go to **APIs & Services → OAuth consent screen**.
   - Choose **External** (unless you're on Google Workspace, in which case choose Internal).
   - Fill in App name (e.g., `WAT Framework`), your email for support and developer contact.
   - Add your own email to **Test users** — this is required for external apps in testing mode.
   - Click Save and Continue through the scopes screen (no custom scopes needed here).
5. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**
   - Name: `WAT Desktop Client` (or anything)
   - Click Create.
6. Click **Download JSON** on the credential that appears. Save the downloaded file as `auth/credentials.json` in this project directory.

Ask the user to confirm when `auth/credentials.json` is in place before proceeding.

Edge cases:
- If the user has a Google Workspace account (company email), guide them to choose "Internal" on the consent screen — no test user step needed.
- If they get a "This app isn't verified" warning during OAuth later, they should click "Advanced → Go to [app name] (unsafe)" — this is expected for personal/developer projects.

---

### Step 3 — Environment Configuration (Agent Step)

Collect the following information conversationally. Ask in groups — don't fire them all at once.

**Group A — Email accounts:**
- What is your personal Gmail address?
- Do you have a work Gmail or Google Workspace email? If yes, what is it?

**Group B — Calendar:**
- Which account should be treated as your primary calendar — personal or work?
- Do you have any shared calendars you want to include (e.g., a family calendar, a partner's calendar)? If yes, ask them to go to **Google Calendar → Settings → [Calendar name] → Calendar ID** and share those IDs.
- What are your typical work hours? (e.g., 8am–6pm)
- What timezone are you in? (IANA format — e.g., `America/Chicago`, `America/New_York`, `America/Los_Angeles`, `America/Denver`, `Europe/London`)

**Group C — Google Keep (optional, for meal planning):**
- Do you use Google Keep? The meal planning workflow can push grocery lists to a Keep note.
- If yes: what is the title of the note you want to use as a shopping list? (default: `Shopping`)

Once all answers are collected, write `.env` by copying `.env.example` and filling in the values:

```
PERSONAL_EMAIL=[answer]
WORK_EMAIL=[answer or leave blank]
CALENDAR_ACCOUNT=[personal or work]
CALENDAR_IDS=primary[,additional IDs if provided]
WORK_DAY_START=[HH:MM]
WORK_DAY_END=[HH:MM]
TIMEZONE=[answer]
SCHEDULE_DATE=
KEEP_EMAIL=[personal email]
KEEP_MASTER_TOKEN=
KEEP_SHOPPING_NOTE_TITLE=[answer or Shopping]
KEEP_GROCERY_STORE_SECTION=[your store section header]
```

If work email is blank, set `WORK_EMAIL=` and note that the work Gmail auth step will be skipped.

---

### Step 4 — Personal Profile (Agent Step)

Explain:
> Your personal profile lives in `context/` and gives me long-running context about who you are — so I don't start from scratch every conversation.

Collect the following:

- **Name:** What's your full name?
- **Location:** City and state/country?
- **Pronouns:** (he/him, she/her, they/them, or skip)
- **Household:** Who do you live with? Any kids or dependents? (brief — we can add detailed family profiles later)
- **Work:** What do you do for work? (role, employer, or type of business)
- **Personal projects:** Any side projects or goals you're actively working on? Status and rough time budget per week?
- **Fitness:** Any regular fitness habits or equipment?
- **Constraints:** What limits your time or attention? What do you always want to protect in your schedule?
- **Preferences:** Anything specific about how you want me to work with you?

Use the answers to write `context/[firstname_lastname].md` (snake_case, lowercase) based on `context_example/profile.md`. Keep the same section structure as the template.

---

### Step 5 — Objectives (Agent Step, Optional)

Ask:
> Do you want to set up your objectives files now? These feed directly into the morning planning workflow — I use them to suggest what to work on each day. You can always fill them in later.

If yes, collect:

**Personal goals:**
- What are 2–3 meaningful things you want to accomplish this year?
- What are you focused on this quarter?
- Any daily or weekly non-negotiables (habits, exercise, family time)?

**Work objectives:**
- What's your main professional focus right now?
- Any specific projects or deliverables on the horizon?

Write both files from the templates in `context_example/objectives/`, placed at:
- `context/objectives/personal_goals.md`
- `context/objectives/work_objectives.md`

If the user skips this, note it in the success summary — they'll see blank objectives the first time they run morning coffee.

---

### Step 6 — Family Context (Agent Step, Optional)

Ask:
> Do you have family members or close relationships you'd like me to track context on — kids, a partner, parents? This helps with gift ideas, scheduling, and keeping up with what's going on in their lives.

If yes:
- Walk through `context_example/profiles/family_overview.md` — fill in household structure and any children/dependents in the table.
- For each person they want a detailed profile on, copy `context_example/profiles/child.md` to `context/profiles/[firstname_lastname].md` and fill it in with whatever they share.

If no, skip.

---

### Step 7 — Create Workflow Index (Agent Step)

Check if `workflows/_index.md` exists. If not, create it:

```markdown
# Workflow Index

Read this file first to find the right workflow. Then read that workflow before acting.

| Workflow | Triggers |
|---|---|
| `public/morning_coffee.md` | morning planning, daily plan, what's on my calendar, check emails, today's schedule |
| `public/plan_meals.md` | meal plan, plan meals, plan this week, grocery list, what should I cook |
| `public/create_workflow.md` | create a workflow, new workflow, add a workflow, define a process, formalize a task |
| `public/onboarding.md` | onboarding, setup, initialize, first time setup, configure |
```

If it already exists, leave it alone.

---

### Step 8 — Authenticate Google APIs (Tool Steps)

Tell the user:
> Now we'll authenticate your Google accounts. A browser window will open for each account. Sign in and click Allow — then come back here.

**Step 8a — Calendar:**
Run: `python tools/get_calendar_events.py`

This triggers OAuth for the calendar account. A browser will open. The user signs in and grants access. Token saved to `auth/token_calendar.json`.

Edge cases:
- If the browser doesn't open automatically, the tool will print a URL — copy/paste it into a browser.
- If the user gets a "This app isn't verified" screen: click Advanced → Go to [app name].

**Step 8b — Personal Gmail:**
Run: `python tools/get_emails.py --account personal`

Token saved to `auth/token_personal.json`.

**Step 8c — Work Gmail (skip if no work email configured):**
Run: `python tools/get_emails.py --account work`

Token saved to `auth/token_work.json`.

**Step 8d — Google Keep (skip if KEEP_EMAIL is blank or user opted out):**
Run: `python tools/setup_keep_auth.py`

This is interactive — follow the on-screen instructions. The tool prints a master token. Copy it into `.env` as `KEEP_MASTER_TOKEN=`.

Edge cases for all auth steps:
- If auth fails partway through, delete the relevant `auth/token_*.json` file and re-run the tool.
- If the user sees a scope mismatch error later (e.g., when blocking calendar), delete `auth/token_calendar.json` and re-authenticate — the token needs `calendar.events` write scope, not read-only.

---

### Step 9 — Verify Setup (Agent Step)

Check that the following files were created:
- `auth/token_calendar.json`
- `auth/token_personal.json`
- `.tmp/calendar_today.json` (from Step 8a)
- `.tmp/emails_personal.json` (from Step 8b)

If all present: report success and give the user a quick summary of what's now ready.

Present a summary like:

```
WAT FRAMEWORK — SETUP COMPLETE
================================
Profile:      context/[name].md ✓
Environment:  .env ✓
Calendar:     Authenticated ✓ ([N] events found for today)
Personal email: Authenticated ✓ ([N] emails fetched)
Work email:   [Authenticated ✓ | Skipped — no work email configured]
Google Keep:  [Authenticated ✓ | Skipped — run setup_keep_auth.py when ready]
Objectives:   [Set up ✓ | Not set up — fill in context/objectives/ before running morning coffee]
Family:       [Set up ✓ | Not set up — add profiles to context/profiles/ anytime]

READY TO USE
You can now run any of these workflows:
  • "Run my morning coffee" — daily planning
  • "Plan meals for the week" — meal planning (requires Google Keep)
  • "Create a workflow for [task]" — define a new SOP

Refer to workflows/_index.md for the full list.
```

If anything failed: identify which step failed, describe what to fix, and offer to retry that step.

---

## Success Criteria
- [ ] `auth/credentials.json` exists
- [ ] `.env` is populated with real values (not placeholder text)
- [ ] `context/[name].md` exists with filled-in profile
- [ ] `auth/token_calendar.json` exists and `.tmp/calendar_today.json` was created
- [ ] `auth/token_personal.json` exists and `.tmp/emails_personal.json` was created
- [ ] `workflows/_index.md` exists
- [ ] User has been shown what workflows are available

## Known Constraints & Notes
- Google OAuth tokens expire after a period. If a tool fails auth later, delete the relevant `auth/token_*.json` file and re-run the tool.
- The `auth/` directory is gitignored — tokens stay on this machine only. Each user authenticates independently.
- `.env` is gitignored — never committed. Each user fills in their own.
- Personal context files in `context/` are gitignored. Only `context_example/` is shared.
- `workflows/_index.md` is gitignored — each user maintains their own route table.
- Google Keep auth (`setup_keep_auth.py`) uses an unofficial API and may break if Google changes the Keep auth flow. Skip it if meal planning isn't needed.
- If a user has two-factor auth on their Google account (they should), the OAuth flow handles it — no special steps needed.
- Windows users: if OAuth fails to open a browser, try running the tool from a terminal (not within VSCode's embedded terminal) or copy the printed URL manually.

## Improvement Log
- 2026-03-02 — Initial version created.
