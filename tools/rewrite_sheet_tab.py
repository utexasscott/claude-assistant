"""
Tool: rewrite_sheet_tab.py
Replaces all data rows in a Google Sheet tab with rows from a JSON file.
The header row is preserved. All existing data rows are cleared and rewritten.

Usage:
  python tools/rewrite_sheet_tab.py --sheet-id SHEET_ID --data .tmp/data.json
  python tools/rewrite_sheet_tab.py --sheet-id SHEET_ID --data .tmp/data.json --tab "Sheet1"
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
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        Path("auth").mkdir(exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def row_to_values(row_dict: dict, headers: list) -> list:
    return [str(row_dict.get(h, "")) for h in headers]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--data", required=True, help="JSON file: array of row dicts keyed by column name")
    parser.add_argument("--tab", default=None, help="Tab name (default: first tab)")
    args = parser.parse_args()

    _project_root = Path(__file__).parent.parent.resolve()
    if not str(Path(args.data).resolve()).startswith(str(_project_root)):
        print(f"ERROR: Path outside project directory: {args.data}")
        sys.exit(1)
    if not Path(args.data).exists():
        print(f"ERROR: {args.data} not found")
        sys.exit(1)
    with open(args.data, encoding="utf-8") as f:
        new_rows = json.load(f)
    if not isinstance(new_rows, list):
        print("ERROR: Data file must be a JSON array.")
        sys.exit(1)
    print(f"Loaded {len(new_rows)} row(s) from {args.data}")

    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheets_api = service.spreadsheets()

    # Resolve tab name
    tab_name = args.tab
    if not tab_name:
        meta = sheets_api.get(spreadsheetId=args.sheet_id).execute()
        tab_name = meta["sheets"][0]["properties"]["title"]
    print(f"Writing to tab: '{tab_name}'")

    # Read current header row
    result = sheets_api.values().get(
        spreadsheetId=args.sheet_id,
        range=f"'{tab_name}'!1:1",
    ).execute()
    header_rows = result.get("values", [])
    if not header_rows:
        print("ERROR: No header row found.")
        sys.exit(1)
    headers = header_rows[0]
    print(f"Headers ({len(headers)}): {headers[:5]}...")

    # Get current data row count to know how many rows to clear
    current_result = sheets_api.values().get(
        spreadsheetId=args.sheet_id,
        range=f"'{tab_name}'",
    ).execute()
    current_rows = current_result.get("values", [])
    current_data_count = len(current_rows) - 1  # subtract header
    print(f"Current data rows: {current_data_count}")

    # Clear all data rows (rows 2 onward)
    if current_data_count > 0:
        clear_range = f"'{tab_name}'!A2:ZZ{current_data_count + 1}"
        sheets_api.values().clear(
            spreadsheetId=args.sheet_id,
            range=clear_range,
        ).execute()
        print(f"Cleared {current_data_count} existing data row(s).")

    # Write new rows
    values = [row_to_values(row, headers) for row in new_rows]
    sheets_api.values().update(
        spreadsheetId=args.sheet_id,
        range=f"'{tab_name}'!A2",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()
    print(f"Wrote {len(values)} row(s).")
    print("Done.")


if __name__ == "__main__":
    main()
