"""
Read all recipe markdown files from the recipes/ directory and output structured JSON.

Output: .tmp/recipes.json
Each recipe includes: name, tags, servings, prep_minutes, cook_minutes, ingredients, filename
"""

import json
import re
import sys
from pathlib import Path

RECIPES_DIR = Path("context/recipes")
OUTPUT_FILE = Path(".tmp/recipes.json")


def parse_duration(text):
    """Convert '20m', '1h', '1h 30m' to total minutes."""
    text = text.strip().lower()
    total = 0
    for h in re.findall(r"(\d+)\s*h", text):
        total += int(h) * 60
    for m in re.findall(r"(\d+)\s*m", text):
        total += int(m)
    return total or None


def parse_recipe(filepath: Path) -> dict:
    """Parse a single recipe markdown file into a dict."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    recipe = {
        "filename": filepath.name,
        "name": None,
        "tags": [],
        "servings": None,
        "prep_minutes": None,
        "cook_minutes": None,
        "ingredients": [],
        "notes": [],
    }

    current_section = None

    for line in lines:
        stripped = line.strip()

        # Title (first H1)
        if stripped.startswith("# ") and recipe["name"] is None:
            recipe["name"] = stripped[2:].strip()
            continue

        # Metadata line: **Servings:** 4 | **Prep:** 20m | **Cook:** 30m
        if stripped.startswith("**Servings:**") or stripped.startswith("**Prep:**") or "**Tags:**" in stripped:
            # Servings
            m = re.search(r"\*\*Servings:\*\*\s*(\d+)", stripped)
            if m:
                recipe["servings"] = int(m.group(1))
            # Prep
            m = re.search(r"\*\*Prep:\*\*\s*([\w\s]+?)(?:\s*\||\s*$)", stripped)
            if m:
                recipe["prep_minutes"] = parse_duration(m.group(1))
            # Cook
            m = re.search(r"\*\*Cook:\*\*\s*([\w\s]+?)(?:\s*\||\s*$)", stripped)
            if m:
                recipe["cook_minutes"] = parse_duration(m.group(1))
            continue

        if "**Tags:**" in stripped:
            m = re.search(r"\*\*Tags:\*\*\s*(.+)", stripped)
            if m:
                recipe["tags"] = [t.strip() for t in m.group(1).split(",")]
            continue

        # Section headers
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
            continue

        # Ingredients
        if current_section == "ingredients" and stripped.startswith("- "):
            ingredient = stripped[2:].strip()
            if ingredient:
                recipe["ingredients"].append(ingredient)
            continue

        # Notes
        if current_section == "notes" and stripped.startswith("- "):
            note = stripped[2:].strip()
            if note:
                recipe["notes"].append(note)
            continue

    # Skip the example template
    if filepath.name.startswith("_"):
        return None

    if not recipe["name"]:
        print(f"  WARNING: No title found in {filepath.name}, skipping.")
        return None

    return recipe


def main():
    if not RECIPES_DIR.exists():
        print(f"ERROR: recipes/ directory not found.")
        sys.exit(1)

    recipe_files = sorted(RECIPES_DIR.glob("*.md"))
    recipes = []

    for filepath in recipe_files:
        if filepath.name.startswith("_"):
            continue  # Skip templates
        result = parse_recipe(filepath)
        if result:
            recipes.append(result)
            print(f"  ✓ {result['name']} ({len(result['ingredients'])} ingredients, tags: {', '.join(result['tags']) or 'none'})")

    if not recipes:
        print("WARNING: No recipes found. Add .md files to the recipes/ folder.")
        print("  See recipes/_example.md for the expected format.")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(recipes, indent=2), encoding="utf-8")
    print(f"\n✓ {len(recipes)} recipes written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
