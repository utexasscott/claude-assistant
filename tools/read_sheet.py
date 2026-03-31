"""
Tool: read_sheet.py
Reads a Google Sheet tab and outputs it as a JSON array of row objects.
Output: .tmp/mh_programs.json (default)

Usage:
  python tools/read_sheet.py --sheet-id SHEET_ID
  python tools/read_sheet.py --sheet-id SHEET_ID --tab "Sheet1"
  python tools/read_sheet.py --sheet-id SHEET_ID --output .tmp/custom.json
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
DEFAULT_OUTPUT = ".tmp/mh_programs.json"


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID (from URL)")
    parser.add_argument("--tab", default=None, help="Tab/sheet name (default: first tab)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON file path")
    args = parser.parse_args()

    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheets_api = service.spreadsheets()

    # Resolve tab name
    tab_name = args.tab
    if not tab_name:
        try:
            meta = sheets_api.get(spreadsheetId=args.sheet_id).execute()
            tab_name = meta["sheets"][0]["properties"]["title"]
            print(f"Using first tab: '{tab_name}'")
        except HttpError as e:
            print(f"ERROR: Could not fetch sheet metadata: {e}")
            sys.exit(1)

    # Read all values from the tab
    try:
        result = sheets_api.values().get(
            spreadsheetId=args.sheet_id,
            range=f"'{tab_name}'",
        ).execute()
    except HttpError as e:
        print(f"ERROR: Could not read sheet data: {e}")
        sys.exit(1)

    rows = result.get("values", [])
    if not rows:
        print("Sheet is empty.")
        output_data = []
    else:
        headers = rows[0]
        data_rows = rows[1:]
        output_data = []
        for row in data_rows:
            # Pad short rows to match header count
            padded = row + [""] * (len(headers) - len(row))
            output_data.append(dict(zip(headers, padded)))

    Path(".tmp").mkdir(exist_ok=True)
    _project_root = Path(__file__).parent.parent.resolve()
    if not str(Path(args.output).resolve()).startswith(str(_project_root)):
        print(f"ERROR: Path outside project directory: {args.output}")
        sys.exit(1)
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Read {len(output_data)} row(s) from '{tab_name}'. Saved to {args.output}")


if __name__ == "__main__":
    main()
