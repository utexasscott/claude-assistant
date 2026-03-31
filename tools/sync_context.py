"""
Tool: sync_context.py
Syncs a local directory with a Google Drive folder.

Usage:
  python tools/sync_context.py --direction pull   # Drive → local context/
  python tools/sync_context.py --direction push   # local context/ → Drive

  # Push a specific subdirectory to a specific Drive folder (for sharing):
  python tools/sync_context.py --direction push --source context/shared/allison --drive-folder "Co-Parenting Updates"
"""

import argparse
import io
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "auth/credentials.json"
TOKEN_FILE = "auth/token_drive.json"
DEFAULT_DRIVE_FOLDER = "Claude Agent Context"
DEFAULT_LOCAL_DIR = Path("context")
FOLDER_MIME = "application/vnd.google-apps.folder"


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


def find_or_create_folder(service, name, parent_id=None):
    """Find a Drive folder by name (and optionally parent). Creates it if not found."""
    query = f"name='{name}' and mimeType='{FOLDER_MIME}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {"name": name, "mimeType": FOLDER_MIME}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  Created Drive folder: {name}")
    return folder["id"]


def list_drive_files(service, folder_id, path_prefix=""):
    """Recursively list all files in a Drive folder. Returns list of (rel_path, file_id, is_folder)."""
    results = []
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        for f in response.get("files", []):
            rel_path = f"{path_prefix}/{f['name']}" if path_prefix else f["name"]
            if f["mimeType"] == FOLDER_MIME:
                results.append((rel_path, f["id"], True))
                results.extend(list_drive_files(service, f["id"], rel_path))
            else:
                results.append((rel_path, f["id"], False))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def pull(service, root_folder_id, local_dir):
    """Download all files from Drive → local directory."""
    print(f"Pulling from Drive -> {local_dir}/ ...")
    files = list_drive_files(service, root_folder_id)
    if not files:
        print("Drive folder is empty — nothing to download.")
        return
    local_dir.mkdir(exist_ok=True)
    downloaded = 0
    for rel_path, file_id, is_folder in files:
        local_path = local_dir / rel_path
        if is_folder:
            local_path.mkdir(parents=True, exist_ok=True)
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            request = service.files().get_media(fileId=file_id)
            with io.FileIO(str(local_path), "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            print(f"  Downloaded: {rel_path}")
            downloaded += 1
        except HttpError as e:
            print(f"  WARNING: Could not download '{rel_path}': {e}")
    print(f"\nDone. {downloaded} file(s) pulled to {local_dir}/")


def push(service, root_folder_id, local_dir):
    """Upload all files from local directory → Drive."""
    print(f"Pushing {local_dir}/ -> Drive ...")
    if not local_dir.exists():
        print(f"ERROR: local directory '{local_dir}' not found.")
        sys.exit(1)
    # Cache folder IDs by relative path to avoid redundant API calls
    folder_id_cache = {"": root_folder_id}
    uploaded = 0
    for local_file in sorted(local_dir.rglob("*")):
        if local_file.is_dir():
            continue
        rel_path = local_file.relative_to(local_dir)
        rel_parts = rel_path.parts
        # Ensure all parent folders exist in Drive
        parent_id = root_folder_id
        for i, part in enumerate(rel_parts[:-1]):
            folder_key = "/".join(rel_parts[:i + 1])
            if folder_key not in folder_id_cache:
                folder_id_cache[folder_key] = find_or_create_folder(service, part, parent_id)
            parent_id = folder_id_cache[folder_key]
        filename = rel_parts[-1]
        # Check if the file already exists in Drive
        query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        existing = service.files().list(q=query, fields="files(id)").execute().get("files", [])
        try:
            media = MediaFileUpload(str(local_file), resumable=False)
            if existing:
                service.files().update(fileId=existing[0]["id"], media_body=media).execute()
                print(f"  Updated: {rel_path}")
            else:
                metadata = {"name": filename, "parents": [parent_id]}
                service.files().create(body=metadata, media_body=media, fields="id").execute()
                print(f"  Uploaded: {rel_path}")
            uploaded += 1
        except HttpError as e:
            print(f"  WARNING: Could not upload '{rel_path}': {e}")
    print(f"\nDone. {uploaded} file(s) pushed to Drive")


def main():
    parser = argparse.ArgumentParser(description="Sync a local directory with Google Drive")
    parser.add_argument(
        "--direction",
        choices=["pull", "push"],
        required=True,
        help="pull = Drive → local, push = local → Drive",
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_LOCAL_DIR),
        help="Local directory to push or pull into (default: context/)",
    )
    parser.add_argument(
        "--drive-folder",
        default=DEFAULT_DRIVE_FOLDER,
        help='Google Drive folder name (default: "Claude Agent Context")',
    )
    args = parser.parse_args()
    local_dir = Path(args.source)
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)
    root_folder_id = find_or_create_folder(service, args.drive_folder)
    if args.direction == "pull":
        pull(service, root_folder_id, local_dir)
    else:
        push(service, root_folder_id, local_dir)


if __name__ == "__main__":
    main()
