"""
Tool: update_keep_list.py
Clears the configured grocery store section of a Google Keep shopping list and inserts a new list of items.

Reads:  .tmp/heb_list.json  — a JSON array of strings (one item per entry)
Output: Updates the Keep note in-place

Configuration (in .env):
  KEEP_EMAIL                  — your Google email
  KEEP_MASTER_TOKEN           — obtained via tools/setup_keep_auth.py
  KEEP_SHOPPING_NOTE_TITLE    — title of the Keep note (default: "Shopping")
  KEEP_GROCERY_STORE_SECTION  — section header name to find/replace

Expected Keep note structure:
  The shopping note should be a List-type note with section headers as unchecked
  list items. Example structure:

    [ ] [your store]     ← section header (matched by KEEP_GROCERY_STORE_SECTION)
    [ ] Chicken breast   ← items in this section
    [ ] Onions
    [ ] Pasta
    [ ] Costco           ← next section header (marks end of grocery store section)
    [ ] Paper towels

  Items are considered part of the grocery store section until another "section header"
  is encountered. A section header is detected as any unchecked item whose text
  matches one of the known section names stored in KEEP_SECTION_HEADERS, or whose
  text is short (≤20 chars) and contains no lowercase letters.

Usage:
  python tools/update_keep_list.py
  python tools/update_keep_list.py --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    import gkeepapi
except ImportError:
    print("ERROR: gkeepapi not installed. Run: pip install gkeepapi")
    sys.exit(1)

load_dotenv()

KEEP_EMAIL = os.getenv("KEEP_EMAIL")
KEEP_MASTER_TOKEN = os.getenv("KEEP_MASTER_TOKEN")
SHOPPING_NOTE_TITLE = os.getenv("KEEP_SHOPPING_NOTE_TITLE", "Shopping")
STORE_SECTION = os.getenv("KEEP_GROCERY_STORE_SECTION", "")
INPUT_FILE = Path(".tmp/heb_list.json")


def is_section_header(text: str, store_section: str) -> bool:
    """
    Detect if a list item is a section header (store name / category divider).
    Heuristic: short text (≤25 chars) with no lowercase letters, or matches the configured store section name.
    """
    text = text.strip()
    if not text:
        return False
    if store_section and text.upper() == store_section.upper():
        return True
    if len(text) <= 25 and text == text.upper() and any(c.isalpha() for c in text):
        return True
    return False


def rebuild_list(note, new_items: list, store_section: str, dry_run: bool = False):
    """
    Rebuild the Keep list note by replacing the grocery store section items with new_items.
    Preserves all other sections and their items.
    """
    # Snapshot current list structure
    current_items = list(note.items)

    # Parse into sections
    sections = []     # list of {"header": str|None, "items": [{"text": str, "checked": bool}]}
    current_section = None

    for item in current_items:
        text = item.text.strip()
        checked = item.checked

        if is_section_header(text, store_section):
            current_section = {"header": text, "header_checked": checked, "items": []}
            sections.append(current_section)
        else:
            if current_section is None:
                # Items before any section header go into a virtual "no header" section
                current_section = {"header": None, "header_checked": False, "items": []}
                sections.append(current_section)
            current_section["items"].append({"text": text, "checked": checked})

    # Find and replace the grocery store section
    store_found = False
    for section in sections:
        if section["header"] and store_section and section["header"].upper() == store_section.upper():
            section["items"] = [{"text": item, "checked": False} for item in new_items]
            store_found = True
            break

    if not store_found:
        # Append a new grocery store section at the end
        print(f"  NOTE: '{store_section}' section not found — it will be added at the bottom.")
        sections.append({
            "header": store_section,
            "header_checked": False,
            "items": [{"text": item, "checked": False} for item in new_items],
        })

    if dry_run:
        print("\n[DRY RUN] Rebuilt list would look like:\n")
        for section in sections:
            if section["header"]:
                check = "x" if section["header_checked"] else " "
                print(f"  [{check}] {section['header']}")
            for it in section["items"]:
                check = "x" if it["checked"] else " "
                print(f"      [{check}] {it['text']}")
        print()
        return

    # Delete all existing items
    for item in current_items:
        item.delete()

    # Re-add in order
    for section in sections:
        if section["header"]:
            note.add(section["header"], section["header_checked"],
                     gkeepapi.node.NewListItemPlacementValue.Bottom)
        for it in section["items"]:
            note.add(it["text"], it["checked"],
                     gkeepapi.node.NewListItemPlacementValue.Bottom)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing to Keep")
    args = parser.parse_args()

    # Validate config
    if not KEEP_EMAIL or not KEEP_MASTER_TOKEN:
        print("ERROR: KEEP_EMAIL and KEEP_MASTER_TOKEN must be set in .env")
        print("  Run: python tools/setup_keep_auth.py")
        sys.exit(1)

    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found.")
        print("  This file should be created by the agent during the meal planning workflow.")
        sys.exit(1)

    with open(INPUT_FILE, encoding="utf-8") as f:
        new_items = json.load(f)

    if not isinstance(new_items, list):
        print("ERROR: heb_list.json must be a JSON array of strings.")
        sys.exit(1)

    print(f"Connecting to Google Keep as {KEEP_EMAIL}...")
    try:
        keep = gkeepapi.Keep()
        keep.authenticate(KEEP_EMAIL, KEEP_MASTER_TOKEN)
        keep.sync()
    except Exception as e:
        print(f"ERROR: Could not connect to Keep: {e}")
        print("  Your token may have expired. Re-run: python tools/setup_keep_auth.py")
        sys.exit(1)

    # Find the shopping note
    shopping_note = None
    for note in keep.all():
        if note.title.strip().lower() == SHOPPING_NOTE_TITLE.lower():
            shopping_note = note
            break

    if not shopping_note:
        print(f"ERROR: Could not find a Keep note titled '{SHOPPING_NOTE_TITLE}'.")
        print(f"  Check KEEP_SHOPPING_NOTE_TITLE in your .env (current: '{SHOPPING_NOTE_TITLE}')")
        sys.exit(1)

    if not isinstance(shopping_note, gkeepapi.node.List):
        print(f"ERROR: The '{SHOPPING_NOTE_TITLE}' note is not a list-type note.")
        print("  In Google Keep, make sure it's a checklist (not a plain text note).")
        sys.exit(1)

    print(f"✓ Found note: '{shopping_note.title}'")
    print(f"  Replacing '{STORE_SECTION}' section with {len(new_items)} new item(s)...")
    if args.dry_run:
        print("  (DRY RUN — no changes will be saved)")

    rebuild_list(shopping_note, new_items, STORE_SECTION, dry_run=args.dry_run)

    if not args.dry_run:
        keep.sync()
        print(f"\n✓ Keep updated. '{STORE_SECTION}' section now has {len(new_items)} item(s).")


if __name__ == "__main__":
    main()
