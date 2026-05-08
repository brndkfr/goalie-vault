# Goalie Vault 🧤

A curated resource hub for floorball goalies — video drills, training exercises, coordination work, and theory, all in one place.

**Live site:** [brndkfr.github.io/goalie-vault](https://brndkfr.github.io/goalie-vault)

---

## What's Inside

| Category | Description |
|---|---|
| 🏋️ Warmups | Activation and mobility exercises |
| 🎾 Coordination | Ball control and reaction drills |
| 🥅 Training | Goal-technical and position-specific work |
| 📖 Theory & Gear | Articles on tactics, mindset, and equipment |

---

## Contributing a Drill

Drills are added via a GitHub Issue form — no manual file editing needed.

1. Open a [New Drill issue](../../issues/new?template=new-drill.yml)
2. Fill in the title, author, social handle, video link, categories, and coaching notes
3. Submit — a GitHub Actions workflow will automatically create the post and close the issue

> **Supported platforms:** Instagram and YouTube

---

## How It Works

```
Issue submitted
      ↓
GitHub Actions (new-drill.yml)
  → Parses the issue form fields
  → Generates a Jekyll post in _posts/
  → Commits and pushes to main
  → Closes the issue with a confirmation comment
      ↓
GitHub Pages rebuilds the site
```

The workflow uses [zentered/issue-forms-body-parser](https://github.com/zentered/issue-forms-body-parser) to extract structured data from the issue body and `jq` to safely access fields with hyphenated keys.

---

## Adding Content Manually

Copy `_posts/post.template` and fill in the frontmatter:

```yaml
---
layout: post
title: "Your Drill Title"
author: "Author Name"
handle: "social_handle"
category: [warmup, coordination]
platform: "instagram"          # or "youtube"
video_id: "XXXXXXXXXX"         # ID from the URL
description: "Key coaching points for this drill."
---
```

Save the file as `_posts/YYYY-MM-DD-slug-title.md`.

---

## Local Development

Requirements: Ruby, Bundler

```bash
bundle install
bundle exec jekyll serve
```

The site will be available at `http://localhost:4000/goalie-vault`.

---

## Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `new-drill.yml` | Issue labeled `new-drill` | Parses the issue form, fetches a thumbnail (YouTube CDN URL or `yt-dlp` for Instagram), creates `_posts/*.md`, commits, and closes the issue |
| `build-and-verify.yml` | Push / PR | Runs `validate_taxonomy.py` (strict YAML + tag check) and `check_site.py` (landing pages + API endpoints) |
| `refresh-thumbs.yml` | Daily 06:17 UTC + manual | Calls `scripts/refresh_thumb_urls.py` to re-fetch expiring Instagram CDN URLs into `_data/thumbnails.json` and opens an auto-merging PR |
| `remove-thumbnail.yml` | Manual — Actions tab → **Run workflow** | Clears `thumbnail:` from the post frontmatter and deletes the image from `assets/images/thumbs/`. Input: `post_slug` |
| `refetch-thumbnails.yml` | Manual or weekly (Mon 03:00 UTC) | Legacy: scans Instagram posts with empty `thumbnail:`, retries `yt-dlp`, patches post files |

To trigger `remove-thumbnail`: go to **Actions → Remove Drill Thumbnail → Run workflow** and enter the post slug.

---

## Thumbnail URL Cache

Instagram CDN URLs are signed and expire (~14 days). To stay legally clean
(no locally stored Instagram thumbnails) the site reads URLs from
[`_data/thumbnails.json`](_data/thumbnails.json), keyed by `video_id`.

The daily `refresh-thumbs.yml` workflow runs `scripts/refresh_thumb_urls.py`
which:

- Picks up to N entries whose `expires` is within the safety window or whose
  `fetched` timestamp is older than the min-age.
- Re-resolves each via `yt-dlp` with random delays + UA rotation.
- Backs off after `--max-attempts` failures.
- Opens a PR (auto-merged when checks pass).

Layouts read `site.data.thumbnails[post.video_id].url`, falling back to the
legacy `post.thumbnail` field, then to a placeholder via `onerror`.

See [_docs/legal-and-compliance-plan.md](_docs/legal-and-compliance-plan.md)
§1.2 + §3.2 for context.

---

## Project Structure

```
_posts/                  # Video drill posts (auto-generated or manual)
_drafts/                 # Soft-deleted posts (excluded from build)
_quizzes/                # Interactive quiz definitions (YAML front matter)
_layouts/                # default.html, post.html, quiz.html, category.html templates
_data/
  quiz_config.yml        # Google Sheets submission config (optional)
  thumbnails.json        # Instagram CDN URL cache (refreshed daily)
assets/images/           # Logo and media
assets/images/thumbs/    # Legacy local Instagram thumbnails (being phased out)
scripts/                 # Local curation pipeline + audit/validator scripts
  curate/                # Static-served vanilla-JS UIs + manifests
assets/js/
  quiz.js                # Quiz engine (state, scoring, Chart.js)
  api.js                 # GoalieAPI static REST fetcher
assets/css/
  vault.css              # Full site stylesheet (dark mode)
api/v1/
  all.json               # All drills (Liquid → JSON at build time)
  search.json            # Lightweight search index
  categories/
    index.json           # Available categories with counts
    warmup.json          # Per-category drill endpoints
    coordination.json
    strength.json
    reaction.json
    movement.json
    goal-technical.json
    stretching.json
_config.yml              # Jekyll site configuration
index.md                 # Home page with drill grid and filter bar
quizzes.md               # Quiz index page
.github/
  workflows/             # new-drill.yml, remove-thumbnail.yml, refetch-thumbnails.yml
  ISSUE_TEMPLATE/        # new-drill.yml — issue form for contributors
```

---

## Static REST API

Jekyll generates static JSON endpoints at build time, hosted as plain files on GitHub Pages. No backend required.

| Endpoint | Description |
|---|---|
| [`/api/v1/all.json`](https://brndkfr.github.io/goalie-vault/api/v1/all.json) | All drills — full schema |
| [`/api/v1/search.json`](https://brndkfr.github.io/goalie-vault/api/v1/search.json) | Lightweight index: `title`, `category`, `url` |
| [`/api/v1/categories/index.json`](https://brndkfr.github.io/goalie-vault/api/v1/categories/index.json) | All available categories with drill counts and endpoint URLs |
| `/api/v1/categories/{name}.json` | Drills filtered by category (e.g. `warmup`, `coordination`, `strength`) |

Each drill object contains: `title`, `author`, `handle`, `platform`, `video_id`, `category`, `description`, `thumbnail`, `url`.

**JavaScript fetcher** — `assets/js/api.js` exposes a `GoalieAPI` module:

```js
GoalieAPI.fetchAll()              // → Promise<Array>  all drills
GoalieAPI.fetchCategory('warmup') // → Promise<Array>  filtered drills
GoalieAPI.fetchSearch()           // → Promise<Array>  lightweight index
```

Include it on any page with `<script src="{{ site.baseurl }}/assets/js/api.js"></script>`. `BASE_URL` is automatically resolved from the Jekyll `site.baseurl` injected by the layouts.

---

## Curation Tooling

The `scripts/` folder contains a local pipeline for bulk-importing Instagram
posts and editing existing drills. Everything runs against the static files
in the repo — no backend, no database. Browser UIs are single HTML files
served over `python -m http.server` and persist work-in-progress to
`localStorage`; you export a JSON file and a Python script applies it to
disk.

**Instagram triage** — pick which Instagram links become posts.

```bash
python scripts/fetch_instagram_thumbs.py     # yt-dlp -> assets/images/thumbs/ + scripts/curate/instagram/*.json
python scripts/build_curate_manifest.py      # -> scripts/curate/manifest.json
python scripts/auto_categorize.py            # heuristic suggestions
# open http://localhost:8765/scripts/curate/  -> keep / maybe / discard, edit categories, Export
python scripts/apply_discards.py             # remove discarded thumbs+metadata
python scripts/generate_posts.py             # write _posts/*.md for kept items
```

**Post curator** — edit or soft-delete existing `_posts/*.md`.

```bash
python scripts/build_posts_manifest.py       # -> scripts/curate/posts_manifest.json
# open http://localhost:8765/scripts/curate/posts.html
#   - edit title/author/handle/description, toggle multi-select category chips
#   - mark posts for deletion, then Export
python scripts/apply_posts_curation.py --dry-run   # preview
python scripts/apply_posts_curation.py             # rewrite front-matter / move deletes to _drafts/
```

The curator reads the canonical category list from `index.md` so the chips
stay in sync with the homepage filter bar. Categories present in posts but
not on the homepage are shown as italic "extra" chips.

---

## Quizzes

Interactive quizzes live at [`/quizzes`](https://brndkfr.github.io/goalie-vault/quizzes). Each quiz is a Markdown file in `_quizzes/` with a YAML questions block.

**Supported question types:** `single`, `multi`, `truefalse`

Each question supports an optional `explanation` field — shown inline only when the player answers incorrectly.

The quiz engine (`assets/js/quiz.js`) handles state, scoring, and a Chart.js doughnut chart on the results screen. Results can optionally be posted to a Google Sheet via a configurable form action in `_data/quiz_config.yml`.

---

## Roadmap

- [x] Quizzes collection (`_quizzes/`) with interactive engine
- [x] Static REST API (`/api/v1/`)
- [x] Live search on the drill grid
- [x] Local curation tooling for Instagram triage and post editing
- [x] On-demand Instagram thumbnail URL cache (`_data/thumbnails.json`)
- [ ] Articles collection (`_articles/`)
- [ ] Phase-4 cleanup: drop local `assets/images/thumbs/*.jpg` once URL cache is fully populated

---

## License

This repository uses a dual license:

| What | License |
|---|---|
| **Code** — layouts, workflows, config, templates | [MIT](LICENSE) |
| **Content** — posts, coaching notes, descriptions | [CC BY 4.0](LICENSE-CONTENT) |

Content may be shared or adapted for any purpose, including commercially, as long as **credit is given to Bernd Kiefer (brndkfr)** with a link to the source.

> Embedded videos remain the property of their respective creators and are subject to the terms of their hosting platforms (Instagram, YouTube, etc.).
