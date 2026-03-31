# Workflow: Check Email

## Objective
Get a clear, actionable picture of both inboxes. Identify what's urgent, what needs a response, what to watch, and what can be archived. Produce an HTML report on Google Drive and archive noise on acceptance.

## When to Run
Anytime you want a focused inbox triage without running the full morning coffee workflow. Useful mid-day, after returning from time away, or whenever the inbox feels out of control.

## Required Inputs
- Personal Gmail account credentials (`token_personal.json`)
- Work Gmail account credentials (`token_work.json`)

## Required Environment Variables (.env)
- `PERSONAL_EMAIL` — personal Gmail address
- `WORK_EMAIL` — work/Workspace Gmail address

## Steps

### Step 1 — Read Email
Run: `python tools/get_emails.py --account personal`
Run: `python tools/get_emails.py --account work`

Output saved to:
- `.tmp/emails_personal.json`
- `.tmp/emails_work.json`

Captures unread emails from the last 24 hours, plus any marked urgent/starred. Each message includes sender, subject, snippet, urgency flag, and starred status.

Edge cases:
- If Gmail auth fails, prompt user to delete the relevant token file and re-run the tool — it will open a browser OAuth flow.
- If inbox is empty or no new mail, note explicitly
- Rate limits: Gmail API allows 250 quota units/second. If batch fails, fall back to individual fetches.

---

### Step 2 — Triage & Synthesize (Agent Step)
This step is handled by the agent (Claude), not a script.

Read both `.tmp/emails_personal.json` and `.tmp/emails_work.json`. For each email, classify it into one of:
- **URGENT** — needs same-day action
- **Watch** — needs a reply or action but not today
- **Read** — no action required, informational
- **Archive** — noise, can be auto-archived

Then write `.tmp/email_report.json` using this schema:

```json
{
  "date": "Weekday, Month D, YYYY",
  "personal_total": 0,
  "work_total": 0,
  "urgent": [
    "Description of urgent item (account — sender — why it's urgent)"
  ],
  "personal_emails": [
    { "sender": "Sender Name", "subject": "Subject line", "action": "Reply today|Watch|Read|Archive" }
  ],
  "work_emails": [
    { "sender": "Sender Name", "subject": "Subject line", "action": "Reply today|Watch|Read|Archive" }
  ],
  "watch_list": [
    "Item needing attention in the next day or two"
  ],
  "archiving": [
    { "account": "personal|work", "id": "gmail_message_id", "sender": "Sender Name", "subject": "Subject line" }
  ]
}
```

**What counts as URGENT:**
- System/infrastructure alerts (SQS depth, error rates, failed jobs)
- Emails from real humans that mention deadlines, urgency, or are awaiting a reply
- Payment failures, account suspensions, or domain/cert expiry warnings
- Anything that gets materially worse if ignored for 24 hours

**Archive candidate criteria (auto-archive on acceptance):**
- Cold sales outreach / loan solicitations
- Marketing newsletters and promotional emails the user didn't subscribe to intentionally
- Automated billing receipts for auto-charged services (no action needed)
- Automated shipping notifications (delivered, order confirmed) — unless tracking is relevant
- Platform newsletters and store loyalty programs (rewards emails, store deals, etc.)

**Do NOT archive:**
- Real humans writing directly (even if the subject is transactional)
- Anything flagged URGENT or Watch
- School/kids communications — see `context/email_triage_rules.md` for specific senders and organizations
- Bank/financial statements (user may want to file these)
- Anything the user has starred recently (within the last 30 days)

After writing `email_report.json`, run: `python tools/generate_email_report.py`

This renders an HTML report, uploads it to the "Claude Email Check" Drive folder, and opens it in the browser.

Ask the user: **"Does this look right, or would you like to adjust before I archive?"**

Accept freeform edits (remove emails from archive list, reclassify items). Update `email_report.json` and re-run `generate_email_report.py` if changes are requested.

---

### Step 3 — Archive Emails
Once the user accepts the report, archive the identified emails.

Run: `python tools/archive_emails.py --account personal --message-ids [ids]`
Run: `python tools/archive_emails.py --account work --message-ids [ids]`

Collect message IDs from `email_report.json["archiving"]`, grouped by account. Run the tool once per account that has candidates.

Output: confirmation of how many emails were archived per account.

Edge cases:
- If the user removes an email from the archive list during review, do not include its ID
- If the tool errors on a specific message ID, log it and continue with the rest
- If no archive candidates, skip this step

---

## Success Criteria
- [ ] Both inboxes read without error
- [ ] Every email classified (Urgent / Watch / Read / Archive)
- [ ] HTML report opened on Drive
- [ ] Archive candidates reviewed and confirmed by user
- [ ] Emails archived

## Known Constraints & Notes
- Gmail API: 250 quota units/second. Email fetch is subject to rate limits on large inboxes.
- Two Gmail accounts require two separate OAuth token files (`token_personal.json`, `token_work.json`).
- `generate_email_report.py` uses `auth/token_drive.json` (scope: `drive`). First run triggers a browser OAuth flow. If upload fails with a 403, delete the token and re-run to re-authorize.
- Drive files are saved inside a "Claude Email Check" folder (separate from "Claude Morning Coffee"). Folder is created automatically on first run.
- Re-running on the same day updates the existing Drive file rather than creating a duplicate.

## Improvement Log
- 2026-03-02 — Workflow created. Focused email-only triage, separate from morning coffee. HTML report uploads to "Claude Email Check" Drive folder.
