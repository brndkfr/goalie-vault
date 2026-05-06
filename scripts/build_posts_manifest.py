"""Build scripts/curate/posts_manifest.json for the post curator UI.

Walks _posts/*.md, parses front-matter (regex, no PyYAML dep), and emits one
record per post. Also extracts the canonical category list from index.md so
the UI's category chips stay in sync with what the homepage filters on.

Output schema (per post):
    {
        "filename":    "2017-06-09-goalie-warmup.md",
        "date":        "2017-06-09",
        "title":       "Goalie warmup",
        "author":      "...",
        "handle":      "...",
        "category":    ["strength"],
        "platform":    "instagram",
        "video_id":    "BVHLNF_B3ck",
        "thumbnail":   "/assets/images/thumbs/BVHLNF_B3ck.jpg",
        "thumb_url":   "...absolute URL the UI can render directly...",
        "description": "...",
        "auto_generated": true
    }
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
INDEX = ROOT / "index.md"
OUT = ROOT / "scripts" / "curate" / "posts_manifest.json"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
KV_RE = re.compile(r'^([A-Za-z_]\w*)\s*:\s*(.*)$', re.MULTILINE)
LIST_RE = re.compile(r"^\[(.*)\]$")
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
FILTER_BTN_RE = re.compile(r'data-filter="([^"]+)"')


def yaml_unquote(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.encode("utf-8").decode("unicode_escape")
        return inner
    return value


def parse_list(value: str) -> list[str]:
    """Parse a flow-style YAML list `[a, b, c]` (with optional quotes)."""
    m = LIST_RE.match(value.strip())
    if not m:
        return [yaml_unquote(value)] if value.strip() else []
    inner = m.group(1).strip()
    if not inner:
        return []
    items = [yaml_unquote(p.strip()) for p in inner.split(",")]
    return [i for i in items if i]


def parse_front_matter(text: str) -> dict | None:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return None
    fm: dict = {}
    for kv in KV_RE.finditer(m.group(1)):
        key, raw = kv.group(1), kv.group(2)
        if key == "category":
            fm[key] = parse_list(raw)
        elif raw.strip().lower() in ("true", "false"):
            fm[key] = raw.strip().lower() == "true"
        else:
            fm[key] = yaml_unquote(raw)
    return fm


def thumb_url(post: dict) -> str:
    thumb = (post.get("thumbnail") or "").strip()
    if thumb and thumb != "skip":
        if "://" in thumb:
            return thumb
        # local path like /assets/images/thumbs/<id>.jpg — make UI-relative
        return ".." + thumb if thumb.startswith("/") else "../" + thumb
    if post.get("platform") == "youtube" and post.get("video_id"):
        return f"https://img.youtube.com/vi/{post['video_id']}/mqdefault.jpg"
    return ""


def collect_categories_from_index() -> list[str]:
    text = INDEX.read_text(encoding="utf-8")
    cats = [m.group(1) for m in FILTER_BTN_RE.finditer(text)]
    return [c for c in cats if c != "all"]


def main() -> None:
    items: list[dict] = []
    skipped = 0
    for path in sorted(POSTS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_front_matter(text)
        if not fm:
            skipped += 1
            continue
        date_match = DATE_PREFIX_RE.match(path.name)
        item = {
            "filename": path.name,
            "date": date_match.group(1) if date_match else "",
            "title": fm.get("title", ""),
            "author": fm.get("author", ""),
            "handle": fm.get("handle", ""),
            "category": fm.get("category") or [],
            "platform": fm.get("platform", ""),
            "video_id": fm.get("video_id", ""),
            "thumbnail": fm.get("thumbnail", ""),
            "description": fm.get("description", ""),
            "auto_generated": bool(fm.get("auto_generated", False)),
        }
        item["thumb_url"] = thumb_url(item)
        items.append(item)

    items.sort(key=lambda x: (x["date"], x["filename"]), reverse=True)

    canonical = collect_categories_from_index()
    in_use: set[str] = set()
    for it in items:
        in_use.update(it["category"])
    extras = sorted(in_use - set(canonical))

    out = {
        "categories": canonical,
        "extra_categories": extras,
        "items": items,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(ROOT)}: {len(items)} posts, "
        f"{len(out['categories'])} categories, {skipped} skipped"
    )


if __name__ == "__main__":
    main()
