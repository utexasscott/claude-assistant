"""
Tool: prep_journal.py
Keeps the active journal window tidy.

Actions:
  1. Move journal/raw/YYYY-MM-DD/ directories older than 10 days → journal/archive/raw/
  2. Move journal/YYYY-MM-DD.md files older than 10 days       → journal/archive/
  3. Create missing journal/raw/YYYY-MM-DD/ dirs for the active window (today − 10 d … today)

Usage:
  python tools/prep_journal.py
  python tools/prep_journal.py --dry-run   # preview without making changes
"""

import argparse
import shutil
from datetime import date, timedelta
from pathlib import Path

# Anchored to project root (two levels up from this file)
ROOT = Path(__file__).parent.parent
JOURNAL_DIR = ROOT / "context" / "journal"
ARCHIVE_DIR = JOURNAL_DIR / "archive"
RAW_DIR = JOURNAL_DIR / "raw"
ARCHIVE_RAW_DIR = ARCHIVE_DIR / "raw"

WINDOW_DAYS = 10  # keep the past N days active


def parse_date(name: str) -> date | None:
    """Return a date if name is YYYY-MM-DD, else None."""
    try:
        return date.fromisoformat(name)
    except ValueError:
        return None


def main(dry_run: bool = False) -> None:
    today = date.today()
    cutoff = today - timedelta(days=WINDOW_DAYS)  # dates < cutoff get archived

    tag = "[DRY RUN] " if dry_run else ""
    archived_files: list[str] = []
    archived_dirs: list[str] = []
    created_dirs: list[str] = []

    # ── 1. Archive old raw directories ────────────────────────────────────────
    if RAW_DIR.exists():
        for entry in sorted(RAW_DIR.iterdir()):
            if not entry.is_dir():
                continue
            entry_date = parse_date(entry.name)
            if entry_date is None or entry_date >= cutoff:
                continue
            dest = ARCHIVE_RAW_DIR / entry.name
            if dest.exists():
                print(f"  SKIP (dest exists): raw/{entry.name}")
                continue
            print(f"  {tag}Archive raw dir: raw/{entry.name} -> archive/raw/{entry.name}")
            if not dry_run:
                ARCHIVE_RAW_DIR.mkdir(parents=True, exist_ok=True)
                shutil.move(str(entry), str(dest))
            archived_dirs.append(entry.name)

    # ── 2. Archive old journal .md files ──────────────────────────────────────
    for md_file in sorted(JOURNAL_DIR.glob("*.md")):
        file_date = parse_date(md_file.stem)
        if file_date is None or file_date >= cutoff:
            continue
        dest = ARCHIVE_DIR / md_file.name
        if dest.exists():
            print(f"  SKIP (dest exists): {md_file.name}")
            continue
        print(f"  {tag}Archive journal: {md_file.name} -> archive/{md_file.name}")
        if not dry_run:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(md_file), str(dest))
        archived_files.append(md_file.name)

    # ── 3. Create missing raw dirs for the active window ──────────────────────
    for offset in range(WINDOW_DAYS + 1):  # cutoff … today inclusive
        day = cutoff + timedelta(days=offset)
        raw_day_dir = RAW_DIR / day.isoformat()
        if not raw_day_dir.exists():
            print(f"  {tag}Create raw dir: raw/{day.isoformat()}/")
            if not dry_run:
                raw_day_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(day.isoformat())

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(f"{'[DRY RUN] ' if dry_run else ''}Done.")
    print(f"  Archived {len(archived_files)} journal file(s):  {', '.join(archived_files) or 'none'}")
    print(f"  Archived {len(archived_dirs)} raw director(y/ies): {', '.join(archived_dirs) or 'none'}")
    print(f"  Created  {len(created_dirs)} raw director(y/ies): {', '.join(created_dirs) or 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making any changes.",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
