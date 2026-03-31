"""
Tool: get_emails.py
Fetches recent unread emails from a configured Gmail account.
Output: .tmp/emails_personal.json or .tmp/emails_work.json

Usage:
  python tools/get_emails.py --account personal
  python tools/get_emails.py --account work
  python tools/get_emails.py --account personal --hours 48
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "auth/credentials.json"
MAX_RESULTS = 50
PREVIEW_LENGTH = 300

URGENCY_KEYWORDS = [
    "urgent", "asap", "time-sensitive", "deadline", "by end of day",
    "by eod", "by tomorrow", "action required", "follow up", "follow-up",
    "reminder", "overdue", "please respond", "need your input",
]


def token_file(account: str) -> str:
    return f"auth/token_{account}.json"


def get_credentials(account: str):
    token_path = token_file(account)
    creds = None
    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                print("Download it from Google Cloud Console > APIs & Services > Credentials.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        Path("auth").mkdir(exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds


def decode_body(payload) -> str:
    """Extract plain text body from a Gmail message payload."""
    body = ""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    elif "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
    return body.strip()


def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def is_urgent(subject: str, snippet: str) -> bool:
    text = (subject + " " + snippet).lower()
    return any(kw in text for kw in URGENCY_KEYWORDS)


def parse_message(msg_detail) -> dict:
    payload = msg_detail.get("payload", {})
    headers = payload.get("headers", [])
    snippet = msg_detail.get("snippet", "")

    subject = get_header(headers, "subject")
    sender = get_header(headers, "from")
    date_str = get_header(headers, "date")
    is_starred = "STARRED" in msg_detail.get("labelIds", [])

    body_preview = decode_body(payload)[:PREVIEW_LENGTH]
    if not body_preview:
        body_preview = snippet[:PREVIEW_LENGTH]

    return {
        "id": msg_detail["id"],
        "subject": subject,
        "from": sender,
        "date": date_str,
        "snippet": snippet[:200],
        "body_preview": body_preview,
        "is_starred": is_starred,
        "is_urgent": is_urgent(subject, snippet),
        "label_ids": msg_detail.get("labelIds", []),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True, choices=["personal", "work"],
                        help="Which Gmail account to fetch")
    parser.add_argument("--hours", type=int, default=24,
                        help="How many hours back to look (default: 24)")
    args = parser.parse_args()

    account = args.account
    hours = args.hours
    output_file = f".tmp/emails_{account}.json"

    email_address = os.getenv(f"{'PERSONAL' if account == 'personal' else 'WORK'}_EMAIL", "")
    print(f"Fetching {account} emails ({email_address or 'address not set'}) — last {hours}h...")

    creds = get_credentials(account)
    service = build("gmail", "v1", credentials=creds)

    # Build query: unread inbox messages in last N hours, OR starred inbox messages
    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp())
    query = f"(in:inbox is:unread after:{since_ts}) OR (in:inbox is:starred is:unread)"

    try:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=MAX_RESULTS,
        ).execute()
    except HttpError as e:
        print(f"ERROR: Gmail API call failed: {e}")
        sys.exit(1)

    messages = response.get("messages", [])
    print(f"Found {len(messages)} message(s). Fetching details...")

    parsed = []
    for msg in messages:
        try:
            detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()
            parsed.append(parse_message(detail))
        except HttpError as e:
            print(f"WARNING: Could not fetch message {msg['id']}: {e}")

    # Sort: urgent/starred first, then by date
    parsed.sort(key=lambda m: (not m["is_urgent"], not m["is_starred"]))

    urgent = [m for m in parsed if m["is_urgent"]]
    starred = [m for m in parsed if m["is_starred"] and not m["is_urgent"]]
    regular = [m for m in parsed if not m["is_urgent"] and not m["is_starred"]]

    output = {
        "account": account,
        "email_address": email_address,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "hours_back": hours,
        "total": len(parsed),
        "urgent_count": len(urgent),
        "starred_count": len(starred),
        "urgent": urgent,
        "starred": starred,
        "regular": regular,
    }

    Path(".tmp").mkdir(exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(parsed)} emails to {output_file} "
          f"({len(urgent)} urgent, {len(starred)} starred)")


if __name__ == "__main__":
    main()
