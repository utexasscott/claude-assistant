# Workflow: Morning Coffee

## Objective
Start each day with a clear, grounded plan. Pull what's on the calendar, what's in the inbox, and what matters long-term — then propose a realistic daily schedule. Upon acceptance, block the day on Google Calendar.

## When to Run
Each morning, before starting work. Ideally before 9am.

## Required Inputs
- Google Calendar access (single account, may have multiple calendars)
- Personal Gmail account credentials (`token_personal.json`)
- Work Gmail account credentials (`token_work.json`)
- `context/objectives/personal_goals.md` — filled in by user
- `context/objectives/work_objectives.md` — filled in by user

## Required Environment Variables (.env)
- `PERSONAL_EMAIL` — personal Gmail address
- `WORK_EMAIL` — work/Workspace Gmail address
- `CALENDAR_ACCOUNT` — which account owns the primary calendar (`personal` or `work`)
- `CALENDAR_IDS` — comma-separated list of calendar IDs to read (e.g. `primary,work@company.com`)
- `WORK_DAY_START` — e.g. `08:00`
- `WORK_DAY_END` — e.g. `18:00`
- `SCHEDULE_DATE` — optional override; defaults to today

## Steps

### Step 1 — Read the Calendar
Run: `python tools/get_calendar_events.py`

Output saved to `.tmp/calendar_today.json`

Captures:
- All events for today across all specified calendars
- Flags: all-day events, meeting invites with other attendees, travel time blocks

Edge cases:
- If calendar auth fails, prompt user to run `python tools/auth_google.py --account calendar`
- If no events found, note that explicitly (don't assume failure)

---

### Step 2 — Read Objectives
Run: `python tools/read_objectives.py`

Output saved to `.tmp/objectives_summary.txt`

Reads:
- `context/objectives/personal_goals.md`
- `context/objectives/work_objectives.md`

Edge cases:
- If either file is empty or only contains template comments, warn the user and continue (objectives will be treated as blank)

---

### Step 3 — Read Email
Run: `python tools/get_emails.py --account personal`
Run: `python tools/get_emails.py --account work`

Output saved to:
- `.tmp/emails_personal.json`
- `.tmp/emails_work.json`

Captures unread emails from the last 24 hours, plus any marked urgent/starred. Summarizes:
- Sender, subject, one-line preview
- Flags messages that look time-sensitive (replies expected, meeting requests, deadlines mentioned)

Edge cases:
- If Gmail auth fails, prompt user to run `python tools/auth_google.py --account personal` (or `--account work`)
- Rate limits: Gmail API allows 250 quota units/second. If batch fails, fall back to individual fetches.
- If inbox is empty or no new mail, note explicitly

---

### Step 4 — Synthesize & Propose Schedule (Agent Step)
This step is handled by the agent (Claude), not a script.

**First, identify archive candidates** from both inboxes (see criteria below). Collect their message IDs — these will be archived in Step 5.

Then reason through the following:
1. What is already committed? (calendar events)
2. What is URGENT from email? (system alerts, anything on fire, time-sensitive replies)
3. What needs action today vs. can wait?
4. What should be protected time? (deep work toward objectives)

Present the plan in this format:

```
MORNING COFFEE PLAN — [Date]
================================

URGENT — ACTION NEEDED TODAY
  - [System alert / email requiring same-day response or action]
  - [Anything that could get worse if ignored today]
  (If nothing urgent: "Nothing urgent. Inbox is quiet.")

YOUR DAY AT A GLANCE
[2-3 sentence summary of today's shape]

COMMITTED
  08:00–09:00  [Calendar event]

PROPOSED BLOCKS
  09:00–11:00  [Focus] Deep work — [specific task from context/objectives/email]
  11:00–11:30  [Admin] Email triage (personal + work)
  11:30–13:00  [next block]
  13:00–14:00  Lunch / break
  15:00–17:00  [next block]
  17:00–17:30  EOD wrap-up + plan tomorrow

WATCH LIST
  - [email item that needs a response today]
  - [deadline or commitment to keep in mind]

DEFERRED
  - [things that are not making the cut today]

ARCHIVING [N emails]
  These were identified as noise and will be archived automatically upon acceptance:
  - [account] — [Sender Name] — [subject]
  - ...
```

**What counts as URGENT:**
- System/infrastructure alerts (SQS depth, error rates, failed jobs)
- Emails from real humans that mention deadlines, urgency, or are awaiting a reply
- Payment failures, account suspensions, or domain/cert expiry warnings
- Anything that gets materially worse if ignored for 24 hours

**Archive candidate criteria (auto-archive on acceptance):**
- Cold sales outreach / loan solicitations (e.g. "we can get you $385k...")
- Marketing newsletters and promotional emails the user didn't subscribe to intentionally
- Automated billing receipts for auto-charged services (no action needed)
- Automated shipping notifications (delivered, order confirmed) — unless tracking is relevant
- Old promotional emails that slipped through (check date — if starred but years old, flag for unstar)
- Platform newsletters and store loyalty programs (rewards emails, store deals, etc.)

**Do NOT archive:**
- Real humans writing directly (even if the subject is transactional)
- Anything flagged URGENT
- School/kids communications — see `context/email_triage_rules.md` for specific senders and organizations
- Bank/financial statements (user may want to file these)
- Anything the user has starred recently (within the last 30 days)

After reasoning through the plan, write `.tmp/plan.json` using this schema:

```json
{
  "date": "Weekday, Month D, YYYY",
  "urgent": ["..."],
  "day_at_a_glance": "2-3 sentence summary.",
  "committed": [
    { "time": "HH:MM–HH:MM", "summary": "Event name" }
  ],
  "proposed_blocks": [
    { "time": "HH:MM–HH:MM", "type": "Focus|Admin|Routine|Lunch", "summary": "What to work on" }
  ],
  "watch_list": ["..."],
  "deferred": ["..."],
  "archiving": [
    { "account": "personal|work", "sender": "Sender Name", "subject": "Subject line" }
  ]
}
```

Then run: `python tools/generate_plan.py`

This opens the HTML plan in the browser. Ask the user: **"Does this plan work, or would you like to adjust?"**

Accept freeform edits (move blocks, swap tasks, remove or restore archive candidates). Update `plan.json` and re-run `generate_plan.py` if changes are requested.

---

### Step 5 — Archive Emails
Run: `python tools/archive_emails.py --account personal --message-ids [ids]`
Run: `python tools/archive_emails.py --account work --message-ids [ids]`

Collect the message IDs for each archive candidate identified in Step 4, grouped by account. Run the tool once per account that has candidates.

Output: confirmation of how many emails were archived per account.

Edge cases:
- If the user removes an email from the archive list during review, do not include its ID
- If the tool errors on a specific message ID, log it and continue with the rest

---

### Step 6 — Block the Calendar
Once the user accepts the plan, run: `python tools/block_calendar.py`

Input: The accepted schedule (agent passes it as a JSON argument or writes it to `.tmp/schedule_accepted.json` first)

Creates Google Calendar events for each **PROPOSED BLOCK** (not the already-committed events). Uses a consistent color/label so they're visually identifiable as "coffee plan" blocks.

Edge cases:
- If a proposed block overlaps with an existing event, warn the user before writing. Don't silently overwrite.
- If a block title is vague, use a sensible default event title prefix: `[Focus] ` or `[Admin] `
- Confirm success by printing the event links

---

## Success Criteria
- [ ] All three data sources read without error
- [ ] Plan presented clearly and accepted by user
- [ ] Archive candidates identified and archived upon acceptance
- [ ] Calendar events created for accepted blocks
- [ ] No existing events overwritten without confirmation

## Known Constraints & Notes
- Gmail API: 250 quota units/second. Email fetch is subject to rate limits on large inboxes.
- Google Calendar: events created via API do not send notifications by default unless `sendNotifications: true` is set.
- Auth tokens expire. If a token fails, delete `auth/token_{account}.json` and re-run the tool — it will open a browser OAuth flow and save a new token. There is no `auth_google.py` script.
- `generate_plan.py` uses `auth/token_drive.json` (scope: `drive`). First run triggers a browser OAuth flow. If upload fails with a 403, delete the token and re-run to re-authorize. Files are saved inside a "Claude Morning Coffee" folder on Drive (created automatically on first run). The `drive` scope (not `drive.file`) is required so that any authorized machine can find the shared folder — `drive.file` is session-scoped and breaks on new machines.
- To view the HTML plan directly in Google Drive without downloading, install **HTML Editor for Google Drive by CloudHQ**: https://workspace.google.com/marketplace/app/html_editor_for_google_drive_by_cloudhq/533233485435 — the tool prints this reminder automatically on first run (when the Drive folder is created).
- Two Gmail accounts require two separate OAuth token files (`token_personal.json`, `token_work.json`).
- Google Calendar auth uses `auth/token_calendar.json`. Both `get_calendar_events.py` and `block_calendar.py` use the `calendar.events` scope — one token covers both tools. If auth fails, delete `auth/token_calendar.json` and re-run `get_calendar_events.py` to re-auth once.
- `block_calendar.py` passes `schedule_accepted.json`. If the tool crashes mid-run (e.g., Unicode error on Windows), only the blocks created before the crash will exist. Remove already-created blocks from `schedule_accepted.json` and re-run for the remainder.

## Improvement Log
- 2026-03-01 — Added URGENT section (first in plan), ARCHIVING section (after DEFERRED), and Step 5 archive tool step. Archive criteria defined based on first real inbox run. Archive candidates are presented to user before execution and removed from archive list if user objects.
- 2026-03-01 — Added generate_plan.py tool (Step 4b). Agent writes plan.json, tool renders styled HTML and opens in browser. Plain-text plan in chat replaced by HTML deliverable.
- 2026-03-02 — Clarified auth flow (no auth_google.py exists; delete token and re-run). Documented calendar scope mismatch: token_calendar.json must use calendar.events write scope, not calendar.readonly. Fixed Unicode crash in block_calendar.py (→ -> on Windows cp1252 console).
- 2026-03-02 — generate_plan.py now uploads HTML to Google Drive (personal account) and opens the Drive URL instead of a local file:// URI. Auth uses auth/token_drive.json with drive.file scope (least privilege — only accesses files the app creates). Local .tmp/ file is still written as a backup. Re-running on the same day updates the existing Drive file rather than creating a duplicate.
- 2026-03-02 — generate_plan.py now saves files inside a "Claude Morning Coffee" Drive folder instead of Drive root. Folder is created automatically on first run.
- 2026-03-04 — Fixed double calendar re-auth. `get_calendar_events.py` now uses `calendar.events` scope (same as `block_calendar.py`), so one token handles both tools.
