"""Auto-suggest categories for Instagram posts based on title + description.

Reads scripts/curate/instagram/*.json, scores each post against keyword sets, and
writes scripts/curate/curation_suggestions.json in the same shape the
curator UI imports: { <id>: { category: "..." } }.

Import that file in the UI (Import button); the existing import flow asks
before overwriting, so re-importing is safe.

Categories must match the ones from scripts/curate/instagram_links.md headings
(case-sensitive) so they appear in the per-card dropdown automatically.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "scripts" / "curate" / "instagram"
OUT = ROOT / "scripts" / "curate" / "curation_suggestions.json"

# Keyword bank. Order matters only for tie-breaking (later category wins).
# Keep keywords lowercase, single words / hashtags. Multi-word phrases are
# matched as substrings.
RULES: dict[str, list[str]] = {
    "Goalie Stretching": [
        "stretch", "stretching", "mobility", "#mobilitymonday",
        "flexibility", "yoga", "frog stretch", "scorpion",
        "hip opener", "hip mobility", "splits",
    ],
    "Goalie Warmup": [
        "warmup", "warm-up", "warm up", "#warmup", "activation",
        "pre-game", "pregame", "ramp up",
    ],
    "Goalie Strength": [
        "strength", "strong", "power", "squad", "squat", "deadlift",
        "lunge", "split squat", "plyometric", "plyo", "medicine ball",
        "medball", "core", "abs", "abdomen", "rubber band",
        "rubberband", "resistance band", "leg day", "kettlebell",
        "weight", "barbell", "dumbbell", "explosive",
    ],
    "Goalie Coordination": [
        "coordination", "reaction", "reactive", "hand-eye", "hand eye",
        "balance", "fitness ball", "swiss ball", "stability ball",
        "agility", "footwork", "ladder", "swedish ladder", "cones",
        "cone", "drill", "eye motion", "vision",
    ],
    # Generic goalie training - catch-all for clearly goalie-specific
    # content that does not match a more specific bucket.
    "Goalie Traning": [
        "goalie", "goal keeper", "goalkeeper", "save", "shot", "shooting",
        "blocker", "catch", "catching", "rebound", "between the posts",
        "in goal",
    ],
    # Field/floorball training (non-goalie focused).
    "floorball training": [
        "floorball", "unihockey", "innebandy", "salibandy",
        "passing", "stick handling", "stickhandling", "shooting drill",
        "team training", "game situation",
    ],
}

# Decoded meta dict -> blob of text we search.
def text_for(d: dict) -> str:
    parts = [
        d.get("title") or "",
        d.get("description") or "",
        d.get("uploader") or "",
        d.get("uploader_id") or "",
    ]
    return " ".join(parts).lower()


def classify(text: str) -> tuple[str | None, dict[str, int]]:
    scores: dict[str, int] = {}
    for cat, kws in RULES.items():
        s = 0
        for kw in kws:
            # Whole-word match for short keywords, substring for the rest.
            if len(kw) <= 4 and not kw.startswith("#") and " " not in kw:
                s += len(re.findall(rf"\b{re.escape(kw)}\b", text))
            else:
                s += text.count(kw)
        if s:
            scores[cat] = s
    if not scores:
        return None, {}
    # Prefer the most specific (highest-scoring) category. Ties broken by
    # the order in RULES (earlier = more specific).
    order = list(RULES.keys())
    best = max(scores.items(), key=lambda kv: (kv[1], -order.index(kv[0])))
    return best[0], scores


def main() -> int:
    suggestions: dict[str, dict] = {}
    counts: Counter[str] = Counter()
    no_match: list[str] = []
    for p in sorted(META_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        cat, _scores = classify(text_for(data))
        if cat:
            suggestions[p.stem] = {"category": cat}
            counts[cat] += 1
        else:
            no_match.append(p.stem)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(suggestions, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(suggestions)} suggestions")
    for cat, n in counts.most_common():
        print(f"  {n:4d}  {cat}")
    print(f"  {len(no_match):4d}  (no match)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
