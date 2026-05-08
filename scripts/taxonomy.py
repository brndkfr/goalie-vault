"""Single source of truth for the goalie-vault tag taxonomy.

Subcommands:

    python scripts/taxonomy.py materialize-pages
        (Re)create one categories/<name>.md and one
        api/v1/categories/<name>.json per registered tag. Idempotent.

    python scripts/taxonomy.py retag --dry-run [--out retag.csv]
        Classify every _posts/*.md, write a CSV with current vs proposed
        category/tags. Does not touch any post.

    python scripts/taxonomy.py retag --apply retag.csv
        Read the CSV (possibly hand-edited) and rewrite the front matter
        of each listed post: replace `category:` with a single string and
        add/replace `tags:` with the array. All other front-matter keys
        and the post body are left untouched.

The taxonomy is organised in four facets. Each tag belongs to exactly one
facet, but a post can carry tags from any combination of facets.

Facets:
    skill      - the primary thing being trained (one per post -> category:)
    sub-skill  - finer-grained classification within a skill
    context    - when/how the drill is used
    equipment  - the prop that defines the drill (only when prominent)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
CATEGORIES = ROOT / "categories"
API_CATEGORIES = ROOT / "api" / "v1" / "categories"

# ---------------------------------------------------------------------------
# Tag registry
# ---------------------------------------------------------------------------

# Priority order for picking the single primary `category:` when several
# skill tags match. Earlier = higher priority.
SKILL_PRIORITY = [
    "technique",
    "reaction",
    "coordination",
    "strength",
    "movement",
    "mobility",
    "stretching",
    "warmup",
    "theory",
]


@dataclass(frozen=True)
class Tag:
    name: str            # slug, used in URLs and front matter
    facet: str           # skill | sub-skill | context | equipment
    title: str           # human heading on the landing page
    description: str     # subtitle on the landing page


TAGS: list[Tag] = [
    # ---- Facet 1: Skill (primary) -----------------------------------------
    Tag("technique",   "skill",     "Technique",            "Saves, stance, hand position - the goalie craft."),
    Tag("coordination","skill",     "Coordination Drills",  "Drills to improve coordination."),
    Tag("movement",    "skill",     "Movement",             "Locomotion and agility around the crease."),
    Tag("reaction",    "skill",     "Reaction",             "Reflex and response training."),
    Tag("strength",    "skill",     "Strength",             "Power, plyometrics and lifting."),
    Tag("stretching",  "skill",     "Stretching",           "Static stretching for goalies."),
    Tag("mobility",    "skill",     "Mobility",             "Dynamic and end-range mobility work."),
    Tag("warmup",      "skill",     "Warmup",               "Pre-training and pre-match preparation."),
    Tag("theory",      "skill",     "Theory",               "Talking-head explanations and concepts."),

    # ---- Facet 2: Sub-skill ------------------------------------------------
    Tag("hand-eye",       "sub-skill", "Hand-Eye Coordination",  "Catching, ball tracking and reactive hand drills."),
    Tag("juggling",       "sub-skill", "Juggling",               "Juggling drills for hand-eye coordination."),
    Tag("vision",         "sub-skill", "Vision",                 "Eye training, peripheral vision, screened shots."),
    Tag("footwork",       "sub-skill", "Footwork",               "Lateral movement, agility ladder, side-to-side."),
    Tag("positioning",    "sub-skill", "Positioning",            "Stance, angles, basic position."),
    Tag("rebound-control","sub-skill", "Rebound Control",        "Controlling and clearing returns after a save."),
    Tag("mental",         "sub-skill", "Mental",                 "Focus, mindset and visualisation."),

    # ---- Facet 3: Context --------------------------------------------------
    Tag("game-situation", "context",   "Game Situation",         "Match-like drills and scenario play."),
    Tag("match-prep",     "context",   "Match Preparation",      "Pre-game rituals and on-day prep."),
    Tag("injury-recovery","context",   "Injury Recovery",        "Rehab and comeback content."),

    # ---- Facet 4: Equipment ------------------------------------------------
    Tag("medicine-ball",  "equipment", "Medicine Ball",          "Drills with a medicine ball."),
    Tag("tennis-ball",    "equipment", "Tennis Ball",            "Drills with a tennis ball."),
    Tag("band",           "equipment", "Resistance Band",        "Resistance / flexi band drills."),
    Tag("slideboard",     "equipment", "Slideboard",             "Slideboard work for goalies."),
    Tag("fitlight",       "equipment", "Reaction Lights",        "Fitlight or similar reaction-light training."),
    Tag("brock-string",   "equipment", "Brock String",           "Vision training with a Brock string."),
]

TAG_BY_NAME: dict[str, Tag] = {t.name: t for t in TAGS}
ALL_NAMES: set[str] = set(TAG_BY_NAME)
SKILLS: set[str] = {t.name for t in TAGS if t.facet == "skill"}

# Legacy tags that should be remapped (not used in the new vocabulary).
# Mapping is consulted both for `retag` classification and as a guard rail.
LEGACY_REMAP: dict[str, list[str]] = {
    "goal-technical": ["technique"],
    "warm-up":        ["warmup"],
    # "training" and "floorball" do not map to anything specific - they
    # are dropped and replaced with whatever the keyword rules suggest.
    "training":  [],
    "floorball": [],
}

# ---------------------------------------------------------------------------
# Keyword rules (post text -> tag suggestions)
#
# Each entry: tag -> list of (pattern, kind). kind is "word" (whole-word) or
# "sub" (substring). All patterns are matched case-insensitively against
# title + description.
# ---------------------------------------------------------------------------

W = "word"  # whole-word match (uses \b...\b)
S = "sub"   # substring match

KEYWORD_RULES: dict[str, list[tuple[str, str]]] = {
    # ---- Skills -----------------------------------------------------------
    "technique": [
        ("save", W), ("saves", W), ("blocker", W), ("catching", W),
        ("catch", W), ("stance", W), ("between the posts", S),
        ("shot stopping", S), ("goalie skills", S), ("technique", S),
    ],
    "coordination": [
        ("coordination", S), ("hand-eye", S), ("hand eye", S),
        ("balance", W), ("agility", W),
    ],
    "movement": [
        ("movement", S), ("lateral", S), ("shuffle", S),
        ("crease movement", S),
    ],
    "reaction": [
        ("reaction", S), ("reactive", S), ("reflex", S),
        ("fitlight", S), ("reaction light", S),
    ],
    "strength": [
        ("strength", S), ("power", W), ("plyo", S), ("plyometric", S),
        ("squat", S), ("deadlift", S), ("lunge", S), ("kettlebell", S),
        ("barbell", S), ("dumbbell", S), ("explosive", W),
        ("medicine ball", S), ("medball", S), ("core", W), ("abs", W),
    ],
    "stretching": [
        ("stretch", S), ("static stretch", S), ("yoga", W),
    ],
    "mobility": [
        ("mobility", S), ("end-range", S), ("end range", S),
        ("hip opener", S), ("frog stretch", S), ("scorpion", W),
        ("range of motion", S), ("flexibility", S),
    ],
    "warmup": [
        ("warmup", S), ("warm-up", S), ("warm up", S), ("activation", W),
        ("ramp up", S), ("pre-game", S), ("pregame", S),
    ],
    "theory": [
        ("explained", W), ("why ", S), ("here's why", S), ("theory", W),
        ("the basics", S), ("fundamentals", S), ("quick tip", S),
    ],

    # ---- Sub-skills -------------------------------------------------------
    "hand-eye": [
        ("hand-eye", S), ("hand eye", S), ("juggle", S), ("juggling", S),
        ("tennis ball", S), ("tracking", W), ("catch", W), ("catching", W),
    ],
    "juggling": [
        ("juggle", S), ("juggling", S),
    ],
    "vision": [
        ("vision", W), ("peripheral", W), ("brock string", S),
        ("eye motion", S), ("see the ball", S), ("screened shot", S),
    ],
    "footwork": [
        ("footwork", S), ("lateral", S), ("side to side", S),
        ("ladder", W), ("cones", W), ("cone", W), ("shuffle", S),
        ("hop", W), ("hops", W), ("bounds", W), ("bound", W),
    ],
    "positioning": [
        ("position", S), ("stance", W), ("angle", W), ("angles", W),
        ("basic position", S), ("grundposition", S), ("grundstellung", S),
    ],
    "rebound-control": [
        ("rebound", S), ("retur", S), ("clear the ball", S),
        ("rebound control", S),
    ],
    "mental": [
        ("mindset", W), ("focus", W), ("mental", W),
        ("visualisation", S), ("visualization", S), ("breathing", W),
    ],

    # ---- Context ----------------------------------------------------------
    "game-situation": [
        ("game situation", S), ("match-like", S), ("scrimmage", W),
        ("vs goalie", S), ("coach vs", S), ("real game", S),
        ("game speed", S),
    ],
    "match-prep": [
        ("pre-match", S), ("prematch", S), ("pre-game", S), ("pregame", S),
        ("pre game", S), ("pre match", S), ("warmup ritual", S),
        ("pre-game-ritual", S), ("pre game ritual", S),
    ],
    "injury-recovery": [
        ("rehab", W), ("recovery", W), ("comeback", W),
        ("dislocation", S), ("post-surgery", S), ("post surgery", S),
        ("injury", W),
    ],

    # ---- Equipment --------------------------------------------------------
    "medicine-ball": [("medicine ball", S), ("medball", S), ("med ball", S)],
    "tennis-ball":   [("tennis ball", S)],
    "band":          [("resistance band", S), ("rubber band", S), ("flexi band", S),
                      ("flexiband", S), ("rubberband", S)],
    "slideboard":    [("slideboard", S), ("slide board", S)],
    "fitlight":      [("fitlight", S), ("reaction light", S),
                      ("reaction lights", S)],
    "brock-string":  [("brock string", S), ("brockschnur", S),
                      ("brock-schnur", S)],
}

# Sanity check at import time: every keyword rule references a known tag.
for _tag in KEYWORD_RULES:
    if _tag not in TAG_BY_NAME:
        raise AssertionError(f"KEYWORD_RULES references unknown tag {_tag!r}")


# ---------------------------------------------------------------------------
# materialize-pages
# ---------------------------------------------------------------------------

CATEGORY_PAGE_TEMPLATE = """\
---
layout: category
title: "{title}"
description: "{description}"
category_filter: {name}
permalink: /{name}/{redirect_block}
---
"""

API_JSON_TEMPLATE = """\
---
layout: none
permalink: /api/v1/categories/{name}.json
---
{{% assign filtered = site.posts | where_exp: "p", "p.category == '{name}' or p.tags contains '{name}'" %}}[\
{{% for post in filtered %}}\
{{"title":{{{{ post.title | jsonify }}}},\
"author":{{{{ post.author | jsonify }}}},\
"handle":{{{{ post.handle | jsonify }}}},\
"platform":{{{{ post.platform | jsonify }}}},\
"video_id":{{{{ post.video_id | jsonify }}}},\
"category":{{{{ post.category | jsonify }}}},\
"tags":{{{{ post.tags | jsonify }}}},\
"description":{{{{ post.description | jsonify }}}},\
"thumbnail":{{{{ post.thumbnail | jsonify }}}},\
"url":{{{{ site.url | append: site.baseurl | append: post.url | jsonify }}}}\
}}{{% unless forloop.last %}},{{% endunless %}}\
{{% endfor %}}]
"""

# Tags that need redirect_from to preserve old URLs after a rename.
REDIRECTS: dict[str, list[str]] = {
    "technique": ["/goal-technical/"],
}


def _redirect_block(name: str) -> str:
    targets = REDIRECTS.get(name, [])
    if not targets:
        return ""
    items = "\n".join(f"  - {t}" for t in targets)
    return f"\nredirect_from:\n{items}"


def materialize_pages() -> None:
    CATEGORIES.mkdir(exist_ok=True)
    API_CATEGORIES.mkdir(parents=True, exist_ok=True)

    written_md: list[str] = []
    written_json: list[str] = []
    for tag in TAGS:
        md_path = CATEGORIES / f"{tag.name}.md"
        json_path = API_CATEGORIES / f"{tag.name}.json"

        md_content = CATEGORY_PAGE_TEMPLATE.format(
            title=tag.title.replace('"', '\\"'),
            description=tag.description.replace('"', '\\"'),
            name=tag.name,
            redirect_block=_redirect_block(tag.name),
        )
        json_content = API_JSON_TEMPLATE.format(name=tag.name)

        if not md_path.exists() or md_path.read_text(encoding="utf-8") != md_content:
            md_path.write_text(md_content, encoding="utf-8")
            written_md.append(str(md_path.relative_to(ROOT)))
        if not json_path.exists() or json_path.read_text(encoding="utf-8") != json_content:
            json_path.write_text(json_content, encoding="utf-8")
            written_json.append(str(json_path.relative_to(ROOT)))

    # Remove obsolete category files that don't correspond to a known tag.
    obsolete_md: list[str] = []
    obsolete_json: list[str] = []
    for p in CATEGORIES.glob("*.md"):
        if p.stem not in ALL_NAMES:
            p.unlink()
            obsolete_md.append(str(p.relative_to(ROOT)))
    for p in API_CATEGORIES.glob("*.json"):
        if p.stem == "index":
            continue
        if p.stem not in ALL_NAMES:
            p.unlink()
            obsolete_json.append(str(p.relative_to(ROOT)))

    print(f"[materialize-pages] wrote {len(written_md)} category page(s), "
          f"{len(written_json)} API JSON file(s).")
    for f in written_md:
        print(f"  + {f}")
    for f in written_json:
        print(f"  + {f}")
    for f in obsolete_md + obsolete_json:
        print(f"  - {f}")


# ---------------------------------------------------------------------------
# retag
# ---------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
CATEGORY_LINE_RE = re.compile(r"(?m)^category:.*$")
TAGS_LINE_RE = re.compile(r"(?m)^tags:.*$")
LIST_VAL_RE = re.compile(r"\[([^\]]*)\]")


def parse_front_matter(text: str) -> tuple[dict[str, str], str, str]:
    """Return (fm dict, raw fm block, body)."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, "", text
    block = m.group(1)
    body = text[m.end():]
    fm: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm, block, body


def parse_list(value: str) -> list[str]:
    """Parse a YAML inline list or single string into a list."""
    if not value:
        return []
    m = LIST_VAL_RE.search(value)
    if m:
        items = [v.strip().strip('"').strip("'") for v in m.group(1).split(",")]
        return [v for v in items if v]
    # Single bare value
    return [value.strip().strip('"').strip("'")]


def text_for(fm: dict[str, str]) -> str:
    parts = [fm.get("title", ""), fm.get("description", "")]
    return " ".join(parts).lower()


def classify(text: str, current: list[str]) -> tuple[str, list[str]]:
    """Return (primary_category, sorted tags-without-primary)."""
    matched: set[str] = set()

    # Apply legacy remap on whatever tags were already there.
    for c in current:
        if c in LEGACY_REMAP:
            for replacement in LEGACY_REMAP[c]:
                matched.add(replacement)
        elif c in ALL_NAMES:
            matched.add(c)

    text_lower = text.lower()
    for tag, rules in KEYWORD_RULES.items():
        for pat, kind in rules:
            if kind == W:
                if re.search(rf"\b{re.escape(pat)}\b", text_lower):
                    matched.add(tag)
                    break
            else:
                if pat in text_lower:
                    matched.add(tag)
                    break

    # Pick primary skill: highest-priority skill in matched, else first
    # legacy skill, else "technique" as a fallback only when NO skills
    # matched and the post mentions "goalie/goalkeeper".
    skills_in_match = [s for s in SKILL_PRIORITY if s in matched]
    if skills_in_match:
        primary = skills_in_match[0]
    else:
        if any(k in text_lower for k in ("goalie", "goalkeeper", "torwart", "torhuter", "malvakt", "brankar")):
            primary = "technique"
            matched.add(primary)
        else:
            # Truly nothing matched - leave the post's first existing tag,
            # or 'technique' as a last resort.
            primary = current[0] if current and current[0] in ALL_NAMES else "technique"
            matched.add(primary)

    secondary = sorted(t for t in matched if t != primary)
    return primary, secondary


def iter_posts() -> Iterable[Path]:
    return sorted(POSTS.glob("*.md"))


def cmd_retag_dry_run(out_path: Path) -> None:
    out_path = (ROOT / out_path).resolve() if not out_path.is_absolute() else out_path
    rows: list[dict[str, str]] = []
    for post in iter_posts():
        text = post.read_text(encoding="utf-8")
        fm, _block, _body = parse_front_matter(text)
        current = parse_list(fm.get("category", ""))
        primary, tags = classify(text_for(fm), current)
        rows.append({
            "path": str(post.relative_to(ROOT)).replace("\\", "/"),
            "title": fm.get("title", "").strip('"'),
            "current_category": ",".join(current),
            "new_category": primary,
            "new_tags": ",".join(tags),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "title", "current_category", "new_category", "new_tags"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[retag --dry-run] wrote {out_path.relative_to(ROOT)} ({len(rows)} posts).")


def _format_yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    inner = ", ".join(items)
    return f"[{inner}]"


def _rewrite_front_matter(text: str, primary: str, tags: list[str]) -> str:
    fm_match = FRONT_MATTER_RE.match(text)
    if not fm_match:
        # Should not happen for valid Jekyll posts.
        return text
    block = fm_match.group(1)
    body = text[fm_match.end():]

    new_category_line = f"category: {primary}"
    new_tags_line = f"tags: {_format_yaml_list(tags)}"

    if CATEGORY_LINE_RE.search(block):
        block = CATEGORY_LINE_RE.sub(new_category_line, block, count=1)
    else:
        block += "\n" + new_category_line

    if TAGS_LINE_RE.search(block):
        block = TAGS_LINE_RE.sub(new_tags_line, block, count=1)
    else:
        # Insert tags right after the category line for tidy front matter.
        block = re.sub(
            r"(?m)^(category:.*)$",
            r"\1\n" + new_tags_line,
            block,
            count=1,
        )

    return f"---\n{block}\n---\n{body}"


def cmd_retag_apply(csv_path: Path) -> None:
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}")
    changed = 0
    skipped = 0
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            post = ROOT / row["path"]
            if not post.exists():
                print(f"  ! missing: {row['path']}")
                skipped += 1
                continue
            primary = row["new_category"].strip()
            tags = [t.strip() for t in row["new_tags"].split(",") if t.strip()]
            if primary not in ALL_NAMES:
                print(f"  ! unknown primary {primary!r} for {row['path']}")
                skipped += 1
                continue
            unknown = [t for t in tags if t not in ALL_NAMES]
            if unknown:
                print(f"  ! unknown tag(s) {unknown} for {row['path']}")
                skipped += 1
                continue
            text = post.read_text(encoding="utf-8")
            new_text = _rewrite_front_matter(text, primary, tags)
            if new_text != text:
                post.write_text(new_text, encoding="utf-8")
                changed += 1
    print(f"[retag --apply] updated {changed} post(s), skipped {skipped}.")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("materialize-pages", help="(Re)create category landing pages and API JSON files.")

    p_retag = sub.add_parser("retag", help="Re-classify posts.")
    mode = p_retag.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", metavar="CSV", help="Apply the retag described by CSV.")
    p_retag.add_argument("--out", default="retag.csv", help="CSV output path for --dry-run.")

    args = parser.parse_args()

    if args.cmd == "materialize-pages":
        materialize_pages()
        return 0
    if args.cmd == "retag":
        if args.dry_run:
            cmd_retag_dry_run(Path(args.out))
        else:
            cmd_retag_apply(Path(args.apply))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
