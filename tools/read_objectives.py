"""
Tool: read_objectives.py
Reads and formats objectives markdown files for agent consumption.
Output: .tmp/objectives_summary.txt

Usage:
  python tools/read_objectives.py
"""

import sys
from pathlib import Path

OBJECTIVES_DIR = Path("context/objectives")
OUTPUT_FILE = Path(".tmp/objectives_summary.txt")
FILES = [
    ("personal_goals.md", "PERSONAL GOALS"),
    ("work_objectives.md", "WORK OBJECTIVES"),
]

TEMPLATE_MARKERS = [
    "<!-- What do you want",
    "<!-- What are the 2-3",
    "<!-- What must happen",
    "<!-- Daily/weekly commitments",
    "<!-- Anything else",
    "<!-- Active projects",
    "<!-- Key results",
    "<!-- Most important work",
    "<!-- Hard deadlines",
    "<!-- Team members",
]


def is_template_line(line: str) -> bool:
    return any(marker in line for marker in TEMPLATE_MARKERS)


def is_substantive(content: str) -> bool:
    """Return True if file has real content beyond headers and template comments."""
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped == "-":
            continue
        if is_template_line(stripped):
            continue
        return True
    return False


def clean_content(content: str) -> str:
    """Remove template comments and blank bullet points."""
    lines = []
    for line in content.splitlines():
        if is_template_line(line):
            continue
        # Skip empty bullet points
        if line.strip() == "-":
            continue
        lines.append(line)
    # Collapse multiple blank lines into one
    cleaned = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()


def main():
    Path(".tmp").mkdir(exist_ok=True)
    sections = []
    warnings = []

    for filename, label in FILES:
        filepath = OBJECTIVES_DIR / filename
        if not filepath.exists():
            warnings.append(f"WARNING: {filepath} not found — skipping.")
            continue

        content = filepath.read_text(encoding="utf-8")

        if not is_substantive(content):
            warnings.append(
                f"WARNING: {filepath} appears to be empty or unfilled. "
                "Consider adding your objectives for a better morning plan."
            )
            sections.append(f"=== {label} ===\n[Not yet filled in]")
        else:
            cleaned = clean_content(content)
            sections.append(f"=== {label} ===\n{cleaned}")

    output = "\n\n".join(sections)

    if warnings:
        warning_block = "\n".join(warnings)
        output = warning_block + "\n\n" + output

    OUTPUT_FILE.write_text(output, encoding="utf-8")

    for w in warnings:
        print(w)
    print(f"Objectives written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
