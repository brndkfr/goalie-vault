"""Quick audit: list posts whose front matter lacks author or handle."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

AUTHOR_RE = re.compile(r'^author:\s*["\'](.*?)["\']', re.M)
HANDLE_RE = re.compile(r'^handle:\s*["\'](.*?)["\']', re.M)


def main() -> int:
    missing: list[tuple[str, str, str]] = []
    for p in sorted(POSTS.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            continue
        end = text.find("---", 3)
        head = text[:end]
        a = (AUTHOR_RE.search(head).group(1).strip() if AUTHOR_RE.search(head) else "")
        h = (HANDLE_RE.search(head).group(1).strip() if HANDLE_RE.search(head) else "")
        if not a or not h:
            missing.append((p.name, a or "(none)", h or "(none)"))
    print(f"Posts missing author or handle: {len(missing)}")
    for n, a, h in missing:
        print(f"  {n}\n      author={a!r}  handle={h!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
