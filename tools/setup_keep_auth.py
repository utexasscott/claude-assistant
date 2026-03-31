"""
Tool: setup_keep_auth.py
One-time interactive setup to authenticate with Google Keep via gkeepapi.

Run this once to get a master token, then store it in .env as KEEP_MASTER_TOKEN.
After that, update_keep_list.py will use the stored token automatically.

Prerequisites:
  pip install gkeepapi gpsoauth

Steps:
  1. python tools/setup_keep_auth.py
  2. Enter your Google email and an app-specific password when prompted
     (Generate an app password at: https://myaccount.google.com/apppasswords)
  3. The script will print your KEEP_MASTER_TOKEN — copy it into your .env file

Why an app password?
  Google requires app passwords (not your main password) for third-party access.
  You need 2-Step Verification enabled to generate one.
  Label it anything, e.g. "gkeepapi".
"""

import os
import sys
import getpass

try:
    import gkeepapi
except ImportError:
    print("ERROR: gkeepapi not installed. Run: pip install gkeepapi")
    sys.exit(1)

try:
    import gpsoauth
except ImportError:
    print("ERROR: gpsoauth not installed. Run: pip install gpsoauth")
    sys.exit(1)


def main():
    print("=" * 60)
    print("Google Keep Authentication Setup")
    print("=" * 60)
    print()
    print("You'll need an app-specific password (NOT your main Google password).")
    print("Generate one at: https://myaccount.google.com/apppasswords")
    print("  1. Choose 'Select app' → 'Other (custom name)' → type 'gkeepapi'")
    print("  2. Click Generate and copy the 16-character password")
    print()

    email = input("Google email: ").strip()
    if not email:
        print("ERROR: Email cannot be empty.")
        sys.exit(1)

    password = getpass.getpass("App password (16 chars, spaces optional): ").replace(" ", "")
    if not password:
        print("ERROR: Password cannot be empty.")
        sys.exit(1)

    print()
    print("Authenticating with Google...")

    try:
        # Exchange credentials for a master token
        auth_result = gpsoauth.perform_master_login(email, password, "0000000000000000")
        master_token = auth_result.get("Token")

        if not master_token:
            error = auth_result.get("Error", "Unknown error")
            print(f"ERROR: Authentication failed — {error}")
            print()
            print("Common causes:")
            print("  - You used your main Google password instead of an app password")
            print("  - The app password is incorrect or was revoked")
            print("  - 2-Step Verification is not enabled on your account")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Verify by connecting to Keep
    print("Verifying connection to Google Keep...")
    try:
        keep = gkeepapi.Keep()
        keep.authenticate(email, master_token)
        keep.sync()
        note_count = len(list(keep.all()))
        print(f"✓ Connected successfully. Found {note_count} note(s) in your Keep account.")
    except Exception as e:
        print(f"ERROR: Could not connect to Keep: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("SUCCESS — Add these lines to your .env file:")
    print("=" * 60)
    print(f"KEEP_EMAIL={email}")
    print(f"KEEP_MASTER_TOKEN={master_token}")
    print()
    print("Also verify these defaults match your Keep setup (add to .env if different):")
    print("  KEEP_SHOPPING_NOTE_TITLE=Shopping")
    print("  KEEP_GROCERY_STORE_SECTION=<your store section header>")


if __name__ == "__main__":
    main()
