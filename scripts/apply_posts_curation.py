"""Apply edits/deletes from the post curator UI to _posts/ files.

Reads a JSON file (default: scripts/curate/posts_curation.json) exported by
scripts/curate/posts.html. Each entry is keyed by post filename and may set:

    {
        "<filename.md>": {
            "status": "edit" | "delete",
            "fields": {
                "title":        "...",
                "author":       "...",
                "handle":       "...",
                "description":  "...",
                "category":     ["a", "b"]
            }
        }
    }

- status="delete" -> move file to _drafts/ (creates dir if needed).
- status="edit"   -> rewrite only the listed front-matter scalars in place,
                     preserving body, ordering of unrelated keys, and any
                     keys we don't recognise.

Use --dry-run to preview without touching disk.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
DRAFTS = ROOT / "_drafts"
DEFAULT_INPUT = ROOT / "scripts" / "curate" / "posts_curation.json"

EDITABLE = ("title", "author", "handle", "description", "category")
FRONT_MATTER_RE = re.compile(r"^(---\s*\n)(.*?)(\n---\s*\n?)", re.DOTALL)


def yaml_quote(value: str) -> str:
    """Double-quoted YAML scalar, JSON-escape style (matches generator)."""
    return json.dumps(value, ensure_ascii=False)


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(yaml_quote(v) for v in values) + "]"


def render_value(key: str, value) -> str:
    if key == "category":
        if not isinstance(value, list):
            value = [str(value)]
        return yaml_list([str(v) for v in value])
    return yaml_quote("" if value is None else str(value))


def update_front_matter(text: str, fields: dict) -> str:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        raise ValueError("no front matter")
    head, body_fm, tail = m.group(1), m.group(2), m.group(3)
    rest = text[m.end():]
    lines = body_fm.split("\n")
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        km = re.match(r"^([A-Za-z_]\w*)\s*:\s*(.*)$", line)
        if km and km.group(1) in fields:
            key = km.group(1)
            new_lines.append(f"{key}: {render_value(key, fields[key])}")
            seen.add(key)
        else:
            new_lines.append(line)
    # Append any new fields that weren't already present
    for key, value in fields.items():
        if key in seen or key not in EDITABLE:
            continue
        new_lines.append(f"{key}: {render_value(key, value)}")
    return head + "\n".join(new_lines) + tail + rest


def apply(curation_path: Path, dry_run: bool) -> None:
    data = json.loads(curation_path.read_text(encoding="utf-8"))
    edits = data.get("edits") if isinstance(data, dict) and "edits" in data else data
    if not isinstance(edits, dict):
        raise SystemExit("Curation JSON must be an object keyed by filename.")

    n_edit = n_delete = n_skip = 0
    for filename, entry in sorted(edits.items()):
        src = POSTS / filename
        if not src.exists():
            print(f"  ! missing: {filename}")
            n_skip += 1
            continue
        status = (entry or {}).get("status", "edit")
        if status == "delete":
            dest = DRAFTS / filename
            print(f"  D {filename} -> _drafts/")
            if not dry_run:
                DRAFTS.mkdir(exist_ok=True)
                shutil.move(str(src), str(dest))
            n_delete += 1
            continue
        fields = (entry or {}).get("fields") or {}
        fields = {k: v for k, v in fields.items() if k in EDITABLE}
        if not fields:
            n_skip += 1
            continue
        original = src.read_text(encoding="utf-8")
        try:
            updated = update_front_matter(original, fields)
        except ValueError as exc:
            print(f"  ! {filename}: {exc}")
            n_skip += 1
            continue
        if updated == original:
            n_skip += 1
            continue
        print(f"  E {filename}  ({', '.join(sorted(fields))})")
        if not dry_run:
            src.write_text(updated, encoding="utf-8")
        n_edit += 1

    suffix = " (dry run)" if dry_run else ""
    print(f"\nedited={n_edit} deleted={n_delete} skipped={n_skip}{suffix}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--dry-run", "-n", action="store_true")
    args = ap.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Curation file not found: {args.input}")
    apply(args.input, args.dry_run)


if __name__ == "__main__":
    main()
