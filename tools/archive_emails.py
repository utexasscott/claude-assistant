"""
Tool: archive_emails.py
Archives Gmail messages by removing them from the inbox (INBOX label).
Does not delete — messages remain searchable in All Mail.

Usage:
  python tools/archive_emails.py --account personal --message-ids id1,id2,id3
  python tools/archive_emails.py --account work --message-ids id1,id2,id3
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = "auth/credentials.json"


def token_file(account: str) -> str:
    # Separate token from get_emails.py (which is readonly).
    # gmail.modify is a broader scope and requires its own auth grant.
    return f"auth/token_{account}_modify.json"


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
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        Path("auth").mkdir(exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds


def archive_message(service, message_id: str) -> bool:
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["INBOX"]},
        ).execute()
        return True
    except HttpError as e:
        print(f"  WARNING: Could not archive {message_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True, choices=["personal", "work"],
                        help="Which Gmail account to use")
    parser.add_argument("--message-ids", required=True,
                        help="Comma-separated list of message IDs to archive")
    args = parser.parse_args()

    account = args.account
    message_ids = [mid.strip() for mid in args.message_ids.split(",") if mid.strip()]

    if not message_ids:
        print("No message IDs provided. Nothing to do.")
        sys.exit(0)

    print(f"Archiving {len(message_ids)} message(s) from {account} account...")

    creds = get_credentials(account)
    service = build("gmail", "v1", credentials=creds)

    archived = 0
    failed = 0
    for mid in message_ids:
        if archive_message(service, mid):
            archived += 1
        else:
            failed += 1

    print(f"Done. {archived} archived, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
