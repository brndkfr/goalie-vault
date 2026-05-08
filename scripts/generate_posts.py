"""Generate Jekyll _posts/*.md files for kept+categorized Instagram posts.

Reads decisions from `scripts/curate/curation.json`, metadata from
`scripts/curate/instagram/`,
thumbnails from `assets/images/thumbs/`, and writes one post per id whose
status is `keep` and whose category maps to known tags.

Idempotent: skips ids that already appear as `video_id:` in any existing post.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date as Date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATION = ROOT / "scripts" / "curate" / "curation.json"
META = ROOT / "scripts" / "curate" / "instagram"
THUMBS = ROOT / "assets" / "images" / "thumbs"
POSTS = ROOT / "_posts"

CATEGORY_MAP: dict[str, tuple[str, list[str]]] = {
    # curator bucket -> (primary skill category, extra tags)
    "Goalie Traning":      ("technique",    []),
    "Goalie Coordination": ("coordination", []),
    "Goalie Strength":     ("strength",     []),
    "Goalie Stretching":   ("stretching",   []),
    "Goalie Warmup":       ("warmup",       []),
    "floorball training":  ("technique",    []),
}

# Display name used when synthesising a fallback title.
CATEGORY_DISPLAY: dict[str, str] = {
    "Goalie Traning": "Goalie training",
    "Goalie Coordination": "Goalie coordination",
    "Goalie Strength": "Goalie strength",
    "Goalie Stretching": "Goalie stretching",
    "Goalie Warmup": "Goalie warmup",
    "floorball training": "Floorball training",
}

GENERIC_TITLE_PREFIX_RE = re.compile(
    r"^(video|reel|photo|post|carousel)\s+by\s+", re.IGNORECASE
)
# yt-dlp uses these as titles for carousel slides (e.g. "Video 1", "Photo 2").
GENERIC_SLIDE_RE = re.compile(
    r"^(video|reel|photo|post|carousel|slide)\s+\d+\s*$", re.IGNORECASE
)
HASHTAG_TOKEN_RE = re.compile(r"[#@][\w._-]+")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
LETTER_RE = re.compile(r"[A-Za-zÀ-ÿ]")
SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")
SKIP_LINE_RE = re.compile(
    r"^(dm\b|link in bio|follow\b|comment\b|tag\b|share\b|click\b)",
    re.IGNORECASE,
)
TITLE_MAX = 70


def strip_tokens(text: str) -> str:
    """Drop hashtags, @mentions and URLs; collapse whitespace; trim punctuation."""
    text = HASHTAG_TOKEN_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # strip leading/trailing decorative punctuation but keep inner punctuation
    text = re.sub(r"^[\s\-\*\u2022\u2014\u2013:;,.|/\\]+", "", text)
    text = re.sub(r"[\s\-\*\u2022\u2014\u2013:;,.|/\\]+$", "", text)
    return text


def has_letters(text: str, minimum: int = 3) -> bool:
    return len(LETTER_RE.findall(text)) >= minimum


def cap_title(text: str) -> str:
    text = text.strip()
    if len(text) <= TITLE_MAX:
        return text
    cut = text[:TITLE_MAX]
    # break on last whitespace if any, else hard cut
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:-")


def first_sentence(text: str) -> str:
    parts = SENTENCE_END_RE.split(text, maxsplit=1)
    return parts[0].strip()


def cap_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _looks_like_handle(text: str, meta: dict) -> bool:
    """yt-dlp often sets `title` to just the channel handle. Detect that."""
    norm = text.strip().lower().lstrip("@")
    if not norm:
        return False
    handle = (meta.get("channel") or "").strip().lower()
    uploader_id = str(meta.get("uploader_id") or "").strip().lower()
    if norm == handle or norm == uploader_id:
        return True
    # No spaces and matches a typical handle pattern (letters/digits/._)
    if " " not in norm and re.fullmatch(r"[a-z0-9._-]{2,}", norm):
        return True
    return False


def derive_title(meta: dict, curator_category: str) -> str:
    raw_title = (meta.get("title") or "").strip()

    # Tier 1: clean the JSON title (skip if it's just the uploader handle
    # or a "Video N" / "Photo N" carousel slide label)
    candidate = GENERIC_TITLE_PREFIX_RE.sub("", raw_title)
    candidate = strip_tokens(candidate)
    if (
        has_letters(candidate)
        and not _looks_like_handle(candidate, meta)
        and not GENERIC_SLIDE_RE.match(candidate)
    ):
        return cap_first(cap_title(first_sentence(candidate)))

    # Tier 2: scan description lines
    desc = (meta.get("description") or "").strip()
    for line in desc.splitlines():
        line = strip_tokens(line)
        if not line or SKIP_LINE_RE.match(line):
            continue
        if not has_letters(line):
            continue
        return cap_first(cap_title(first_sentence(line)))

    # Tier 3: synthesised fallback
    cat_display = CATEGORY_DISPLAY.get(curator_category, curator_category)
    uploader = (meta.get("uploader") or meta.get("channel") or "").strip()
    if uploader:
        return cap_title(f"{cat_display} by {uploader}")
    return cap_title(f"{cat_display} drill")


def clean_description(desc: str) -> str:
    if not desc:
        return ""
    lines = desc.splitlines()
    # Drop trailing block of hashtag-only / empty lines
    while lines:
        last = lines[-1].strip()
        stripped = strip_tokens(last)
        if not last or not has_letters(stripped, minimum=2):
            lines.pop()
            continue
        break
    return "\n".join(lines).strip()


def date_from_meta(meta: dict) -> str:
    raw = (meta.get("upload_date") or "").strip()
    if re.fullmatch(r"\d{8}", raw):
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return Date.today().isoformat()


def find_thumbnail(pid: str) -> str:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = THUMBS / f"{pid}.{ext}"
        if p.exists():
            return f"/assets/images/thumbs/{p.name}"
    return "skip"


def collect_used_video_ids() -> set[str]:
    used: set[str] = set()
    pat = re.compile(r'^video_id:\s*"?([^"\s]+)"?', re.MULTILINE)
    for f in POSTS.glob("*.md"):
        for m in pat.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            used.add(m.group(1).strip())
    return used


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "untitled"


def yaml_str(s: str) -> str:
    """JSON string == valid YAML double-quoted scalar; safe for any content."""
    return json.dumps(s, ensure_ascii=False)


def render_post(meta: dict, pid: str, title: str, tags: list[str], thumb: str) -> str:
    description = clean_description(meta.get("description") or "")
    author = (meta.get("uploader") or meta.get("channel") or "").strip()
    handle = (meta.get("channel") or meta.get("uploader_id") or "").strip()
def render_post(meta: dict, pid: str, title: str, primary: str, tags: list[str], thumb: str) -> str:
    description = clean_description(meta.get("description") or "")
    author = (meta.get("uploader") or meta.get("channel") or "").strip()
    handle = (meta.get("channel") or meta.get("uploader_id") or "").strip()
    lines = [
        "---",
        "layout: post",
        f"title: {yaml_str(title)}",
        f"author: {yaml_str(author)}",
        f"handle: {yaml_str(handle)}",
        f"category: {primary}",
        "tags: [" + ", ".join(tags) + "]",
        'platform: "instagram"',
        f"video_id: {yaml_str(pid)}",
        f"thumbnail: {yaml_str(thumb)}",
        f"description: {yaml_str(description)}",
        "auto_generated: true",
        "---",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    curation = json.loads(CURATION.read_text(encoding="utf-8"))
    used_ids = collect_used_video_ids()

    candidates = [
        (pid, v["category"])
        for pid, v in curation.items()
        if v.get("status") == "keep"
        and v.get("category")
        and v["category"] in CATEGORY_MAP
    ]
    print(f"keep+categorized candidates: {len(candidates)}")

    skipped_existing = 0
    skipped_no_meta = 0
    written = 0
    used_filenames: set[str] = set()

    for pid, cat in candidates:
        if pid in used_ids:
            skipped_existing += 1
            continue
        meta_path = META / f"{pid}.json"
        if not meta_path.exists():
            skipped_no_meta += 1
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title = derive_title(meta, cat)
        primary, extra_tags = CATEGORY_MAP[cat]
        thumb = find_thumbnail(pid)
        date = date_from_meta(meta)
        fname = f"{date}-{slugify(title)}.md"
        out = POSTS / fname
        if out.exists() or fname in used_filenames:
            fname = f"{date}-{slugify(title)}-{pid}.md"
            out = POSTS / fname
        used_filenames.add(fname)

        out.write_text(render_post(meta, pid, title, primary, extra_tags, thumb), encoding="utf-8")
        written += 1

    print(f"written:            {written}")
    print(f"skipped (existing): {skipped_existing}")
    print(f"skipped (no meta):  {skipped_no_meta}")


if __name__ == "__main__":
    main()
