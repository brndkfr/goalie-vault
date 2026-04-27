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
_layouts/                # default.html and post.html templates
assets/images/           # Logo and media
assets/images/thumbs/    # Auto-fetched Instagram thumbnails
_config.yml              # Jekyll site configuration
index.md                 # Home page with drill grid and filter bar
.github/
  workflows/             # new-drill.yml, remove-thumbnail.yml
  ISSUE_TEMPLATE/        # new-drill.yml — issue form for contributors
```

---

## Roadmap

- [ ] Articles collection (`_articles/`)
- [ ] Quizzes collection (`_quizzes/`)
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
