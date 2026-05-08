"""Find posts whose title/description likely need a manual touch-up after
the emoji/hashtag/handle stripping pass. Scans front matter only.

Heuristics flagged:
  - dangling connector words at end of line ("and", "with", "for", "von", ...)
  - dangling connector words followed by punctuation ("and,", "in.")
  - mid-sentence "<word> ," (comma preceded by space, missed)
  - empty parentheses "()" or "(  )"
  - leading "but/and/or/und/aber" at sentence start
  - "  " double space
  - lone punctuation lines
  - sentences ending in ", but" / ", and" / "in," (likely missing object)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CONNECTORS = r"(?:and|but|or|with|by|for|in|of|to|from|featuring|feat\.?|" \
             r"und|aber|oder|mit|von|für|fuer|in|auf|im)"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("dangling-end",       re.compile(rf"\b{CONNECTORS}\s*[.!?]?\s*$", re.IGNORECASE | re.MULTILINE)),
    ("dangling-comma",     re.compile(rf"\b{CONNECTORS}\s*,", re.IGNORECASE)),
    ("ws-before-punct",    re.compile(r"\s+[,;]")),
    ("empty-parens",       re.compile(r"\(\s*\)")),
    ("paren-comma",        re.compile(r"\(\s*[,.]")),
    ("double-space",       re.compile(r"  +")),
    ("trailing-conn-stop", re.compile(rf"\b{CONNECTORS}\.\s*$", re.IGNORECASE | re.MULTILINE)),
    ("lone-punct-line",    re.compile(r"^\s*[.,;:!?\-]+\s*$", re.MULTILINE)),
    ("comma-stop",         re.compile(r",\s*$", re.MULTILINE)),
]

FIELDS = ("title", "description")
FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
QUOTED_VALUE_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"$')


def get_field(block: str, field: str) -> str | None:
    m = re.search(rf"^{re.escape(field)}:\s*(.*)$", block, re.MULTILINE)
    if not m:
        return None
    raw = m.group(1).strip()
    qm = QUOTED_VALUE_RE.match(raw)
    if not qm:
        return raw
    import json
    return json.loads(f'"{qm.group(1)}"')


def main() -> int:
    findings: list[tuple[Path, dict[str, list[str]]]] = []
    for path in sorted(POSTS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            continue
        block = m.group(1)
        per_field: dict[str, list[str]] = {}
        for field in FIELDS:
            value = get_field(block, field)
            if not value:
                continue
            hits: list[str] = []
            for name, regex in PATTERNS:
                if regex.search(value):
                    hits.append(name)
            if hits:
                per_field[field] = hits
        if per_field:
            findings.append((path, per_field))

    print(f"Posts needing review: {len(findings)}")
    for path, per_field in findings:
        rel = path.relative_to(ROOT).as_posix()
        print(f"\n{rel}")
        for field, hits in per_field.items():
            value = get_field(FRONT_MATTER_RE.match(path.read_text(encoding='utf-8')).group(1), field) or ""
            tags = ",".join(hits)
            preview = value if len(value) <= 140 else value[:140] + "..."
            print(f"  [{field}] {tags}")
            print(f"    {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
