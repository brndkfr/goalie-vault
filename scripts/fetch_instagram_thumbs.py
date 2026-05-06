"""Fetch Instagram thumbnails + metadata for links in scripts/curate/instagram_links.md.

For each unique Instagram post ID found in the doc:
  * Download the thumbnail to assets/images/thumbs/<id>.<ext>
  * Save metadata JSON to scripts/curate/instagram/<id>.json

Both files act as resume state: an ID is skipped if its JSON already exists.
The markdown is then rewritten so each link group is replaced by an inline
<img> gallery block bracketed by HTML markers (idempotent).

Usage:
    yt-dlp must be on PATH.
    python scripts/fetch_instagram_thumbs.py
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "scripts" / "curate" / "instagram_links.md"
THUMB_DIR = ROOT / "assets" / "images" / "thumbs"
META_DIR = ROOT / "scripts" / "curate" / "instagram"
THUMB_REL = "/assets/images/thumbs"

LINK_RE = re.compile(r"^https://www\.instagram\.com/p/([A-Za-z0-9_-]+)/?\s*$")

GALLERY_OPEN = "<!-- ig-gallery:start -->"
GALLERY_CLOSE = "<!-- ig-gallery:end -->"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
# Instagram only emits og: meta tags for known link-preview bots.
BOT_UA = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"

OG_RE = re.compile(
    r'<meta[^>]+property=["\']og:([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)

# Subset of yt-dlp metadata fields we keep.
KEEP_FIELDS = (
    "id",
    "title",
    "description",
    "uploader",
    "uploader_id",
    "uploader_url",
    "channel",
    "upload_date",
    "timestamp",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
    "thumbnail",
    "webpage_url",
    "extractor",
)


def existing_thumb(video_id: str) -> Path | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = THUMB_DIR / f"{video_id}.{ext}"
        if p.exists():
            return p
    return None


def meta_path(video_id: str) -> Path:
    return META_DIR / f"{video_id}.json"


def save_meta(video_id: str, data: dict) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    meta_path(video_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def ytdlp_fetch(video_id: str) -> tuple[Path | None, dict | None]:
    """Run yt-dlp once to grab both thumbnail and metadata JSON."""
    url = f"https://www.instagram.com/p/{video_id}/"
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--write-thumbnail",
        "--skip-download",
        "--no-warnings",
        "--dump-json",
        "-o",
        str(THUMB_DIR / "%(id)s.%(ext)s"),
        url,
    ]
    try:
        proc = subprocess.run(
            cmd, check=True, timeout=60, capture_output=True, text=True
        )
    except subprocess.TimeoutExpired:
        print("  ! yt-dlp timeout", file=sys.stderr)
        return None, None
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip().splitlines()[-1] if exc.stderr else str(exc)
        print(f"  ! yt-dlp failed: {err}", file=sys.stderr)
        return None, None
    info = None
    try:
        info = json.loads(proc.stdout.splitlines()[0])
    except (ValueError, IndexError):
        pass
    meta = {k: info.get(k) for k in KEEP_FIELDS} if info else None
    return existing_thumb(video_id), meta


def og_fetch(video_id: str) -> tuple[Path | None, dict | None]:
    """Fallback: scrape og:* tags using the facebook bot UA, save image."""
    url = f"https://www.instagram.com/p/{video_id}/"
    req = urllib.request.Request(url, headers={"User-Agent": BOT_UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"  ! og fetch failed: {exc}", file=sys.stderr)
        return None, None

    og: dict[str, str] = {}
    for prop, content in OG_RE.findall(html):
        og.setdefault(prop.lower(), content.replace("&amp;", "&"))

    img_url = og.get("image")
    if not img_url:
        print("  ! no og:image tag", file=sys.stderr)
        return None, None

    ext = "jpg"
    for cand in (".jpg", ".jpeg", ".png", ".webp"):
        if cand in img_url.lower():
            ext = cand.lstrip(".")
            break
    target: Path | None = THUMB_DIR / f"{video_id}.{ext}"
    try:
        img_req = urllib.request.Request(img_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(img_req, timeout=60) as resp:
            target.write_bytes(resp.read())
    except Exception as exc:  # noqa: BLE001
        print(f"  ! image download failed: {exc}", file=sys.stderr)
        target = None

    meta = {
        "id": video_id,
        "title": og.get("title"),
        "description": og.get("description"),
        "thumbnail": img_url,
        "webpage_url": url,
        "extractor": "og-fallback",
    }
    print("  + via og fallback")
    return target, meta


def collect_ids(text: str) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = LINK_RE.match(line.strip())
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            ids.append(m.group(1))
    return ids


def fetch_all(ids: list[str]) -> dict[str, Path | None]:
    thumbs: dict[str, Path | None] = {}
    for i, vid in enumerate(ids, 1):
        thumb = existing_thumb(vid)
        meta_exists = meta_path(vid).exists()
        if thumb and meta_exists:
            print(f"[{i}/{len(ids)}] {vid} (cached)")
            thumbs[vid] = thumb
            continue
        print(f"[{i}/{len(ids)}] {vid} fetching...")
        thumb, meta = ytdlp_fetch(vid)
        if not thumb or not meta:
            t2, m2 = og_fetch(vid)
            thumb = thumb or t2
            meta = meta or m2
        if meta:
            save_meta(vid, meta)
        thumbs[vid] = thumb
        time.sleep(random.uniform(2.0, 6.0))
    return thumbs


def rewrite_markdown(text: str, thumbs: dict[str, Path | None]) -> str:
    text = re.sub(
        re.escape(GALLERY_OPEN) + r".*?" + re.escape(GALLERY_CLOSE) + r"\n?",
        "",
        text,
        flags=re.DOTALL,
    )

    out_lines: list[str] = []
    group: list[str] = []

    def flush() -> None:
        if not group:
            return
        cards = []
        for vid in group:
            thumb = thumbs.get(vid)
            url = f"https://www.instagram.com/p/{vid}/"
            if thumb and thumb.exists():
                src = f"..{THUMB_REL}/{thumb.name}"
                cards.append(
                    f'<a href="{url}" target="_blank" rel="noopener">'
                    f'<img src="{src}" alt="{vid}" width="180"></a>'
                )
            else:
                cards.append(f'<a href="{url}" target="_blank" rel="noopener">{vid}</a>')
        out_lines.append(GALLERY_OPEN)
        out_lines.append(" ".join(cards))
        out_lines.append(GALLERY_CLOSE)
        group.clear()

    for line in text.splitlines():
        m = LINK_RE.match(line.strip())
        if m:
            group.append(m.group(1))
        else:
            flush()
            out_lines.append(line)
    flush()
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    ids = collect_ids(text)
    print(f"Found {len(ids)} unique Instagram post IDs.")
    thumbs = fetch_all(ids)
    new_text = rewrite_markdown(text, thumbs)
    DOC.write_text(new_text, encoding="utf-8")
    have_thumb = sum(1 for p in thumbs.values() if p)
    have_meta = sum(1 for v in ids if meta_path(v).exists())
    print(f"Done. thumbs: {have_thumb}/{len(ids)}  meta: {have_meta}/{len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
