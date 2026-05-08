"""Clean low-quality post titles:
- Strip 'X on Instagram: "...' platform suffix titles, replacing with caption fragment.
- Convert ALL-CAPS titles to Title Case.
- Decode HTML entities and strip stray '&;' fragments.
"""
from __future__ import annotations
import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

FRONT_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TITLE_RE = re.compile(r'^title:\s*"([^"\n]*)"\s*$', re.MULTILINE)
DESC_RE = re.compile(r'^description:\s*"([^"\n]*)"\s*$', re.MULTILINE)


def clean_text(t: str) -> str:
    t = html.unescape(t)
    # Strip leftover '&;' artifacts produced by previous cleaning passes.
    t = re.sub(r"\s*&;\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_caption_title(title: str, desc: str) -> str:
    """Pull a meaningful phrase from the IG-style title or description."""
    # Prefer caption from description: "<n> likes, <m> comments - handle on <date>: "<caption>..."
    desc_clean = clean_text(desc)
    m = re.search(r':\s*"([^"]{4,})', desc_clean)
    if m:
        cap = m.group(1)
    else:
        # Fallback: caption from the title after "Instagram: <quote>"
        title_clean = clean_text(title)
        m = re.search(r"on (?:Instagram|TikTok|YouTube):\s*\"?(.+)$", title_clean, re.IGNORECASE)
        cap = m.group(1) if m else title_clean
    cap = cap.strip(' "\'')
    # First sentence / line.
    cap = re.split(r"[.\n!?]", cap, maxsplit=1)[0].strip()
    # Strip any residual whitespace control chars.
    cap = re.sub(r"\s+", " ", cap).strip()
    # Cap length.
    if len(cap) > 80:
        cap = cap[:77].rstrip() + "..."
    return cap or title


SMALL_WORDS = {"a","an","and","as","at","but","by","for","in","of","on","or","the","to","vs","with"}


def title_case(t: str) -> str:
    words = re.split(r"(\s+|[\-/|()])", t.lower())
    out = []
    word_idx = 0
    for tok in words:
        if not tok or tok.isspace() or tok in {"-", "/", "|", "(", ")"}:
            out.append(tok)
            continue
        if word_idx > 0 and tok in SMALL_WORDS:
            out.append(tok)
        else:
            out.append(tok[:1].upper() + tok[1:])
        word_idx += 1
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed: list[tuple[str, str, str]] = []
    for p in sorted(POSTS.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        m = FRONT_RE.match(text)
        if not m:
            continue
        fm = m.group(1)
        tm = TITLE_RE.search(fm)
        if not tm:
            continue
        old = tm.group(1)
        old_clean = clean_text(old)
        new = old

        if re.search(r"on (?:Instagram|TikTok|YouTube):", old_clean, re.IGNORECASE):
            dm = DESC_RE.search(fm)
            desc = dm.group(1) if dm else ""
            new = extract_caption_title(old, desc)
        elif old_clean.isupper() and len(old_clean.split()) >= 2:
            new = title_case(old_clean)
        elif "&;" in old or "&quot" in old or "&amp" in old:
            new = clean_text(old)

        if new and new != old:
            changed.append((p.name, old, new))
            if args.apply:
                new_fm = TITLE_RE.sub(f'title: "{new}"', fm, count=1)
                new_text = text.replace(m.group(0), f"---\n{new_fm}\n---", 1)
                p.write_text(new_text, encoding="utf-8")

    for name, old, new in changed:
        print(f"  {name}")
        print(f"    OLD: {old!r}")
        print(f"    NEW: {new!r}")
    print(f"\n{'Applied' if args.apply else 'Would apply'} {len(changed)} change(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
