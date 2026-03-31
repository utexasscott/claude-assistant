"""
Tool: update_sheet.py
Appends new rows to or updates existing rows in a Google Sheet.
Matches on a configurable key column (default: first column). Updates in place if match found; appends if not.
Input: JSON file (array of row objects keyed by column name)

Usage:
  python tools/update_sheet.py --sheet-id SHEET_ID --data .tmp/data.json
  python tools/update_sheet.py --sheet-id SHEET_ID --data .tmp/data.json --match-key "Name" --tab "Sheet1"
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "auth/credentials.json"
TOKEN_FILE = "auth/token_sheets.json"


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


def row_to_values(row_dict: dict, headers: list) -> list:
    """Convert a dict to an ordered list matching the sheet's header row."""
    return [str(row_dict.get(h, "")) for h in headers]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID (from URL)")
    parser.add_argument("--data", required=True, help="Path to JSON file with row updates")
    parser.add_argument("--match-key", required=True, help="Column header to use as the unique match key for upsert")
    parser.add_argument("--tab", default=None, help="Tab/sheet name (default: first tab)")
    args = parser.parse_args()
    match_key = args.match_key

    # Load input data
    _project_root = Path(__file__).parent.parent.resolve()
    if not str(Path(args.data).resolve()).startswith(str(_project_root)):
        print(f"ERROR: Path outside project directory: {args.data}")
        sys.exit(1)
    if not Path(args.data).exists():
        print(f"ERROR: Data file not found: {args.data}")
        sys.exit(1)
    with open(args.data, encoding="utf-8") as f:
        updates = json.load(f)
    if not isinstance(updates, list):
        print("ERROR: Data file must be a JSON array of row objects.")
        sys.exit(1)
    print(f"Loaded {len(updates)} row(s) from {args.data}")

    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheets_api = service.spreadsheets()

    # Resolve tab name
    tab_name = args.tab
    if not tab_name:
        try:
            meta = sheets_api.get(spreadsheetId=args.sheet_id).execute()
            tab_name = meta["sheets"][0]["properties"]["title"]
        except HttpError as e:
            print(f"ERROR: Could not fetch sheet metadata: {e}")
            sys.exit(1)

    # Read current sheet to get headers and existing rows
    try:
        result = sheets_api.values().get(
            spreadsheetId=args.sheet_id,
            range=f"'{tab_name}'",
        ).execute()
    except HttpError as e:
        print(f"ERROR: Could not read current sheet data: {e}")
        sys.exit(1)

    rows = result.get("values", [])
    if not rows:
        print("ERROR: Sheet appears to be empty (no header row found). Add headers first.")
        sys.exit(1)

    headers = rows[0]
    data_rows = rows[1:]

    if match_key not in headers:
        print(f"ERROR: Column '{match_key}' not found in sheet headers: {headers}")
        sys.exit(1)
    match_col_idx = headers.index(match_key)

    # Index existing rows by match key value (case-insensitive)
    existing_names = {
        (row[match_col_idx].strip().lower() if match_col_idx < len(row) else ""): i
        for i, row in enumerate(data_rows)
    }

    # Separate updates into in-place edits vs. appends
    updates_to_apply = []  # list of (row_index_in_data, values)
    appends = []           # list of value lists

    for update_row in updates:
        name = str(update_row.get(match_key, "")).strip().lower()
        values = row_to_values(update_row, headers)
        if name and name in existing_names:
            row_idx = existing_names[name]
            updates_to_apply.append((row_idx, values))
            print(f"  UPDATE: {update_row.get(match_key)}")
        else:
            appends.append(values)
            print(f"  APPEND: {update_row.get(match_key)}")

    # Apply in-place updates via batchUpdate
    if updates_to_apply:
        value_ranges = []
        for row_idx, values in updates_to_apply:
            # +2: +1 for 1-based index, +1 to skip header row
            sheet_row = row_idx + 2
            value_ranges.append({
                "range": f"'{tab_name}'!A{sheet_row}",
                "values": [values],
            })
        try:
            sheets_api.values().batchUpdate(
                spreadsheetId=args.sheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": value_ranges,
                },
            ).execute()
            print(f"Updated {len(updates_to_apply)} existing row(s).")
        except HttpError as e:
            print(f"ERROR: Batch update failed: {e}")
            sys.exit(1)

    # Append new rows
    if appends:
        try:
            sheets_api.values().append(
                spreadsheetId=args.sheet_id,
                range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": appends},
            ).execute()
            print(f"Appended {len(appends)} new row(s).")
        except HttpError as e:
            print(f"ERROR: Append failed: {e}")
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
