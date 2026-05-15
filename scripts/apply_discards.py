"""Remove all resources for posts marked status='discard' in scripts/curate/curation.json.

Actions per discarded id:
  - delete `scripts/curate/thumbs/<id>*` (any extension, plus carousel siblings <id>_N.*)
  - delete `scripts/curate/instagram/<id>.json`
  - strip `<a href=".../p/<id>/" ...>...</a>` anchors (with optional surrounding whitespace) from `scripts/curate/instagram_links.md`
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURATION = ROOT / "scripts" / "curate" / "curation.json"
THUMBS = ROOT / "scripts" / "curate" / "thumbs"
META = ROOT / "scripts" / "curate" / "instagram"
DOC = ROOT / "scripts" / "curate" / "instagram_links.md"


def main() -> None:
    data = json.loads(CURATION.read_text(encoding="utf-8"))
    discard_ids = sorted(i for i, v in data.items() if v.get("status") == "discard")
    print(f"discarded ids: {len(discard_ids)}")

    # 1) delete thumbnails (id and id_N siblings)
    removed_thumbs = 0
    for pid in discard_ids:
        for p in THUMBS.glob(f"{pid}.*"):
            p.unlink(missing_ok=True)
            removed_thumbs += 1
        for p in THUMBS.glob(f"{pid}_*.*"):
            p.unlink(missing_ok=True)
            removed_thumbs += 1

    # 2) delete metadata files
    removed_meta = 0
    for pid in discard_ids:
        f = META / f"{pid}.json"
        if f.exists():
            f.unlink()
            removed_meta += 1

    # 3) strip anchors from the gallery markdown
    text = DOC.read_text(encoding="utf-8")
    removed_anchors = 0
    for pid in discard_ids:
        # anchor regex: <a ... href=".../p/<id>/...">...</a> with optional preceding whitespace
        pattern = re.compile(
            r"\s*<a\s[^>]*href=\"https://www\.instagram\.com/p/"
            + re.escape(pid)
            + r"/[^\"]*\"[^>]*>.*?</a>",
            re.DOTALL,
        )
        new_text, n = pattern.subn("", text)
        if n:
            removed_anchors += n
            text = new_text
    DOC.write_text(text, encoding="utf-8")

    print(f"thumbs removed: {removed_thumbs}")
    print(f"metadata removed: {removed_meta}")
    print(f"anchors removed: {removed_anchors}")

    # 4) prune curation.json itself
    kept = {k: v for k, v in data.items() if v.get("status") != "discard"}
    CURATION.write_text(
        json.dumps(kept, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(f"curation.json: kept {len(kept)} of {len(data)} entries")


if __name__ == "__main__":
    main()
