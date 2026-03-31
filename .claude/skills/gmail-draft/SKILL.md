---
name: gmail-draft
description: >
  Use when someone asks to create a Gmail draft, save an email to Gmail drafts,
  push a draft to Gmail, or draft an email in Gmail. NEVER sends the email —
  always saves to Drafts only.
argument-hint: "[draft-file-path] [personal|work]"
metadata:
  visibility: public
---

## What This Skill Does

Pushes a local email draft file into Gmail Drafts using either the personal or work account.
Does **not** send the email under any circumstances.

## Dependencies

- **Script:** `tools/create_draft.py`
- **Accounts:** Personal (`PERSONAL_EMAIL`) or Work (`WORK_EMAIL`) from `.env`
- **Auth tokens:** `auth/token_personal_draft.json` or `auth/token_work_draft.json` (created on first run via OAuth)
- **Draft files:** `.tmp/email_draft_*.txt` — format: first line `Subject: ...`, blank line, then body

## Account Resolution

Determine which account to use by checking these sources in order — stop at the first match:

1. **Explicit argument** — account passed directly in the invocation (e.g., `/gmail-draft .tmp/foo.txt personal`)
2. **Draft file header** — if the draft file contains `Account: personal` or `Account: work` as a header line (after `Subject:`), use it
3. **Active workflow declaration** — if currently executing a workflow that declares `Email account: personal` or `Email account: work` in its metadata, use that
4. **Conversation context** — if replying to or following up on an email that was fetched from a known inbox (e.g., the email appeared in `.tmp/emails_personal.json` or `.tmp/emails_work.json`), use that inbox's account
5. **Ask the user** — if none of the above resolves it unambiguously, ask: *"Should this be drafted from your personal or work Gmail?"*

## Steps

### 1 — Identify the draft file

If a path is provided as an argument, use it directly.

If no argument is given:
- List files matching `.tmp/email_draft_*.txt`
- If exactly one exists, use it and tell the user which file you're pushing
- If multiple exist, list them and ask the user which one to push
- If none exist, tell the user no draft file was found and ask them to provide a path

### 2 — Resolve the account

Apply the Account Resolution logic above to determine `personal` or `work`.

### 3 — Confirm before running

Show the user:
- The file path being used
- The account being used (e.g., `From: personal (your-name@gmail.com)`)
- The subject line (read the first line of the file)

Then run without further prompting.

### 4 — Run the tool

```
python tools/create_draft.py --account [personal|work] --draft [draft-file-path]
```

Do NOT add `--to` unless the user has explicitly provided a recipient address in this conversation.

### 5 — Confirm success

On success, report:
- Draft created successfully
- The account it was drafted from
- The Gmail Draft ID returned by the script
- Reminder: "Open Gmail > Drafts to add a recipient and review before sending."

On failure, show the full error output and stop. Do not retry automatically.

## Hard Rules

- **Never** add `--to` unless the user explicitly provides an address
- **Never** run `tools/send_email.py` — that sends; this skill only drafts
- **Never** retry on failure — report the error and wait for instructions
- **Always** confirm the resolved account with the user during Step 3 so they can catch mistakes before the draft is created
