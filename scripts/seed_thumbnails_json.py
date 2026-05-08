"""One-shot: seed `_data/thumbnails.json` from existing curate metadata.

Reads scripts/curate/instagram/*.json, extracts the `thumbnail` URL, and
writes a single `_data/thumbnails.json` file used by Jekyll layouts.

Each entry has the shape:
    "<video_id>": {
      "url":      "<cdninstagram.com URL or null>",
      "fetched":  "<YYYY-MM-DD or null>",
      "status":   "ok | stale | pending | not_found | rate_limit | error",
      "attempts": <int>
    }

Initial seed marks all entries as "stale" so the refresh script will
pick them up in oldest-first order even though they may currently work.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "scripts" / "curate" / "instagram"
OUT = ROOT / "_data" / "thumbnails.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if OUT.exists():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            existing = {}

    out: dict[str, dict] = dict(existing)
    seeded = 0
    skipped = 0
    for path in sorted(META_DIR.glob("*.json")):
        vid = path.stem
        if vid in out and out[vid].get("url"):
            skipped += 1
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        url = data.get("thumbnail")
        if not url:
            continue
        out[vid] = {
            "url": url,
            "fetched": "2025-01-01",  # deliberately stale -> refresh will pick up
            "status": "stale",
            "attempts": 0,
        }
        seeded += 1

    OUT.write_text(
        json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out)} entries (seeded {seeded}, skipped {skipped}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
