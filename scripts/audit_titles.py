"""Audit post titles for low-quality / placeholder patterns."""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"([^"\n]*)"\s*$', re.MULTILINE)


def categorize(title: str) -> str | None:
    t = title.strip()
    low = t.lower()
    # IG/yt-dlp scraped titles still containing the source phrase
    if " on instagram" in low or " on tiktok" in low or " on youtube" in low:
        return "scraped-platform-suffix"
    # HTML entity remnants
    if "&quot" in low or "&amp" in low or "&;" in t or "&#" in t:
        return "html-entity-remnant"
    # Generic stub left over
    if re.fullmatch(r"goalie\s+(training|coordination|warmup|strength|movement|reaction)\s+drill\.?", low):
        return "generic-stub"
    if re.fullmatch(r"floorball\s+training\s+drill\.?", low):
        return "generic-stub"
    # Truncated mid-word (ends in hyphen or trailing ellipsis-ish)
    if t.endswith("-") or t.endswith("...") or t.endswith("…"):
        return "truncated"
    # Smart-quote leftover at end
    if t.endswith('"') or t.endswith("'") or t.endswith("”") or t.endswith("“"):
        return "dangling-quote"
    # Very short / non-descriptive
    if len(t) < 6:
        return "too-short"
    # All-caps screaming (3+ words)
    if t.isupper() and len(t.split()) >= 3:
        return "all-caps"
    return None


def main() -> int:
    buckets: dict[str, list[tuple[str, str]]] = {}
    for p in sorted(POSTS.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = FRONT_RE.match(text)
        if not m:
            continue
        tm = TITLE_RE.search(m.group(1))
        if not tm:
            continue
        title = tm.group(1)
        cat = categorize(title)
        if cat:
            buckets.setdefault(cat, []).append((p.name, title))

    total = sum(len(v) for v in buckets.values())
    for cat in sorted(buckets):
        rows = buckets[cat]
        print(f"\n== {cat} ({len(rows)}) ==")
        for name, title in rows:
            print(f"  {name}")
            print(f"    title: {title!r}")
    print(f"\nTotal flagged: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
