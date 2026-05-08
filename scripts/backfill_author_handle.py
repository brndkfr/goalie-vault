"""Backfill missing author/handle in posts from scripts/curate/instagram/*.json.

For each post that has empty author or handle but a known video_id, look up
the matching curate JSON and write `author` (= uploader) and `handle`
(= channel) into the front matter.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
META_DIR = ROOT / "scripts" / "curate" / "instagram"

VIDEO_RE = re.compile(r'^video_id:\s*["\']?([A-Za-z0-9_-]+)', re.M)
PLATFORM_RE = re.compile(r'^platform:\s*["\']?([a-zA-Z0-9_-]+)', re.M)
AUTHOR_RE = re.compile(r'^author:\s*["\']?(.*?)["\']?\s*$', re.M)
HANDLE_RE = re.compile(r'^handle:\s*["\']?(.*?)["\']?\s*$', re.M)


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def load_meta() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in META_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out[path.stem] = data
    return out


def update_post(path: Path, meta: dict[str, dict], apply: bool) -> str | None:
    """Return a status string describing what would change, or None if nothing."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    head = text[:end]
    body = text[end:]

    plat = PLATFORM_RE.search(head)
    if not plat or plat.group(1).lower() != "instagram":
        return None
    vid_m = VIDEO_RE.search(head)
    if not vid_m:
        return None
    vid = vid_m.group(1)

    author_m = AUTHOR_RE.search(head)
    handle_m = HANDLE_RE.search(head)
    cur_author = (author_m.group(1).strip() if author_m else "") if author_m else ""
    cur_handle = (handle_m.group(1).strip() if handle_m else "") if handle_m else ""

    if cur_author and cur_handle:
        return None  # already populated

    data = meta.get(vid)
    if not data:
        return f"  no curate data for {vid}"

    new_author = cur_author or (data.get("uploader") or "").strip()
    new_handle = cur_handle or (data.get("channel") or data.get("uploader_id") or "").strip()

    if new_author == cur_author and new_handle == cur_handle:
        return f"  no fillable data for {vid}"

    new_head = head
    if author_m and not cur_author and new_author:
        new_head = AUTHOR_RE.sub(f'author: "{yaml_escape(new_author)}"', new_head, count=1)
    elif not author_m and new_author:
        # Insert author right after layout line
        new_head = re.sub(r'(^layout:.*\n)', r'\1author: "' + yaml_escape(new_author) + '"\n', new_head, count=1, flags=re.M)
    if handle_m and not cur_handle and new_handle:
        new_head = HANDLE_RE.sub(f'handle: "{yaml_escape(new_handle)}"', new_head, count=1)
    elif not handle_m and new_handle:
        new_head = re.sub(r'(^layout:.*\n)', r'\1handle: "' + yaml_escape(new_handle) + '"\n', new_head, count=1, flags=re.M)

    if new_head == head:
        return None

    if apply:
        path.write_text(new_head + body, encoding="utf-8")
    return f"  + {path.name}: author={new_author!r} handle={new_handle!r}"


def main() -> int:
    apply = "--apply" in sys.argv
    meta = load_meta()
    print(f"Loaded {len(meta)} curate JSON files.")
    changes = 0
    skips = 0
    for path in sorted(POSTS.glob("*.md")):
        result = update_post(path, meta, apply)
        if result is None:
            continue
        print(result)
        if result.startswith("  +"):
            changes += 1
        else:
            skips += 1
    verb = "Applied" if apply else "Would apply"
    print(f"\n{verb} {changes} change(s); {skips} post(s) had no usable curate data.")
    if not apply:
        print("Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
