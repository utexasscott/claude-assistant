"""
Tool: block_calendar.py
Creates Google Calendar time-block events from an accepted morning coffee schedule.
Reads: .tmp/schedule_accepted.json
Output: Prints created event links.

Usage:
  python tools/block_calendar.py
  python tools/block_calendar.py --dry-run

schedule_accepted.json format:
[
  {
    "summary": "Deep work — Project X proposal",
    "start": "2026-03-01T09:00:00",
    "end": "2026-03-01T11:00:00",
    "description": "",       // optional
    "calendar_id": "primary" // optional, defaults to CALENDAR_IDS[0]
  },
  ...
]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_FILE = "auth/credentials.json"
TOKEN_FILE = "auth/token_calendar.json"
INPUT_FILE = ".tmp/schedule_accepted.json"

# Color for "morning coffee" blocks so they're visually distinct
# Google Calendar color IDs: 1=lavender,2=sage,3=grape,4=flamingo,5=banana,
#   6=tangerine,7=peacock,8=graphite,9=blueberry,10=basil,11=tomato
BLOCK_COLOR_ID = "7"  # peacock (teal)
BLOCK_TAG = "[Focus] "


def get_credentials():
    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
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
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_existing_events(service, calendar_id, date_str):
    """Fetch existing events for the day to check for conflicts."""
    time_min = f"{date_str}T00:00:00Z"
    time_max = f"{date_str}T23:59:59Z"
    try:
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
        ).execute()
        return result.get("items", [])
    except HttpError:
        return []


def events_overlap(new_start: str, new_end: str, existing_events: list) -> list:
    """Return any existing events that overlap with the proposed block."""
    overlaps = []
    try:
        ns = datetime.fromisoformat(new_start)
        ne = datetime.fromisoformat(new_end)
    except ValueError:
        return []

    for ev in existing_events:
        es_raw = ev.get("start", {}).get("dateTime")
        ee_raw = ev.get("end", {}).get("dateTime")
        if not es_raw or not ee_raw:
            continue
        try:
            es = datetime.fromisoformat(es_raw.replace("Z", "+00:00"))
            ee = datetime.fromisoformat(ee_raw.replace("Z", "+00:00"))
            # Strip timezone for naive comparison if needed
            ns_cmp = ns.replace(tzinfo=None) if ns.tzinfo is None else ns
            ne_cmp = ne.replace(tzinfo=None) if ne.tzinfo is None else ne
            es_cmp = es.replace(tzinfo=None)
            ee_cmp = ee.replace(tzinfo=None)
            if ns_cmp < ee_cmp and ne_cmp > es_cmp:
                overlaps.append(ev.get("summary", "(untitled)"))
        except Exception:
            continue
    return overlaps


def get_default_calendar_id():
    ids = os.getenv("CALENDAR_IDS", "primary")
    return ids.split(",")[0].strip()


def get_timezone():
    return os.getenv("TIMEZONE", "America/Chicago")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be created without writing to calendar")
    args = parser.parse_args()

    if not Path(INPUT_FILE).exists():
        print(f"ERROR: {INPUT_FILE} not found. Run the morning coffee workflow first.")
        sys.exit(1)

    with open(INPUT_FILE) as f:
        blocks = json.load(f)

    if not blocks:
        print("No blocks to create.")
        sys.exit(0)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Creating {len(blocks)} calendar block(s)...\n")

    if args.dry_run:
        for block in blocks:
            print(f"  WOULD CREATE: {block['summary']}")
            print(f"    {block['start']} → {block['end']}")
            if block.get("description"):
                print(f"    Note: {block['description']}")
        print("\nDry run complete. No events written.")
        return

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    default_cal = get_default_calendar_id()
    tz = get_timezone()

    # Pre-fetch existing events for overlap detection
    # Assume all blocks are on the same date
    try:
        date_str = blocks[0]["start"][:10]
        existing = get_existing_events(service, default_cal, date_str)
    except Exception:
        existing = []

    created = []
    skipped = []

    for block in blocks:
        calendar_id = block.get("calendar_id", default_cal)
        summary = block["summary"]
        start = block["start"]
        end = block["end"]
        description = block.get("description", "Created by Morning Coffee workflow.")

        # Check for conflicts
        conflicts = events_overlap(start, end, existing)
        if conflicts:
            conflict_list = ", ".join(conflicts)
            print(f"  CONFLICT: '{summary}' overlaps with: {conflict_list}")
            answer = input("    Create anyway? (y/N): ").strip().lower()
            if answer != "y":
                print(f"    Skipping '{summary}'.")
                skipped.append(summary)
                continue

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": tz},
            "end": {"dateTime": end, "timeZone": tz},
            "colorId": BLOCK_COLOR_ID,
            "reminders": {"useDefault": False, "overrides": []},
        }

        try:
            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body,
            ).execute()
            link = event.get("htmlLink", "")
            print(f"  CREATED: {summary}")
            print(f"    {start} -> {end}")
            print(f"    {link}\n")
            created.append(summary)
        except HttpError as e:
            print(f"  ERROR creating '{summary}': {e}")
            skipped.append(summary)

    print(f"\nDone. {len(created)} created, {len(skipped)} skipped.")


if __name__ == "__main__":
    main()
