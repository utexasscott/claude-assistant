#!/usr/bin/env python3
"""
format_ofw.py — Parse and reformat Our Family Wizard conversation exports.

Single file:     python tools/format_ofw.py <file.txt>
                 Reformats one export in chronological order.
                 Output: <file>_formatted.txt

Combine folder:  python tools/format_ofw.py --dir <folder>
                 Merges all .txt files in folder into one unified thread.
                 Detects branching; shows "In reply to #N" when a message
                 is not a reply to the immediately preceding message.
                 Output: <folder>/combined.txt
"""

import re
import sys
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Datetime helpers
# ---------------------------------------------------------------------------

def parse_ofw_datetime(s):
    s = s.strip()
    for fmt in ('%b %d, %Y, %I:%M %p', '%b %d, %Y, %I:%M%p'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def format_dt(dt):
    """Format as 'Apr 4, 2026 - 10:17 AM' (no leading zeros, cross-platform)."""
    hour = dt.hour % 12 or 12
    ampm = 'AM' if dt.hour < 12 else 'PM'
    return f'{dt.strftime("%b")} {dt.day}, {dt.year} - {hour}:{dt.minute:02d} {ampm}'


def title_name(name):
    return ' '.join(w.capitalize() for w in name.strip().split()) if name else 'Unknown'

# ---------------------------------------------------------------------------
# Body extraction
# ---------------------------------------------------------------------------

def extract_body(lines):
    """Strip leading/trailing blank lines and join."""
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return '\n'.join(line.rstrip() for line in lines)

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

FROM_RE = re.compile(r'^From:\s+(.+?)\s+on\s+(.+?)\s*$', re.IGNORECASE)
SENT_RE = re.compile(r'^Sent\s+(.+?)\s*$', re.IGNORECASE)
VIEWED_RE = re.compile(r'^\(Viewed', re.IGNORECASE)
TO_RE = re.compile(r'^To:\s*(.+?)\s*$', re.IGNORECASE)
SUBJ_RE = re.compile(r'^Subject:\s*(.+?)\s*$', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Parsing individual message blocks
# ---------------------------------------------------------------------------

def parse_top_block(lines):
    """
    Parse the header block at the top of an OFW export file.
    This is always the newest message in that branch.

    Expected structure:
        [0] Subject line
        [1] "Sent" or "Inbox"
        [2] sender name
        [3] "Sent Apr 4, 2026, 10:17 AM"
        [4] blank
        [5] "To:"
        [6] recipient name
        [7] "(Viewed ...)"
        [8+] message body
    """
    if len(lines) < 4:
        return None

    subject = lines[0].strip()
    sender, dt, recipient = None, None, None
    body_start = len(lines)

    for i, line in enumerate(lines):
        if i == 0:
            continue
        m = SENT_RE.match(line)
        if m:
            dt = parse_ofw_datetime(m.group(1))
            if i >= 2:
                sender = lines[i - 1].strip()
            continue
        if line.strip().lower() == 'to:' and i + 1 < len(lines):
            recipient = lines[i + 1].strip()
            continue
        if VIEWED_RE.match(line.strip()):
            body_start = i + 1
            break

    body = extract_body(list(lines[body_start:]))
    return {
        'sender': title_name(sender),
        'recipient': title_name(recipient),
        'subject': subject,
        'dt': dt,
        'body': body,
    }


def parse_from_block(lines, match):
    """Parse a quoted message block starting with 'From: name on date'."""
    sender = match.group(1).strip()
    dt = parse_ofw_datetime(match.group(2))
    recipient, subject = None, None
    body_start = 1

    for i, line in enumerate(lines[1:], 1):
        if not recipient:
            m = TO_RE.match(line)
            if m:
                recipient = m.group(1).strip()
                continue
        if not subject:
            m = SUBJ_RE.match(line)
            if m:
                subject = m.group(1).strip()
                body_start = i + 1
                continue

    body = extract_body(list(lines[body_start:]))
    return {
        'sender': title_name(sender),
        'recipient': title_name(recipient),
        'subject': subject or '',
        'dt': dt,
        'body': body,
    }

# ---------------------------------------------------------------------------
# Parse a file as an ordered chain (oldest -> newest)
# ---------------------------------------------------------------------------

def parse_file_as_chain(filepath):
    """
    Parse an OFW export file and return an ordered list of messages,
    oldest first. Consecutive pairs represent parent -> child relationships.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    boundaries = []
    for i, line in enumerate(lines):
        m = FROM_RE.match(line)
        if m:
            boundaries.append((i, m))

    messages = []

    top_end = boundaries[0][0] if boundaries else len(lines)
    top = parse_top_block(lines[:top_end])
    if top:
        messages.append(top)

    for idx, (start, match) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        msg = parse_from_block(lines[start:end], match)
        if msg:
            messages.append(msg)

    # Sort oldest first — this gives the correct chain order
    messages.sort(key=lambda m: m['dt'] or datetime.min)
    return messages

# ---------------------------------------------------------------------------
# Message identity key
# ---------------------------------------------------------------------------

def msg_key(msg):
    """
    Stable unique identifier for a message.
    Uses sender + datetime + body fingerprint to handle the edge case
    where two messages share the same sender and minute (different bodies).
    """
    sender = (msg['sender'] or '').lower().replace(' ', '_')
    dt_str = msg['dt'].strftime('%Y%m%d%H%M') if msg['dt'] else 'no_time'
    # Body fingerprint: first 60 chars, lowercased, spaces normalized
    body_raw = re.sub(r'\s+', ' ', (msg['body'] or '').strip().lower())[:60]
    body_fp = re.sub(r'[^a-z0-9 ]', '', body_raw).replace(' ', '_')
    return f'{sender}|{dt_str}|{body_fp}'

# ---------------------------------------------------------------------------
# Subject normalization
# ---------------------------------------------------------------------------

def normalize_subject(s):
    return re.sub(r'^(Re:\s*)+', '', s or '', flags=re.IGNORECASE).strip()

# ---------------------------------------------------------------------------
# Single-file mode
# ---------------------------------------------------------------------------

def format_single(messages):
    subjects = [normalize_subject(m['subject']) for m in messages]
    unique_subjects = {s for s in subjects if s}
    all_same = len(unique_subjects) == 1
    thread_subject = subjects[0] if all_same else None

    out = []
    if thread_subject:
        out.append(f'# Thread: {thread_subject}')
        out.append('')

    for i, msg in enumerate(messages, 1):
        out.append('---')
        out.append('')
        dt_str = format_dt(msg['dt']) if msg['dt'] else '(unknown time)'
        out.append(f'[#{i}] [{dt_str}]')
        out.append(f'From: {msg["sender"]}')
        out.append(f'To: {msg["recipient"]}')
        if not all_same and msg['subject']:
            out.append(f'Subject: {msg["subject"]}')
        out.append('')
        out.append(msg['body'])
        out.append('')

    out.append('---')
    return '\n'.join(out)

# ---------------------------------------------------------------------------
# Combine mode — build message tree from multiple files
# ---------------------------------------------------------------------------

def build_tree(filepaths):
    """
    Combine chains from multiple OFW export files into a unified message tree.

    Returns:
        sorted_msgs   — all unique messages sorted chronologically
        parent_map    — child_key -> parent_key
        all_messages  — key -> msg dict
    """
    all_messages = {}  # key -> msg
    parent_map = {}    # child_key -> parent_key

    for filepath in filepaths:
        chain = parse_file_as_chain(filepath)

        for msg in chain:
            k = msg_key(msg)
            if k not in all_messages:
                all_messages[k] = msg

        for i in range(1, len(chain)):
            child_k = msg_key(chain[i])
            parent_k = msg_key(chain[i - 1])
            if child_k not in parent_map:
                parent_map[child_k] = parent_k

    sorted_msgs = sorted(all_messages.values(), key=lambda m: m['dt'] or datetime.min)

    # Assign sequential IDs in chronological order
    for i, msg in enumerate(sorted_msgs, 1):
        msg['id'] = i

    return sorted_msgs, parent_map, all_messages


def format_combined(sorted_msgs, parent_map, all_messages):
    """
    Format the merged thread. When a message is not replying to the
    immediately preceding message, show an "In reply to #N" indicator
    with a short excerpt of the parent message.
    """
    subjects = [normalize_subject(m['subject']) for m in sorted_msgs]
    unique_subjects = {s for s in subjects if s}
    all_same = len(unique_subjects) == 1
    thread_subject = subjects[0] if all_same else None

    # Build key -> id lookup
    key_to_id = {msg_key(m): m['id'] for m in sorted_msgs}

    out = []
    if thread_subject:
        out.append(f'# Thread: {thread_subject}')
        out.append('')

    prev_key = None
    for msg in sorted_msgs:
        k = msg_key(msg)
        parent_k = parent_map.get(k)

        out.append('---')
        out.append('')

        dt_str = format_dt(msg['dt']) if msg['dt'] else '(unknown time)'
        out.append(f'[#{msg["id"]}] [{dt_str}]')

        # Show "In reply to" if the parent isn't the immediately preceding message
        if parent_k and parent_k != prev_key:
            parent_id = key_to_id.get(parent_k)
            parent_msg = all_messages.get(parent_k)
            if parent_id and parent_msg:
                excerpt = (parent_msg['body'] or '').replace('\n', ' ').strip()
                if len(excerpt) > 72:
                    excerpt = excerpt[:72] + '...'
                out.append(f'In reply to #{parent_id} ({parent_msg["sender"]}, {format_dt(parent_msg["dt"])}):')
                out.append(f'  > "{excerpt}"')

        out.append(f'From: {msg["sender"]}')
        out.append(f'To: {msg["recipient"]}')
        if not all_same and msg['subject']:
            out.append(f'Subject: {msg["subject"]}')
        out.append('')
        out.append(msg['body'])
        out.append('')

        prev_key = k

    out.append('---')
    return '\n'.join(out)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    if not args:
        print('Usage:')
        print('  python tools/format_ofw.py <file.txt>')
        print('  python tools/format_ofw.py --dir <folder>')
        sys.exit(1)

    if args[0] == '--dir':
        if len(args) < 2:
            print('Error: --dir requires a folder path')
            sys.exit(1)

        folder = args[1]
        if not os.path.isdir(folder):
            print(f'Error: Not a directory: {folder}')
            sys.exit(1)

        txt_files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith('.txt')
            and '_formatted' not in f
            and 'combined' not in f
        )

        if not txt_files:
            print(f'No .txt files found in {folder}')
            sys.exit(1)

        filepaths = [os.path.join(folder, f) for f in txt_files]
        print(f'Combining {len(filepaths)} files: {", ".join(txt_files)}')

        sorted_msgs, parent_map, all_messages = build_tree(filepaths)
        formatted = format_combined(sorted_msgs, parent_map, all_messages)

        output_path = os.path.join(folder, 'combined.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted)

        print(f'Combined {len(sorted_msgs)} unique messages -> {output_path}')

    else:
        filepath = args[0]
        if not os.path.exists(filepath):
            print(f'Error: File not found: {filepath}')
            sys.exit(1)

        chain = parse_file_as_chain(filepath)
        if not chain:
            print('No messages found.')
            sys.exit(1)

        formatted = format_single(chain)
        base, ext = os.path.splitext(filepath)
        output_path = f'{base}_formatted{ext}'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted)

        print(f'Formatted {len(chain)} messages -> {output_path}')


if __name__ == '__main__':
    main()
