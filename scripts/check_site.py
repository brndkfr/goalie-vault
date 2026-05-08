"""End-to-end integrity check after the taxonomy migration.

Verifies (without running Jekyll):
1. Every registered tag has a categories/<name>.md landing page.
2. Every registered tag has an api/v1/categories/<name>.json endpoint.
3. No orphan files in categories/ or api/v1/categories/ outside the registry.
4. Every post has a known category and only known tags.
5. Every post's category and tags reference an existing landing page (so
   the tag chip links won't 404).
6. The redirect_from setup is intact for renamed tags.
7. _config.yml has the expected permalink + plugin settings.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomy import (  # noqa: E402
    ALL_NAMES, API_CATEGORIES, CATEGORIES, POSTS, REDIRECTS, ROOT, TAGS,
    parse_front_matter, parse_list,
)

results: list[tuple[str, str]] = []  # (status, message)


def ok(msg: str) -> None:
    results.append(("OK", msg))


def fail(msg: str) -> None:
    results.append(("FAIL", msg))


# 1 + 2 + 3: landing pages + API endpoints
for tag in TAGS:
    md = CATEGORIES / f"{tag.name}.md"
    js = API_CATEGORIES / f"{tag.name}.json"
    if md.exists():
        ok(f"category page exists: {tag.name}.md")
    else:
        fail(f"missing category page: {tag.name}.md")
    if js.exists():
        ok(f"API endpoint exists: {tag.name}.json")
    else:
        fail(f"missing API endpoint: {tag.name}.json")

orphan_md = [p.name for p in CATEGORIES.glob("*.md") if p.stem not in ALL_NAMES]
if orphan_md:
    fail(f"orphan category pages: {orphan_md}")
else:
    ok("no orphan category pages")

orphan_js = [
    p.name for p in API_CATEGORIES.glob("*.json")
    if p.stem != "index" and p.stem not in ALL_NAMES
]
if orphan_js:
    fail(f"orphan API endpoints: {orphan_js}")
else:
    ok("no orphan API endpoints")

# 4 + 5: post tags must be registered AND have landing pages
existing_pages = {p.stem for p in CATEGORIES.glob("*.md")}
post_tag_errors: list[str] = []
total_posts = 0
for p in sorted(POSTS.glob("*.md")):
    total_posts += 1
    text = p.read_text(encoding="utf-8")
    fm, _, _ = parse_front_matter(text)
    cat = fm.get("category", "").strip().strip('"').strip("'")
    tags = parse_list(fm.get("tags", ""))
    if not cat or cat not in ALL_NAMES:
        post_tag_errors.append(f"{p.name}: bad category {cat!r}")
        continue
    if cat not in existing_pages:
        post_tag_errors.append(f"{p.name}: category {cat!r} has no landing page")
    bad = [t for t in tags if t not in ALL_NAMES]
    if bad:
        post_tag_errors.append(f"{p.name}: unknown tags {bad}")
    missing = [t for t in tags if t not in existing_pages]
    if missing:
        post_tag_errors.append(f"{p.name}: tags missing landing page {missing}")
if post_tag_errors:
    for e in post_tag_errors[:10]:
        fail(e)
    if len(post_tag_errors) > 10:
        fail(f"... and {len(post_tag_errors) - 10} more post errors")
else:
    ok(f"all {total_posts} posts have registered category + tags with landing pages")

# 6: redirects
for tag_name, paths in REDIRECTS.items():
    md = CATEGORIES / f"{tag_name}.md"
    body = md.read_text(encoding="utf-8") if md.exists() else ""
    for path in paths:
        if f"- {path}" in body:
            ok(f"redirect_from on {tag_name}.md includes {path}")
        else:
            fail(f"redirect_from on {tag_name}.md missing {path}")

# 7: _config.yml
config = (ROOT / "_config.yml").read_text(encoding="utf-8")
if re.search(r"^permalink:\s*/:year/:month/:day/:title/", config, re.MULTILINE):
    ok("_config.yml: permalink locked")
else:
    fail("_config.yml: permalink not locked to /:year/:month/:day/:title/")
if "jekyll-redirect-from" in config:
    ok("_config.yml: jekyll-redirect-from plugin enabled")
else:
    fail("_config.yml: jekyll-redirect-from plugin missing")

# Extra: Liquid syntax sniff in updated layouts
for path in [
    ROOT / "_layouts" / "category.html",
    ROOT / "_layouts" / "post.html",
    ROOT / "index.md",
]:
    body = path.read_text(encoding="utf-8")
    open_blocks = body.count("{%")
    close_blocks = body.count("%}")
    open_outs = body.count("{{")
    close_outs = body.count("}}")
    if open_blocks == close_blocks and open_outs == close_outs:
        ok(f"liquid braces balanced in {path.relative_to(ROOT)}")
    else:
        fail(
            f"liquid braces unbalanced in {path.relative_to(ROOT)}: "
            f"{{% {open_blocks} vs %}} {close_blocks}, "
            f"{{{{ {open_outs} vs }}}} {close_outs}"
        )

# Summary
fails = [m for s, m in results if s == "FAIL"]
print(f"Checks run: {len(results)}, failures: {len(fails)}")
for s, m in results:
    if s == "FAIL":
        print(f"  FAIL: {m}")
if not fails:
    print("All checks passed.")
sys.exit(0 if not fails else 1)
