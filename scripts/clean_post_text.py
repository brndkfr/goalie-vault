"""One-off cleanup: strip emojis, #hashtags and @handles from post title +
description front matter fields. Collapses trailing whitespace and dangling
punctuation that the strips leave behind. Body content is untouched.

Usage:
    python scripts/clean_post_text.py --dry-run        # prints summary + samples
    python scripts/clean_post_text.py --apply          # rewrites posts in place
    python scripts/clean_post_text.py --apply --only _posts/foo.md
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# Make stdout safe for emoji/Unicode on Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"

# Tokens to remove
HASHTAG_RE = re.compile(r"#[\w\u00C0-\u024F._-]+", re.UNICODE)
HANDLE_RE = re.compile(r"@[\w._-]+")

# Emoji / pictograph ranges we strip. Avoid removing letters with combining
# marks (e.g. ä, é) - only block-level pictographs.
EMOJI_RANGES = [
    (0x1F300, 0x1F6FF),  # symbols & pictographs, transport
    (0x1F700, 0x1F77F),  # alchemical
    (0x1F780, 0x1F7FF),  # geometric extended
    (0x1F800, 0x1F8FF),  # supplemental arrows-C
    (0x1F900, 0x1F9FF),  # supplemental symbols & pictographs (faces, gestures)
    (0x1FA00, 0x1FA6F),  # chess, etc.
    (0x1FA70, 0x1FAFF),  # symbols & pictographs extended-A
    (0x2600, 0x26FF),    # miscellaneous symbols (sun, snow, sport)
    (0x2700, 0x27BF),    # dingbats
    (0x2B00, 0x2BFF),    # arrows + misc
    (0x1F000, 0x1F02F),  # mahjong
    (0x1F0A0, 0x1F0FF),  # playing cards
    (0x1F100, 0x1F1FF),  # enclosed alphanumeric supplement (incl. flags A-Z)
    (0x1F200, 0x1F2FF),  # enclosed ideographic supplement
]
EMOJI_MODIFIERS = {
    0x200D,   # ZWJ
    0xFE0F,   # variation selector-16 (emoji style)
    0xFE0E,   # variation selector-15 (text style)
}
SKIN_TONE_RANGE = (0x1F3FB, 0x1F3FF)


def is_emoji_codepoint(cp: int) -> bool:
    if cp in EMOJI_MODIFIERS:
        return True
    if SKIN_TONE_RANGE[0] <= cp <= SKIN_TONE_RANGE[1]:
        return True
    for lo, hi in EMOJI_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def strip_emoji(text: str) -> str:
    return "".join(ch for ch in text if not is_emoji_codepoint(ord(ch)))


# Collapse whitespace runs but preserve newlines.
LINE_TRAIL_WS_RE = re.compile(r"[ \t]+(?=\n)")
MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
LEADING_PUNCT_RE = re.compile(r"^[\s\-\u2022\u2014\u2013:;,.|/\\!?]+")
TRAILING_PUNCT_RE = re.compile(r"[\s\-\u2022\u2014\u2013:;,|/\\]+$")


def clean_text(text: str) -> str:
    if not text:
        return text
    # Order matters: strip tokens, then emoji, then whitespace cleanup.
    text = HASHTAG_RE.sub("", text)
    text = HANDLE_RE.sub("", text)
    text = strip_emoji(text)
    # Collapse artifacts left by removed tokens, e.g.
    #   "demonstrating in  ,"  -> "demonstrating in,"  (then drop dangling)
    #   "by  for"              -> "by for"
    #   "()"                   -> ""
    #   "( ,"                  -> "("
    text = re.sub(r"\(\s*\)", "", text)            # empty parens
    text = re.sub(r"\(\s*,\s*", "(", text)         # "( ," -> "("
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)   # space before punctuation
    text = re.sub(r"([,;:])(?=[,.;:!?])", "", text)  # duplicated punct
    # Drop dangling connector words left at line ends after removals:
    # "Video by", "Danke", "und", "and", "with", "feat.", etc.
    text = re.sub(
        r"\b(by|with|feat\.?|featuring|von|mit|und|and|für|for|in)\s*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    # Per-line cleanup: trim trailing whitespace and collapse internal runs.
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = MULTI_SPACE_RE.sub(" ", line)
        line = LINE_TRAIL_WS_RE.sub("", line)
        line = line.rstrip()
        line_stripped = line.strip()
        if not line_stripped or not re.search(r"[A-Za-z\u00C0-\u024F0-9]", line_stripped):
            cleaned_lines.append("")
            continue
        line_stripped = LEADING_PUNCT_RE.sub("", line_stripped)
        line_stripped = TRAILING_PUNCT_RE.sub("", line_stripped)
        cleaned_lines.append(line_stripped)
    text = "\n".join(cleaned_lines)
    text = MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
QUOTED_VALUE_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"$')


def split_frontmatter(text: str) -> tuple[str, str, str]:
    """Return (raw_block_with_newlines, body, full_match_or_'')."""
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return "", text, ""
    return m.group(1), text[m.end():], m.group(0)


def yaml_decode(value: str) -> str:
    """Decode a JSON-style double-quoted scalar (matches yaml_str in
    generate_posts.py). Falls back to raw value if not quoted."""
    value = value.strip()
    m = QUOTED_VALUE_RE.match(value)
    if not m:
        return value
    raw = m.group(1)
    # Use json to handle escapes consistently.
    import json
    return json.loads(f'"{raw}"')


def yaml_encode(value: str) -> str:
    import json
    return json.dumps(value, ensure_ascii=False)


def replace_field(block: str, field: str, new_value: str) -> str:
    pattern = re.compile(rf"^({re.escape(field)}:\s*).*$", re.MULTILINE)
    return pattern.sub(lambda m: m.group(1) + yaml_encode(new_value), block, count=1)


def get_field(block: str, field: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.*)$", re.MULTILINE)
    m = pattern.search(block)
    if not m:
        return None
    return yaml_decode(m.group(1))


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def process_file(path: Path, apply: bool) -> tuple[bool, dict[str, tuple[str, str]]]:
    """Return (changed?, {field: (old, new)})."""
    text = path.read_text(encoding="utf-8")
    block, body, full = split_frontmatter(text)
    if not full:
        return False, {}

    diffs: dict[str, tuple[str, str]] = {}
    new_block = block
    for field in ("title", "description"):
        old = get_field(new_block, field)
        if old is None:
            continue
        new = clean_text(old)
        if new != old:
            new_block = replace_field(new_block, field, new)
            diffs[field] = (old, new)

    if not diffs:
        return False, {}

    if apply:
        new_text = f"---\n{new_block}\n---\n{body}"
        path.write_text(new_text, encoding="utf-8")
    return True, diffs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--only", help="Limit to a single post path.")
    parser.add_argument("--samples", type=int, default=10,
                        help="How many before/after samples to print.")
    args = parser.parse_args()

    if args.dry_run == args.apply:
        sys.exit("Pick exactly one of --dry-run or --apply.")

    if args.only:
        files = [ROOT / args.only]
    else:
        files = sorted(POSTS.glob("*.md"))

    changed = 0
    samples_printed = 0
    for path in files:
        did_change, diffs = process_file(path, apply=args.apply)
        if did_change:
            changed += 1
            if samples_printed < args.samples:
                samples_printed += 1
                print(f"\n=== {path.relative_to(ROOT)} ===")
                for field, (old, new) in diffs.items():
                    print(f"  {field}:")
                    print(f"    -  {old!r}")
                    print(f"    +  {new!r}")

    mode = "would update" if args.dry_run else "updated"
    print(f"\n{mode} {changed} of {len(files)} post(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
