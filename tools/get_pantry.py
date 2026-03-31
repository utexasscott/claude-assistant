"""
Read pantry.md and output a structured JSON inventory.

Output: .tmp/pantry.json
Structure: { "categories": { "Proteins": [...], "Produce": [...], ... }, "all_items": [...] }
"""

import json
import re
import sys
from pathlib import Path

PANTRY_FILE = Path("pantry.md")
OUTPUT_FILE = Path(".tmp/pantry.json")


def normalize(text):
    """Lowercase and strip quantity/parenthetical info for matching."""
    # Remove quantities in parens like "(2 lbs)", "(3)", "(1 can)"
    text = re.sub(r"\(.*?\)", "", text)
    # Remove leading quantities like "1 lb", "2 tbsp"
    text = re.sub(r"^\d+[\d./]*\s*(lb|lbs|oz|cup|cups|tbsp|tsp|can|cans|bag|bags|head|heads|stick|sticks|clove|cloves|pkg|package|bunch)s?\s+", "", text, flags=re.IGNORECASE)
    return text.strip().lower()


def main():
    if not PANTRY_FILE.exists():
        print(f"ERROR: {PANTRY_FILE} not found.")
        sys.exit(1)

    text = PANTRY_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()

    categories = {}
    current_category = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            current_category = stripped[3:].strip()
            categories[current_category] = []
            continue

        if current_category and stripped.startswith("- "):
            item = stripped[2:].strip()
            if item:
                categories[current_category].append(item)

    all_items = []
    for items in categories.values():
        all_items.extend(items)

    # Build a normalized lookup list for the agent to use for matching
    normalized_items = [normalize(item) for item in all_items]

    output = {
        "categories": categories,
        "all_items": all_items,
        "normalized_items": normalized_items,
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2), encoding="utf-8")

    total = len(all_items)
    print(f"✓ Pantry loaded: {total} items across {len(categories)} categories")
    for cat, items in categories.items():
        print(f"  {cat}: {len(items)} items")
    print(f"\n✓ Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
