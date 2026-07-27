#!/usr/bin/env python3
"""
Parse Linux kernel patch series from email subject lines.

Reads subject lines (one per line, or as a JSON array of objects) from
stdin or a file, extracts patch series metadata (version, sequence, total,
flags), groups related patches by base subject + author, and outputs
structured JSON.

Also exposes slugify_subject() for generating filesystem-safe slugs from
patch base subjects, used by the LKML sched daily digest skill for archive
file naming.

Usage:
    # From a text file (one subject per line):
    python3 parse_series.py subjects.txt

    # From stdin (one subject per line):
    cat subjects.txt | python3 parse_series.py

    # From a JSON array of {"subject": "...", "author": "..."} objects:
    python3 parse_series.py --json emails.json

    # Slugify a single subject (prints the slug):
    python3 parse_series.py --slug "sched/fair: fix load balance on numa"

Output:
    JSON array of series objects, each containing:
        base_subject      : subject with [PATCH ...] prefix stripped
        author           : submitter (empty if unknown)
        current_version  : highest version number seen
        versions         : list of {version, seq, total, flags, raw}
        has_tip         : bool, whether a tip-bot reply exists
        tip_branches     : list of tip branch names
        has_stable       : bool, whether a stable-commit reply exists
        slug             : slugify_subject(base_subject)
"""

import sys
import re
import json
import argparse
from collections import defaultdict


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Match [PATCH ...] prefix, capturing the inner content (may be empty).
# Examples:
#   [PATCH] sched: foo
#   [PATCH v2] sched: foo
#   [PATCH v3 1/7] sched: foo
#   [PATCH v2 3/7 RFC] sched: foo
#   [PATCH RFC 1/4] sched: foo        ← flags before version
#   [PATCH RESEND v3 2/7] sched: foo   ← flags before version
#   [PATCH RFC RESEND v2 1/4] sched: foo
PATCH_PREFIX_RE = re.compile(
    r'^\s*\[\s*PATCH(?:\s+(?P<inner>[^\]]+))?\s*\]\s*',
    re.IGNORECASE,
)

# Extract version / seq / total / flags from the inner content.
PATCH_VERSION_RE = re.compile(r'\bv(?P<version>\d+)\b', re.IGNORECASE)
PATCH_SEQ_RE = re.compile(r'(?P<seq>\d+)/(?P<total>\d+)')
PATCH_FLAGS_RE = re.compile(r'\b(?:RFC|RESEND|WIP)\b', re.IGNORECASE)

# Match tip-bot notifications: [tip: sched/urgent] ...
TIP_PREFIX_RE = re.compile(
    r'^\s*\[\s*tip:\s*(?P<branch>[^\]]+)\s*\]\s*',
    re.IGNORECASE,
)

# Match stable-commit bot replies: [patch stable] / [for stable] / [stable]
STABLE_PREFIX_RE = re.compile(
    r'^\s*\[\s*(?:patch\s+stable|for\s+stable|stable)[^\]]*\]\s*',
    re.IGNORECASE,
)

# Match "Re:" / "Fwd:" prefixes on replies (repeated, e.g. "Re: Re: foo")
REPLY_PREFIX_RE = re.compile(r'^\s*(?:Re|Fwd)\s*:\s*', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Core parsing functions
# ---------------------------------------------------------------------------

def parse_subject(subject):
    """
    Parse a single email subject line into structured metadata.

    Returns a dict with keys:
        raw          : original subject
        base_subject : subject with prefix and version/seq stripped
        version      : int (1 if not specified)
        seq          : int or None (None for non-numbered single patches)
        total        : int or None
        flags        : list of uppercase strings (e.g. ['RFC'])
        kind         : 'patch' | 'tip' | 'stable' | 'other'
        branch       : tip branch name (only for kind='tip')
    """
    result = {
        'raw': subject,
        'base_subject': subject.strip(),
        'version': 1,
        'seq': None,
        'total': None,
        'flags': [],
        'kind': 'other',
        'branch': None,
    }

    # Try tip-bot notification first
    m = TIP_PREFIX_RE.match(subject)
    if m:
        result['kind'] = 'tip'
        result['branch'] = m.group('branch').strip()
        result['base_subject'] = subject[m.end():].strip()
        return result

    # Try stable-commit bot
    m = STABLE_PREFIX_RE.match(subject)
    if m:
        result['kind'] = 'stable'
        result['base_subject'] = subject[m.end():].strip()
        return result

    # Try patch prefix
    m = PATCH_PREFIX_RE.match(subject)
    if m:
        result['kind'] = 'patch'
        inner = m.group('inner') or ''
        vm = PATCH_VERSION_RE.search(inner)
        sm = PATCH_SEQ_RE.search(inner)
        result['version'] = int(vm.group('version')) if vm else 1
        result['seq'] = int(sm.group('seq')) if sm else None
        result['total'] = int(sm.group('total')) if sm else None
        result['flags'] = [f.upper() for f in PATCH_FLAGS_RE.findall(inner)]
        result['base_subject'] = subject[m.end():].strip()
        return result

    # Plain reply or discussion — strip Re:/Fwd: prefixes (repeated), then
    # try to extract patch prefix so replies to a patch series are grouped
    # correctly
    base = subject
    while True:
        new_base = REPLY_PREFIX_RE.sub('', base, count=1).strip()
        if new_base == base:
            break
        base = new_base
    m = PATCH_PREFIX_RE.match(base)
    if m:
        # This is a reply to a patch — extract metadata and strip prefix
        # so it groups with the original patch series
        inner = m.group('inner') or ''
        vm = PATCH_VERSION_RE.search(inner)
        sm = PATCH_SEQ_RE.search(inner)
        result['version'] = int(vm.group('version')) if vm else 1
        result['seq'] = int(sm.group('seq')) if sm else None
        result['total'] = int(sm.group('total')) if sm else None
        result['flags'] = [f.upper() for f in PATCH_FLAGS_RE.findall(inner)]
        result['base_subject'] = base[m.end():].strip()
    else:
        result['base_subject'] = base
    return result


def slugify_subject(subject):
    """
    Generate a filesystem-safe slug from a patch base subject.

    Rules (must match the naming convention in SKILL.md Step 5):
        - Lowercase
        - Replace non-alphanumeric characters (incl. CJK punctuation,
          slashes, colons, brackets) with '-'
        - Collapse consecutive '-' into one
        - Strip leading/trailing '-'
        - Truncate to 60 characters
    """
    s = subject.lower()
    # Replace any run of non-alphanumeric characters with a single '-'
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    if len(s) > 60:
        s = s[:60].rstrip('-')
    return s


def _find_matching_group(groups, base_subject):
    """Find a matching patch group for a reply (tip/stable/other).

    Tries three levels of matching:
    1. Exact match
    2. Normalized match (lowercase + strip extra whitespace)
    3. Substring match (normalized, one is substring of the other)

    Returns the matching group key, or None if no match found.
    """
    # 1. Exact match
    for k in groups:
        if k[0] == base_subject:
            return k
    # 2. Normalized match (case-insensitive, whitespace-normalized)
    norm = ' '.join(base_subject.lower().split())
    for k in groups:
        if ' '.join(k[0].lower().split()) == norm:
            return k
    # 3. Substring match (normalized)
    for k in groups:
        k_norm = ' '.join(k[0].lower().split())
        if norm in k_norm or k_norm in norm:
            return k
    return None


def group_series(entries):
    """
    Group parsed subject entries into logical patch series.

    A series is identified by (base_subject, author) — different versions of
    the same subject by the same author are grouped together. Tip-bot and
    stable-commit replies are attached to the matching base_subject (author
    left empty since the bot sender is not the original author).

    Args:
        entries: list of dicts, each with at least 'subject' and optionally
                 'author'.

    Returns:
        list of series dicts (sorted by base_subject), each containing:
            base_subject    : str
            author          : str
            current_version : int or None
            versions        : list of version dicts (sorted)
            has_tip         : bool
            tip_branches    : list of str
            has_stable      : bool
            slug            : str
    """
    parsed = []
    for e in entries:
        subject = e.get('subject', '')
        author = e.get('author', '')
        info = parse_subject(subject)
        info['author'] = author
        parsed.append(info)

    groups = defaultdict(lambda: {
        'base_subject': '',
        'author': '',
        'versions': [],
        'has_tip': False,
        'tip_branches': [],
        'has_stable': False,
    })

    # Two-pass grouping: patches first, then tip/stable/other replies.
    # This allows replies to find and attach to an existing patch series
    # (keyed by base_subject + author) rather than creating a separate
    # (base_subject, '') group that would never merge with the patch.
    patches = [p for p in parsed if p['kind'] == 'patch']
    replies = [p for p in parsed if p['kind'] != 'patch']

    for p in patches:
        key = (p['base_subject'], p['author'])
        g = groups[key]
        g['base_subject'] = p['base_subject']
        if p['author']:
            g['author'] = p['author']
        g['versions'].append({
            'version': p['version'],
            'seq': p['seq'],
            'total': p['total'],
            'flags': p['flags'],
            'raw': p['raw'],
        })

    for p in replies:
        # Try to find an existing patch group with a matching base_subject
        # (any author). Uses fuzzy matching to handle minor differences like
        # case changes (e.g. tip-bot may capitalize "fix" -> "Fix").
        match_key = _find_matching_group(groups, p['base_subject'])
        if match_key is None:
            match_key = (p['base_subject'], '')
        g = groups[match_key]
        g['base_subject'] = p['base_subject']
        if p['kind'] == 'tip':
            g['has_tip'] = True
            if p['branch']:
                g['tip_branches'].append(p['branch'])
        elif p['kind'] == 'stable':
            g['has_stable'] = True
        else:
            # 'other' — add as a version entry
            g['versions'].append({
                'version': p['version'],
                'seq': p['seq'],
                'total': p['total'],
                'flags': p['flags'],
                'raw': p['raw'],
            })

    result = []
    for g in groups.values():
        g['versions'].sort(key=lambda v: (v['version'], v['seq'] or 0))
        g['current_version'] = (
            g['versions'][-1]['version'] if g['versions'] else None
        )
        g['slug'] = slugify_subject(g['base_subject'])
        result.append(g)

    result.sort(key=lambda s: s['base_subject'])
    return result


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_input(input_path, as_json):
    """Read subject entries from file/stdin as text or JSON."""
    if as_json:
        if input_path == '-' or not input_path:
            text = sys.stdin.read()
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return json.loads(text)

    # Plain text: one subject per line
    if input_path == '-' or not input_path:
        lines = sys.stdin.read().splitlines()
    else:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    return [{'subject': line, 'author': ''} for line in lines if line.strip()]


def main():
    parser = argparse.ArgumentParser(
        description='Parse Linux kernel patch series from email subject lines.',
    )
    parser.add_argument(
        'input', nargs='?', default='-',
        help='Input file (default: stdin)',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Treat input as a JSON array of {subject, author} objects',
    )
    parser.add_argument(
        '--slug', metavar='SUBJECT',
        help='Slugify a single subject and print the result',
    )
    args = parser.parse_args()

    if args.slug:
        print(slugify_subject(args.slug))
        return

    entries = read_input(args.input, args.json)
    if not entries:
        print('[]')
        return

    series = group_series(entries)
    print(json.dumps(series, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
