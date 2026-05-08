"""Validate that every post has a known category and only known tags."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomy import ALL_NAMES, POSTS, parse_front_matter, parse_list  # noqa: E402


def main() -> int:
    errors: list[str] = []
    ok = 0
    for p in sorted(POSTS.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        fm, _, _ = parse_front_matter(text)
        if not fm:
            errors.append(f"{p.name}: no front matter")
            continue
        cat_raw = fm.get("category", "")
        cat = cat_raw.strip().strip('"').strip("'")
        tags = parse_list(fm.get("tags", ""))

        had_error = False
        if not cat:
            errors.append(f"{p.name}: missing category")
            had_error = True
        elif cat not in ALL_NAMES:
            errors.append(f"{p.name}: unknown category {cat!r}")
            had_error = True
        bad = [t for t in tags if t not in ALL_NAMES]
        if bad:
            errors.append(f"{p.name}: unknown tags {bad}")
            had_error = True
        if not had_error:
            ok += 1

    total = ok + len({e.split(":")[0] for e in errors})
    print(f"OK: {ok}")
    print(f"Errors: {len(errors)}")
    for e in errors[:30]:
        print(f"  {e}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
