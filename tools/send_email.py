"""
Tool: send_email.py
Sends an email via Gmail from a pre-approved draft file.

Draft file format:
  Subject: Some subject line

  Body text here...

Uses a separate token file (token_{account}_send.json) to avoid scope
conflicts with the readonly token used by get_emails.py.

Usage:
  python tools/send_email.py --account personal --draft .tmp/email_draft_program.txt --to admissions@example.com
"""

import argparse
import base64
import os
import sys
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "auth/credentials.json"


def token_file(account: str) -> str:
    # Separate token from get_emails.py (which uses readonly scope)
    return f"auth/token_{account}_send.json"


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


def parse_draft(draft_path: str) -> tuple[str, str]:
    """
    Parse a draft file into (subject, body).
    Expects first line to be 'Subject: ...' followed by an optional blank line,
    then the body. Exits with error if subject or body is missing.
    """
    text = Path(draft_path).read_text(encoding="utf-8").strip()
    lines = text.splitlines()

    subject = ""
    body_start = 0

    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0][len("subject:"):].strip()
        body_start = 1
        # Skip one blank line after the subject header if present
        if body_start < len(lines) and lines[body_start].strip() == "":
            body_start += 1

    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True, choices=["personal", "work"],
                        help="Which Gmail account to send from")
    parser.add_argument("--draft", required=True,
                        help="Path to draft text file")
    parser.add_argument("--to", required=True,
                        help="Recipient email address")
    args = parser.parse_args()

    _project_root = Path(__file__).parent.parent.resolve()
    if not str(Path(args.draft).resolve()).startswith(str(_project_root)):
        print(f"ERROR: Path outside project directory: {args.draft}")
        sys.exit(1)

    if not Path(args.draft).exists():
        print(f"ERROR: Draft file not found: {args.draft}")
        sys.exit(1)

    subject, body = parse_draft(args.draft)
    if not subject:
        print("ERROR: Draft file has no 'Subject:' line as the first line.")
        sys.exit(1)
    if not body:
        print("ERROR: Draft file body is empty.")
        sys.exit(1)

    env_key = "PERSONAL_EMAIL" if args.account == "personal" else "WORK_EMAIL"
    sender = os.getenv(env_key, "")
    if not sender:
        print(f"ERROR: {env_key} not set in .env")
        sys.exit(1)

    print(f"Sending from: {sender}")
    print(f"To:           {args.to}")
    print(f"Subject:      {subject}")
    print("-" * 40)
    print(body)
    print("-" * 40)

    creds = get_credentials(args.account)
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = args.to
    message["from"] = sender
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()
        print("Email sent successfully.")
    except HttpError as e:
        print(f"ERROR: Gmail send failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
