"""
Tool: generate_plan.py
Renders the morning coffee plan as a styled HTML file, uploads it to Google Drive,
and opens the Drive URL in the browser.

Input:  .tmp/plan.json  (written by the agent during Step 4)
Output: .tmp/morning_coffee_[date].html  (local backup)
        Google Drive file (opened in browser)

Auth:   auth/token_drive.json  (scope: drive.file)
        First run opens a browser OAuth flow and saves the token.

Usage:
  python tools/generate_plan.py
"""

import html as html_mod
import io
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

INPUT_FILE = ".tmp/plan.json"
CREDENTIALS_FILE = "auth/credentials.json"
DRIVE_TOKEN_FILE = "auth/token_drive.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def load_plan() -> dict:
    if not Path(INPUT_FILE).exists():
        print(f"ERROR: {INPUT_FILE} not found. The agent must write the plan before running this tool.")
        sys.exit(1)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def block_type_style(block_type: str) -> str:
    styles = {
        "Focus":   ("var(--focus-bg)",   "var(--focus-fg)"),
        "Admin":   ("var(--admin-bg)",   "var(--admin-fg)"),
        "Routine": ("var(--routine-bg)", "var(--routine-fg)"),
        "Lunch":   ("var(--lunch-bg)",   "var(--lunch-fg)"),
    }
    bg, fg = styles.get(block_type, ("var(--routine-bg)", "var(--routine-fg)"))
    return f'background:{bg};color:{fg}'


def render_html(plan: dict) -> str:
    date_str = plan.get("date", "")
    urgent = plan.get("urgent", [])
    glance = plan.get("day_at_a_glance", "")
    committed = plan.get("committed", [])
    proposed = plan.get("proposed_blocks", [])
    watch = plan.get("watch_list", [])
    deferred = plan.get("deferred", [])
    archiving = plan.get("archiving", [])

    def e(s):
        return html_mod.escape(str(s))

    def li(items):
        return "".join(f"<li>{e(i)}</li>" for i in items)

    def committed_rows():
        rows = ""
        for ev in committed:
            rows += f"""
            <div class="time-row committed-row">
              <span class="time">{e(ev.get('time',''))}</span>
              <span class="summary">{e(ev.get('summary',''))}</span>
            </div>"""
        return rows or "<p class='empty'>No calendar events today.</p>"

    def proposed_rows():
        rows = ""
        for b in proposed:
            btype = b.get("type", "Routine")
            rows += f"""
            <div class="time-row proposed-row">
              <span class="time">{e(b.get('time',''))}</span>
              <span class="block-tag" style="{block_type_style(btype)}">{e(btype)}</span>
              <span class="summary">{e(b.get('summary',''))}</span>
            </div>"""
        return rows

    def archive_rows():
        rows = ""
        for a in archiving:
            acct = a.get("account", "")
            badge = f'<span class="acct-badge acct-{e(acct)}">{e(acct)}</span>'
            rows += f"""
            <div class="archive-row">
              {badge}
              <span class="archive-sender">{e(a.get('sender',''))}</span>
              <span class="archive-subject">— {e(a.get('subject',''))}</span>
            </div>"""
        return rows

    urgent_section = ""
    if urgent:
        urgent_section = f"""
        <section class="urgent-section">
          <h2>🚨 URGENT — ACTION NEEDED TODAY</h2>
          <ul>{''.join(f'<li>{html_mod.escape(str(u))}</li>' for u in urgent)}</ul>
        </section>"""
    else:
        urgent_section = """
        <section class="urgent-section quiet">
          <h2>✅ URGENT — ACTION NEEDED TODAY</h2>
          <p>Nothing urgent. Inbox is quiet.</p>
        </section>"""

    archive_section = ""
    if archiving:
        archive_section = f"""
        <section class="archive-section">
          <h2>🗂 ARCHIVING ({len(archiving)} emails)</h2>
          <p class="section-note">Identified as noise — archived automatically upon plan acceptance.</p>
          <div class="archive-list">{archive_rows()}</div>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morning Coffee — {date_str}</title>
  <style>
    :root {{
      --bg:         #f5f2ee;
      --surface:    #ffffff;
      --border:     #e8e3dc;
      --text:       #1c1917;
      --muted:      #78716c;
      --accent:     #92400e;

      --urgent-bg:  #fef2f2;
      --urgent-border: #fca5a5;
      --urgent-heading: #991b1b;

      --focus-bg:   #1e40af;  --focus-fg:   #ffffff;
      --admin-bg:   #065f46;  --admin-fg:   #ffffff;
      --routine-bg: #4b5563;  --routine-fg: #ffffff;
      --lunch-bg:   #92400e;  --lunch-fg:   #ffffff;

      --watch-bg:   #fffbeb;
      --watch-border: #fcd34d;

      --archive-bg: #f0fdf4;
      --archive-border: #86efac;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 40px 24px 80px;
      font-size: 15px;
      line-height: 1.6;
    }}

    .page {{ max-width: 780px; margin: 0 auto; }}

    header {{
      border-bottom: 2px solid var(--accent);
      padding-bottom: 16px;
      margin-bottom: 32px;
    }}

    header h1 {{
      font-size: 28px;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.5px;
    }}

    header .date {{
      font-size: 14px;
      color: var(--muted);
      margin-top: 4px;
      font-weight: 500;
    }}

    section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 20px;
    }}

    h2 {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 14px;
    }}

    /* URGENT */
    .urgent-section {{
      background: var(--urgent-bg);
      border-color: var(--urgent-border);
    }}
    .urgent-section h2 {{ color: var(--urgent-heading); }}
    .urgent-section ul {{ padding-left: 20px; }}
    .urgent-section li {{
      margin-bottom: 8px;
      color: #7f1d1d;
      font-weight: 500;
    }}
    .urgent-section.quiet {{ background: #f0fdf4; border-color: #86efac; }}
    .urgent-section.quiet h2 {{ color: #166534; }}
    .urgent-section.quiet p {{ color: #166534; font-weight: 500; }}

    /* GLANCE */
    .glance-section p {{
      color: var(--text);
      font-size: 15px;
      line-height: 1.7;
    }}

    /* TIME BLOCKS */
    .time-row {{
      display: flex;
      align-items: baseline;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
    }}
    .time-row:last-child {{ border-bottom: none; }}

    .time {{
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      white-space: nowrap;
      min-width: 110px;
      font-variant-numeric: tabular-nums;
    }}

    .committed-row .summary {{
      font-weight: 600;
      color: var(--text);
    }}

    .block-tag {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 2px 8px;
      border-radius: 4px;
      white-space: nowrap;
    }}

    .proposed-row .summary {{ color: var(--text); }}

    /* WATCH LIST */
    .watch-section {{
      background: var(--watch-bg);
      border-color: var(--watch-border);
    }}
    .watch-section h2 {{ color: #92400e; }}
    .watch-section ul {{ padding-left: 20px; }}
    .watch-section li {{ margin-bottom: 6px; color: #78350f; }}

    /* DEFERRED */
    .deferred-section ul {{ padding-left: 20px; }}
    .deferred-section li {{ margin-bottom: 4px; color: var(--muted); }}

    /* ARCHIVE */
    .archive-section {{
      background: var(--archive-bg);
      border-color: var(--archive-border);
    }}
    .archive-section h2 {{ color: #166534; }}
    .section-note {{
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 12px;
    }}
    .archive-row {{
      display: flex;
      align-items: baseline;
      gap: 8px;
      padding: 5px 0;
      border-bottom: 1px solid #bbf7d0;
      font-size: 13px;
    }}
    .archive-row:last-child {{ border-bottom: none; }}
    .acct-badge {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 1px 6px;
      border-radius: 3px;
      white-space: nowrap;
    }}
    .acct-personal {{ background: #dbeafe; color: #1e40af; }}
    .acct-work     {{ background: #ede9fe; color: #5b21b6; }}
    .archive-sender {{ font-weight: 600; color: #166534; }}
    .archive-subject {{ color: var(--muted); }}

    .empty {{ color: var(--muted); font-style: italic; }}

    @media print {{
      body {{ background: white; padding: 20px; }}
      section {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>☕ Morning Coffee</h1>
      <div class="date">{date_str}</div>
    </header>

    {urgent_section}

    <section class="glance-section">
      <h2>Your Day at a Glance</h2>
      <p>{glance}</p>
    </section>

    <section class="committed-section">
      <h2>Committed</h2>
      {committed_rows()}
    </section>

    <section class="proposed-section">
      <h2>Proposed Blocks</h2>
      {proposed_rows()}
    </section>

    <section class="watch-section">
      <h2>👀 Watch List</h2>
      <ul>{li(watch)}</ul>
    </section>

    <section class="deferred-section">
      <h2>Deferred</h2>
      <ul>{li(deferred)}</ul>
    </section>

    {archive_section}
  </div>
</body>
</html>"""


def get_drive_credentials():
    creds = None
    if Path(DRIVE_TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(DRIVE_TOKEN_FILE, DRIVE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                print("Download it from Google Cloud Console > APIs & Services > Credentials.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, DRIVE_SCOPES)
            creds = flow.run_local_server(port=0)
        Path("auth").mkdir(exist_ok=True)
        with open(DRIVE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


DRIVE_FOLDER_NAME = "Claude Morning Coffee"


def get_or_create_folder(service, folder_name: str) -> str:
    """Return the Drive folder ID for folder_name, creating it if it doesn't exist."""
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)",
    ).execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]
    folder = service.files().create(
        body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
        fields="id",
    ).execute()
    print(f"Created Drive folder: {folder_name}")
    print()
    print("NOTE: To view HTML files directly in Google Drive (without downloading),")
    print("install the HTML Editor for Google Drive by CloudHQ:")
    print("https://workspace.google.com/marketplace/app/html_editor_for_google_drive_by_cloudhq/533233485435")
    print()
    return folder["id"]


def upload_to_drive(html_content: str, filename: str) -> str:
    """Upload HTML to the 'Claude Morning Coffee' Drive folder.
    Updates existing file if found; creates new otherwise.
    Returns the webViewLink."""
    creds = get_drive_credentials()
    service = build("drive", "v3", credentials=creds)

    folder_id = get_or_create_folder(service, DRIVE_FOLDER_NAME)

    media = MediaIoBaseUpload(
        io.BytesIO(html_content.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )

    try:
        # Look for a file with this name inside the folder
        results = service.files().list(
            q=f"name='{filename}' and '{folder_id}' in parents and trashed=false",
            fields="files(id,webViewLink)",
        ).execute()
        existing = results.get("files", [])

        if existing:
            file_id = existing[0]["id"]
            file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields="id,webViewLink",
            ).execute()
            print(f"Updated existing Drive file.")
        else:
            metadata = {"name": filename, "mimeType": "text/html", "parents": [folder_id]}
            file = service.files().create(
                body=metadata,
                media_body=media,
                fields="id,webViewLink",
            ).execute()
            print(f"Uploaded new file to Drive folder '{DRIVE_FOLDER_NAME}'.")

        return file.get("webViewLink")

    except HttpError as e:
        print(f"ERROR: Drive upload failed: {e}")
        sys.exit(1)


def main():
    plan = load_plan()
    date_str = plan.get("date", datetime.now().strftime("%Y-%m-%d"))
    safe_date = date_str.replace(",", "").replace(" ", "_")

    Path(".tmp").mkdir(exist_ok=True)
    output_path = Path(f".tmp/morning_coffee_{safe_date}.html")
    drive_filename = f"Morning Coffee - {safe_date}.html"

    html = render_html(plan)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Plan saved locally to {output_path.resolve()}")

    drive_url = upload_to_drive(html, drive_filename)
    print(f"Drive URL: {drive_url}")
    webbrowser.open(drive_url)
    print("Opened in browser.")


if __name__ == "__main__":
    main()
