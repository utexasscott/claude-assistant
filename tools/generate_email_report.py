"""
Tool: generate_email_report.py
Renders the email triage report as a styled HTML file, uploads it to Google Drive
("Claude Email Check" folder), and opens the Drive URL in the browser.

Input:  .tmp/email_report.json  (written by the agent during Step 2)
Output: .tmp/email_report_[date].html  (local backup)
        Google Drive file (opened in browser)

Auth:   auth/token_drive.json  (scope: drive)
        First run opens a browser OAuth flow and saves the token.

Usage:
  python tools/generate_email_report.py
"""

import html as html_mod
import io
import json
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

INPUT_FILE = ".tmp/email_report.json"
CREDENTIALS_FILE = "auth/credentials.json"
DRIVE_TOKEN_FILE = "auth/token_drive.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
DRIVE_FOLDER_NAME = "Claude Email Check"


def load_report() -> dict:
    if not Path(INPUT_FILE).exists():
        print(f"ERROR: {INPUT_FILE} not found. The agent must write the report before running this tool.")
        sys.exit(1)
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


ACTION_STYLES = {
    "Reply today": ("var(--urgent-bg)", "var(--urgent-fg)"),
    "Watch":       ("var(--watch-bg)",  "var(--watch-fg)"),
    "Read":        ("var(--read-bg)",   "var(--read-fg)"),
    "Archive":     ("var(--archive-bg-tag)", "var(--archive-fg-tag)"),
}


def action_badge(action: str) -> str:
    bg, fg = ACTION_STYLES.get(action, ("var(--read-bg)", "var(--read-fg)"))
    return f'<span class="action-badge" style="background:{bg};color:{fg}">{html_mod.escape(action)}</span>'


def render_html(report: dict) -> str:
    now = datetime.now()
    date_str = report.get("date", f"{now.strftime('%A, %B')} {now.day}, {now.year}")
    personal_total = report.get("personal_total", 0)
    work_total = report.get("work_total", 0)
    urgent = report.get("urgent", [])
    personal_emails = report.get("personal_emails", [])
    work_emails = report.get("work_emails", [])
    watch_list = report.get("watch_list", [])
    archiving = report.get("archiving", [])

    def esc(s):
        return html_mod.escape(str(s))

    def li(items):
        return "".join(f"<li>{esc(i)}</li>" for i in items)

    def email_rows(emails):
        if not emails:
            return "<p class='empty'>No emails.</p>"
        rows = ""
        for em in emails:
            badge = action_badge(em.get("action", "Read"))
            rows += f"""
            <div class="email-row">
              <span class="email-sender">{esc(em.get('sender', ''))}</span>
              <span class="email-subject">{esc(em.get('subject', ''))}</span>
              {badge}
            </div>"""
        return rows

    def archive_rows():
        if not archiving:
            return ""
        rows = ""
        for a in archiving:
            acct = a.get("account", "")
            badge = f'<span class="acct-badge acct-{esc(acct)}">{esc(acct)}</span>'
            rows += f"""
            <div class="archive-row">
              {badge}
              <span class="archive-sender">{esc(a.get('sender', ''))}</span>
              <span class="archive-subject">— {esc(a.get('subject', ''))}</span>
            </div>"""
        return rows

    if urgent:
        urgent_section = f"""
        <section class="urgent-section">
          <h2>🚨 URGENT — ACTION NEEDED TODAY</h2>
          <ul>{li(urgent)}</ul>
        </section>"""
    else:
        urgent_section = """
        <section class="urgent-section quiet">
          <h2>✅ URGENT — ACTION NEEDED TODAY</h2>
          <p>Nothing urgent. Inboxes are quiet.</p>
        </section>"""

    watch_section = ""
    if watch_list:
        watch_section = f"""
        <section class="watch-section">
          <h2>👀 Watch List</h2>
          <ul>{li(watch_list)}</ul>
        </section>"""

    archive_section = ""
    if archiving:
        archive_section = f"""
        <section class="archive-section">
          <h2>🗂 ARCHIVING ({len(archiving)} emails)</h2>
          <p class="section-note">Identified as noise — archived automatically upon acceptance.</p>
          <div class="archive-list">{archive_rows()}</div>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email Check — {date_str}</title>
  <style>
    :root {{
      --bg:         #f0f4f8;
      --surface:    #ffffff;
      --border:     #e2e8f0;
      --text:       #1a202c;
      --muted:      #718096;
      --accent:     #2b6cb0;

      --urgent-bg:  #fff5f5;
      --urgent-fg:  #c53030;
      --urgent-border: #feb2b2;
      --urgent-heading: #9b2c2c;

      --watch-bg:   #1a56db;
      --watch-fg:   #ffffff;
      --watch-section-bg: #fffbeb;
      --watch-border: #fcd34d;

      --read-bg:    #e2e8f0;
      --read-fg:    #4a5568;

      --archive-bg-tag: #c6f6d5;
      --archive-fg-tag: #276749;

      --archive-bg: #f0fff4;
      --archive-border: #9ae6b4;
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

    header .meta {{
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
      color: #742a2a;
      font-weight: 500;
    }}
    .urgent-section.quiet {{ background: #f0fff4; border-color: #9ae6b4; }}
    .urgent-section.quiet h2 {{ color: #276749; }}
    .urgent-section.quiet p {{ color: #276749; font-weight: 500; }}

    /* INBOX SECTIONS */
    .inbox-section h2 {{ color: var(--muted); }}
    .inbox-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 14px;
    }}
    .inbox-count {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 500;
    }}

    /* EMAIL ROWS */
    .email-row {{
      display: flex;
      align-items: baseline;
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
    }}
    .email-row:last-child {{ border-bottom: none; }}

    .email-sender {{
      font-weight: 600;
      color: var(--text);
      min-width: 140px;
      font-size: 13px;
    }}

    .email-subject {{
      flex: 1;
      color: var(--muted);
      font-size: 13px;
    }}

    .action-badge {{
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 2px 8px;
      border-radius: 4px;
      white-space: nowrap;
    }}

    /* WATCH */
    .watch-section {{
      background: var(--watch-section-bg);
      border-color: var(--watch-border);
    }}
    .watch-section h2 {{ color: #92400e; }}
    .watch-section ul {{ padding-left: 20px; }}
    .watch-section li {{ margin-bottom: 6px; color: #78350f; }}

    /* ARCHIVE */
    .archive-section {{
      background: var(--archive-bg);
      border-color: var(--archive-border);
    }}
    .archive-section h2 {{ color: #276749; }}
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
      border-bottom: 1px solid #9ae6b4;
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
    .archive-sender {{ font-weight: 600; color: #276749; }}
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
      <h1>📬 Email Check</h1>
      <div class="meta">{date_str} &nbsp;·&nbsp; {personal_total} personal &nbsp;·&nbsp; {work_total} work</div>
    </header>

    {urgent_section}

    <section class="inbox-section">
      <div class="inbox-header">
        <h2>Personal Inbox</h2>
        <span class="inbox-count">{personal_total} emails</span>
      </div>
      {email_rows(personal_emails)}
    </section>

    <section class="inbox-section">
      <div class="inbox-header">
        <h2>Work Inbox</h2>
        <span class="inbox-count">{work_total} emails</span>
      </div>
      {email_rows(work_emails)}
    </section>

    {watch_section}

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


def get_or_create_folder(service, folder_name: str) -> str:
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
    """Upload HTML to the Drive folder. Updates existing file if found; creates new otherwise."""
    creds = get_drive_credentials()
    service = build("drive", "v3", credentials=creds)

    folder_id = get_or_create_folder(service, DRIVE_FOLDER_NAME)

    media = MediaIoBaseUpload(
        io.BytesIO(html_content.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )

    try:
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
            print("Updated existing Drive file.")
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
    report = load_report()
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    safe_date = date_str.replace(",", "").replace(" ", "_")

    Path(".tmp").mkdir(exist_ok=True)
    output_path = Path(f".tmp/email_report_{safe_date}.html")
    drive_filename = f"Email Check - {safe_date}.html"

    html = render_html(report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved locally to {output_path.resolve()}")

    drive_url = upload_to_drive(html, drive_filename)
    print(f"Drive URL: {drive_url}")
    webbrowser.open(drive_url)
    print("Opened in browser.")


if __name__ == "__main__":
    main()
