"""Rename post files whose slug contains ugly scraped artifacts to a clean
slug derived from the current (already cleaned) title. Adds a redirect_from
entry preserving the old permalink.

Usage:
    python scripts/rename_ugly_slugs.py [--apply]
"""
from __future__ import annotations
import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

DATE_SLUG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.*)\.md$")
FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"([^"\n]*)"\s*$', re.MULTILINE)
REDIRECT_BLOCK_RE = re.compile(r"^redirect_from:\n(?:  - .+\n)+", re.MULTILINE)

# Markers that indicate a slug needs cleaning.
UGLY_MARKERS = (
    "-on-instagram-quot-",
    "-on-tiktok-quot-",
    "-on-youtube-quot-",
)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    # Cap length so URLs stay reasonable.
    if len(text) > 70:
        text = text[:70].rsplit("-", 1)[0]
    return text


def permalink_for(date: str, slug: str) -> str:
    y, m, d = date.split("-")
    return f"/{y}/{m}/{d}/{slug}/"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    used_targets: set[str] = set()
    plans: list[tuple[Path, Path, str]] = []  # old_path, new_path, old_permalink

    for p in sorted(POSTS.glob("*.md")):
        m = DATE_SLUG_RE.match(p.name)
        if not m:
            continue
        date, slug = m.group(1), m.group(2)
        if not any(x in slug for x in UGLY_MARKERS):
            # Also catch the `2026-04-29-.md` case (empty slug).
            if slug:
                continue
        text = p.read_text(encoding="utf-8")
        fmm = FRONT_RE.match(text)
        if not fmm:
            continue
        tm = TITLE_RE.search(fmm.group(1))
        if not tm:
            continue
        new_slug = slugify(tm.group(1))
        if not new_slug or new_slug == slug:
            continue
        # Avoid collisions in same date.
        candidate = new_slug
        i = 2
        while (POSTS / f"{date}-{candidate}.md").exists() or f"{date}-{candidate}" in used_targets:
            candidate = f"{new_slug}-{i}"
            i += 1
        used_targets.add(f"{date}-{candidate}")
        new_path = POSTS / f"{date}-{candidate}.md"
        plans.append((p, new_path, permalink_for(date, slug)))

    for old, new, old_link in plans:
        print(f"  {old.name}")
        print(f"    -> {new.name}")
        print(f"    redirect_from: {old_link}")

    if args.apply:
        for old, new, old_link in plans:
            text = old.read_text(encoding="utf-8")
            fmm = FRONT_RE.match(text)
            assert fmm
            fm = fmm.group(1)
            existing = REDIRECT_BLOCK_RE.search(fm)
            if existing:
                if old_link not in existing.group(0):
                    block = existing.group(0).rstrip() + f"\n  - {old_link}\n"
                    new_fm = fm.replace(existing.group(0), block, 1)
                else:
                    new_fm = fm
            else:
                new_fm = fm.rstrip() + f"\nredirect_from:\n  - {old_link}\n"
            new_text = text.replace(fmm.group(0), f"---\n{new_fm}---", 1)
            new.write_text(new_text, encoding="utf-8")
            old.unlink()

    print(f"\n{'Renamed' if args.apply else 'Would rename'} {len(plans)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
