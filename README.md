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
| `remove-thumbnail.yml` | Manual — Actions tab → **Run workflow** | Clears `thumbnail:` from the post frontmatter and deletes the image from `assets/images/thumbs/`. Input: `post_slug` (e.g. `2026-04-24-inner-core-strength`) |
| `refetch-thumbnails.yml` | Manual or weekly (Mon 03:00 UTC) | Scans all Instagram posts with empty `thumbnail:`, retries `yt-dlp` for each, patches post files and commits. Results shown in the Actions run summary. |

To trigger `remove-thumbnail`: go to **Actions → Remove Drill Thumbnail → Run workflow** and enter the post slug.

---

## Project Structure

```
_posts/                  # Video drill posts (auto-generated or manual)
_quizzes/                # Interactive quiz definitions (YAML front matter)
_layouts/                # default.html, post.html, quiz.html templates
_data/
  quiz_config.yml        # Google Sheets submission config (optional)
assets/images/           # Logo and media
assets/images/thumbs/    # Auto-fetched Instagram thumbnails
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

## Quizzes

Interactive quizzes live at [`/quizzes`](https://brndkfr.github.io/goalie-vault/quizzes). Each quiz is a Markdown file in `_quizzes/` with a YAML questions block.

**Supported question types:** `single`, `multi`, `truefalse`

Each question supports an optional `explanation` field — shown inline only when the player answers incorrectly.

The quiz engine (`assets/js/quiz.js`) handles state, scoring, and a Chart.js doughnut chart on the results screen. Results can optionally be posted to a Google Sheet via a configurable form action in `_data/quiz_config.yml`.

---

## Roadmap

- [x] Quizzes collection (`_quizzes/`) with interactive engine
- [x] Static REST API (`/api/v1/`)
- [ ] Articles collection (`_articles/`)
- [ ] Category filter pages (`/warmup`, `/coordination`, etc.)
- [ ] Search functionality

---

## License

This repository uses a dual license:

| What | License |
|---|---|
| **Code** — layouts, workflows, config, templates | [MIT](LICENSE) |
| **Content** — posts, coaching notes, descriptions | [CC BY 4.0](LICENSE-CONTENT) |

Content may be shared or adapted for any purpose, including commercially, as long as **credit is given to Bernd Kiefer (brndkfr)** with a link to the source.

> Embedded videos remain the property of their respective creators and are subject to the terms of their hosting platforms (Instagram, YouTube, etc.).
