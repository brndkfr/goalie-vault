"""List/delete posts with generic titles AND missing author/handle.

Used to clean up auto-generated stubs that lack any creator metadata.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

TITLE_RE = re.compile(r'^title:\s*["\'](.+?)["\']', re.M)
AUTHOR_RE = re.compile(r'^author:\s*["\'](.*?)["\']', re.M)
HANDLE_RE = re.compile(r'^handle:\s*["\'](.*?)["\']', re.M)
GENERIC = re.compile(
    r"^(Goalie\s+(?:Training|Coordination|Warmup|Strength|Movement|Reaction)\s+Drill)\.?$",
    re.I,
)


def main() -> int:
    apply = "--apply" in sys.argv
    targets: list[Path] = []
    for p in sorted(POSTS.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        m_title = TITLE_RE.search(text)
        m_author = AUTHOR_RE.search(text)
        m_handle = HANDLE_RE.search(text)
        if not m_title:
            continue
        title = m_title.group(1).strip()
        author = (m_author.group(1).strip() if m_author else "")
        handle = (m_handle.group(1).strip() if m_handle else "")
        if GENERIC.match(title) and not author and not handle:
            targets.append(p)
            print(f"  {p.name} | {title}")
    print(f"\n{len(targets)} candidates.")
    if apply:
        for p in targets:
            p.unlink()
        print(f"Deleted {len(targets)} file(s).")
    else:
        print("Re-run with --apply to delete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
