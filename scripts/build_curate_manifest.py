"""Build the manifest consumed by scripts/curate/index.html.

Pairs each metadata JSON in scripts/curate/instagram/ with the matching thumbnail file
under scripts/curate/thumbs/ (extension-agnostic). Also extracts the section
headings from scripts/curate/instagram_links.md so the UI's category dropdown stays
in sync.

Output: scripts/curate/manifest.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "scripts" / "curate" / "instagram"
THUMB_DIR = ROOT / "scripts" / "curate" / "thumbs"
DOC = ROOT / "scripts" / "curate" / "instagram_links.md"
OUT = ROOT / "scripts" / "curate" / "manifest.json"

# Path used in the HTML (relative to scripts/curate/index.html).
THUMB_REL_PREFIX = "thumbs/"

# Fields surfaced to the UI.
KEEP = (
    "id",
    "title",
    "description",
    "uploader",
    "uploader_id",
    "uploader_url",
    "upload_date",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
    "webpage_url",
)


def find_thumb(video_id: str) -> str | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = THUMB_DIR / f"{video_id}.{ext}"
        if p.exists():
            return THUMB_REL_PREFIX + p.name
    return None


def collect_categories() -> list[str]:
    if not DOC.exists():
        return []
    cats: list[str] = []
    seen: set[str] = set()
    skip = {"Snippet", "All Link List", "Already Used in Posts", "Missing - needs review", "Missing — needs review"}
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if not m:
            continue
        name = m.group(1).strip()
        if name in skip or name in seen:
            continue
        seen.add(name)
        cats.append(name)
    return cats


def build() -> dict:
    items: list[dict] = []
    for meta_file in sorted(META_DIR.glob("*.json")):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        # Filename is canonical: yt-dlp sometimes returns the first carousel
        # slide's id inside the JSON, but the file was saved under the parent
        # post id we asked for.
        vid = meta_file.stem
        entry = {k: data.get(k) for k in KEEP}
        entry["id"] = vid
        entry["thumb"] = find_thumb(vid)
        entry["webpage_url"] = f"https://www.instagram.com/p/{vid}/"
        items.append(entry)

    # Include IDs that have a thumbnail but no metadata json (rare, but
    # we want them visible in the curator too).
    # Include IDs that have a thumbnail but no metadata json *only if* they
    # also appear as a top-level link in instagram_links.md. Otherwise they
    # are usually carousel siblings yt-dlp expanded out of a playlist.
    linked_ids: set[str] = set()
    if DOC.exists():
        for m in re.finditer(
            r"instagram\.com/p/([A-Za-z0-9_-]+)/", DOC.read_text(encoding="utf-8")
        ):
            linked_ids.add(m.group(1))

    have = {it["id"] for it in items}
    for thumb in sorted(THUMB_DIR.iterdir()):
        if not thumb.is_file():
            continue
        # Carousel posts produce <id>_1.jpg, <id>_2.jpg, ... - strip only that
        # suffix; leave underscores that are part of the real ID alone.
        m = re.match(r"^(.+?)_\d+$", thumb.stem)
        base = m.group(1) if m else thumb.stem
        if base in have or base not in linked_ids:
            continue
        items.append(
            {
                "id": base,
                "thumb": THUMB_REL_PREFIX + thumb.name,
                "webpage_url": f"https://www.instagram.com/p/{base}/",
            }
        )
        have.add(base)

    return {
        "generated_from": "scripts/build_curate_manifest.py",
        "categories": collect_categories(),
        "items": items,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = build()
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    n = len(manifest["items"])
    with_thumb = sum(1 for it in manifest["items"] if it.get("thumb"))
    print(f"Wrote {OUT.relative_to(ROOT)}: {n} items ({with_thumb} with thumb), "
          f"{len(manifest['categories'])} categories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
