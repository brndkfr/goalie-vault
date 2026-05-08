"""Backfill author/handle on posts that have empty values, parsing them from
the description text or the title.

Pattern A (Instagram description from yt-dlp):
    "<n> likes, <m> comments - <handle> on <Month Day, Year>: ..."
Pattern B (title): "<Author Display> on Instagram: ..."

Usage:
    python scripts/backfill_from_description.py [--apply]
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
DESC_HANDLE_RE = re.compile(r"comments?\s*-\s*([A-Za-z0-9_.]+)\s+on\s+", re.IGNORECASE)
TITLE_AUTHOR_RE = re.compile(r'^title:\s*"([^"]+?)\s+on\s+Instagram', re.IGNORECASE | re.MULTILINE)


def field(fm: str, name: str) -> str | None:
    m = re.search(rf'^{name}:\s*"?([^"\n]*)"?\s*$', fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def set_field(fm: str, name: str, value: str) -> str:
    pattern = rf'^({name}:\s*)"?[^"\n]*"?\s*$'
    return re.sub(pattern, rf'\1"{value}"', fm, count=1, flags=re.MULTILINE)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed = []
    skipped = []
    for path in sorted(POSTS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = FRONT_RE.match(text)
        if not m:
            continue
        fm = m.group(1)
        author = field(fm, "author") or ""
        handle = field(fm, "handle") or ""
        if author and handle:
            continue

        new_author = author
        new_handle = handle

        # handle from description
        desc = field(fm, "description") or ""
        if not new_handle:
            dm = DESC_HANDLE_RE.search(desc)
            if dm:
                new_handle = dm.group(1)

        # author from title pattern
        if not new_author:
            tm = TITLE_AUTHOR_RE.search(fm)
            if tm:
                cand = tm.group(1).strip()
                # strip trailing "&;&;" / quotes / ampersands
                cand = re.sub(r"[&;\s]+$", "", cand).strip()
                # Drop stray HTML-entity fragments like "&;" inside the name.
                cand = re.sub(r"\s*&;\s*", "", cand).strip()
                cand = re.sub(r"\s+", " ", cand)
                if cand:
                    new_author = cand

        if (new_author, new_handle) == (author, handle):
            skipped.append(path.name)
            continue

        new_fm = fm
        if new_author and new_author != author:
            new_fm = set_field(new_fm, "author", new_author)
        if new_handle and new_handle != handle:
            new_fm = set_field(new_fm, "handle", new_handle)

        new_text = text.replace(m.group(0), f"---\n{new_fm}\n---", 1)
        changed.append((path.name, author, new_author, handle, new_handle))
        if args.apply:
            path.write_text(new_text, encoding="utf-8")

    for name, a0, a1, h0, h1 in changed:
        print(f"  {name}")
        print(f"    author: {a0!r} -> {a1!r}")
        print(f"    handle: {h0!r} -> {h1!r}")
    print(f"\n{'Applied' if args.apply else 'Would apply'} {len(changed)} change(s); {len(skipped)} unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
