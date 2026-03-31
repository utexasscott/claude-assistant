"""
Tool: get_calendar_events.py
Fetches today's Google Calendar events across all configured calendars.
Output: .tmp/calendar_today.json

Usage:
  python tools/get_calendar_events.py [--date YYYY-MM-DD]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
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
OUTPUT_FILE = ".tmp/calendar_today.json"


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
                print("Download it from Google Cloud Console > APIs & Services > Credentials.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        Path("auth").mkdir(exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def fetch_events(service, calendar_id, time_min, time_max):
    try:
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        ).execute()
        return result.get("items", [])
    except HttpError as e:
        print(f"WARNING: Could not fetch calendar '{calendar_id}': {e}")
        return []


def parse_event(event, calendar_id):
    start = event.get("start", {})
    end = event.get("end", {})
    attendees = event.get("attendees", [])
    is_all_day = "date" in start and "dateTime" not in start

    return {
        "calendar_id": calendar_id,
        "summary": event.get("summary", "(No title)"),
        "start": start.get("dateTime", start.get("date")),
        "end": end.get("dateTime", end.get("date")),
        "is_all_day": is_all_day,
        "location": event.get("location", ""),
        "description": (event.get("description", "") or "")[:300],
        "attendee_count": len(attendees),
        "has_other_attendees": len(attendees) > 1,
        "hangout_link": event.get("hangoutLink", ""),
        "status": event.get("status", "confirmed"),
        "html_link": event.get("htmlLink", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Date to fetch (YYYY-MM-DD). Defaults to today.")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    calendar_ids_raw = os.getenv("CALENDAR_IDS", "primary")
    calendar_ids = [c.strip() for c in calendar_ids_raw.split(",") if c.strip()]

    # Build time window (full day in local time, converted to UTC)
    time_min = f"{target_date}T00:00:00Z"
    time_max = f"{target_date}T23:59:59Z"

    print(f"Fetching calendar events for {target_date}...")
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    all_events = []
    for cal_id in calendar_ids:
        raw_events = fetch_events(service, cal_id, time_min, time_max)
        for e in raw_events:
            all_events.append(parse_event(e, cal_id))

    # Sort by start time
    all_events.sort(key=lambda e: e["start"] or "")

    output = {
        "date": target_date,
        "calendars_checked": calendar_ids,
        "event_count": len(all_events),
        "events": all_events,
    }

    Path(".tmp").mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Found {len(all_events)} event(s). Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
