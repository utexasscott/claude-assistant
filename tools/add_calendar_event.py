"""
Tool: add_calendar_event.py
Creates a single Google Calendar event from command-line arguments.
Used by workflows to schedule things like grocery store trips.

Usage:
  python tools/add_calendar_event.py \
    --title "grocery run" \
    --date 2026-03-02 \
    --time 10:00 \
    --duration 60 \
    --description "Meal plan grocery run" \
    --color 5

  --dry-run flag prints without creating.

Color IDs: 1=lavender, 2=sage, 3=grape, 4=flamingo, 5=banana,
           6=tangerine, 7=peacock, 8=graphite, 9=blueberry, 10=basil, 11=tomato
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

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


def main():
    parser = argparse.ArgumentParser(description="Add a single event to Google Calendar")
    parser.add_argument("--title", required=True, help="Event title/summary")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--time", required=True, help="Start time in HH:MM (24h) format")
    parser.add_argument("--duration", type=int, default=60, help="Duration in minutes (default: 60)")
    parser.add_argument("--description", default="", help="Optional event description")
    parser.add_argument("--color", default="5", help="Google Calendar color ID (default: 5=banana/yellow)")
    parser.add_argument("--calendar-id", default=None, help="Calendar ID (defaults to CALENDAR_IDS[0])")
    parser.add_argument("--dry-run", action="store_true", help="Print without creating")
    args = parser.parse_args()

    tz = os.getenv("TIMEZONE", "America/Chicago")
    calendar_id = args.calendar_id or os.getenv("CALENDAR_IDS", "primary").split(",")[0].strip()

    try:
        start_dt = datetime.strptime(f"{args.date} {args.time}", "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"ERROR: Invalid date/time format. Use YYYY-MM-DD and HH:MM.")
        sys.exit(1)

    end_dt = start_dt + timedelta(minutes=args.duration)
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Event details:")
    print(f"  Title:    {args.title}")
    print(f"  Date:     {args.date}")
    print(f"  Time:     {args.time} – {end_dt.strftime('%H:%M')} ({args.duration} min)")
    print(f"  Calendar: {calendar_id}")
    if args.description:
        print(f"  Note:     {args.description}")

    if args.dry_run:
        print("\nDry run complete. No event created.")
        return

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    event_body = {
        "summary": args.title,
        "description": args.description or f"Added by WAT workflow.",
        "start": {"dateTime": start_str, "timeZone": tz},
        "end": {"dateTime": end_str, "timeZone": tz},
        "colorId": str(args.color),
        "reminders": {"useDefault": True},
    }

    try:
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        link = event.get("htmlLink", "")
        print(f"\n✓ Event created: {args.title}")
        print(f"  {link}")
    except HttpError as e:
        print(f"\nERROR: Failed to create event: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
