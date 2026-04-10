#!/usr/bin/env python3
"""
format_text_messages.py - Format Google Messages web export HTML to plain text

Usage: python tools/format_text_messages.py <path_to_html>

Source:      context/text_messages/raw/
Destination: context/text_messages/formatted/

Parses aria-label attributes from Google Messages HTML exports.
Auto-detects sender and contact names from the HTML. Prompts if not found.
"""

import re
import sys
import os
from datetime import datetime


def parse_timestamp(date_str, time_str):
    """Convert 'December 21, 2025' + '1:16\u202fPM' to '2025-12-21 13:16'."""
    time_str = time_str.replace('\u202f', ' ').strip()
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%B %d, %Y %I:%M %p")
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return f"{date_str} {time_str}"


def extract_account_name(content):
    """Extract first name from Google Account aria-label."""
    m = re.search(r'aria-label="Google Account:\s*([^(\n\r"]+?)[\s\n\r(]', content)
    if m:
        full_name = m.group(1).strip()
        return full_name.split()[0] if full_name else None
    return None


def extract_messages(content):
    """
    Parse all message aria-labels.

    Outgoing: 'You said: {msg}. Sent on {date} at {time}[. SMS].'
    Incoming: '{Name} said: {msg}. Received on {date} at {time}.'

    Uses [^"]+ to stay within the aria-label attribute — prevents
    the regex from crossing message boundaries.
    """
    pattern = re.compile(
        r'aria-label="'
        r'(?:(You) said: |([^"]+?) said: )'
        r'([^"]+?)'
        r'\. (?:Sent|Received) on '
        r'([A-Za-z]+ \d{1,2}, \d{4})'
        r' at '
        r'(\d{1,2}:\d{2}[\u202f ][AP]M)'
        r'[^"]*"'
    )

    messages = []
    seen = set()

    for m in pattern.finditer(content):
        is_you = (m.group(1) == 'You')
        contact_name = m.group(2) if not is_you else None
        message = m.group(3)
        timestamp = parse_timestamp(m.group(4), m.group(5))

        key = (is_you, timestamp, message[:60])
        if key in seen:
            continue
        seen.add(key)

        messages.append({
            'is_you': is_you,
            'contact_name': contact_name,
            'message': message,
            'timestamp': timestamp,
        })

    return messages


def detect_contact_name(messages):
    """Return the contact name from incoming messages, or None."""
    for msg in messages:
        if not msg['is_you'] and msg['contact_name']:
            return msg['contact_name']
    return None


def format_output(messages, your_name, contact_name):
    """
    Format messages as plain text.

    Each message: Name (YYYY-MM-DD HH:MM) first line of message
    Additional lines in the same message are appended as-is (no prefix).
    """
    lines = []
    for msg in messages:
        name = your_name if msg['is_you'] else contact_name
        msg_lines = msg['message'].split('\n')
        lines.append(f"{name} ({msg['timestamp']}) {msg_lines[0]}")
        for extra_line in msg_lines[1:]:
            lines.append(extra_line)
    return '\n'.join(lines)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("Usage: python tools/format_text_messages.py <path_to_html>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]

    if not os.path.exists(html_path):
        print(f"Error: File not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Auto-detect names
    your_name = extract_account_name(content)
    messages = extract_messages(content)
    contact_name = detect_contact_name(messages)

    if your_name:
        print(f"Detected sender (You): {your_name}")
    else:
        your_name = input("Could not detect your name. Who is the sender? ").strip()

    if contact_name:
        print(f"Detected contact: {contact_name}")
    else:
        contact_name = input("Could not detect contact name. Who is the other person? ").strip()

    if not messages:
        print("No messages found. The HTML structure may have changed.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(messages)} messages ({sum(1 for m in messages if m['is_you'])} outgoing, "
          f"{sum(1 for m in messages if not m['is_you'])} incoming)")

    output = format_output(messages, your_name, contact_name)

    # Output path: sibling 'formatted/' directory next to 'raw/'
    base_name = os.path.splitext(os.path.basename(html_path))[0]
    raw_dir = os.path.dirname(os.path.abspath(html_path))
    parent_dir = os.path.dirname(raw_dir)
    output_dir = os.path.join(parent_dir, 'formatted')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}_formatted.txt")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Saved: {output_path}")


if __name__ == '__main__':
    main()
