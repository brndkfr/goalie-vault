# Legal & Compliance Plan

**Status:** Draft – engineering analysis only, not legal advice. Confirm
substantive points with a German/Swiss media lawyer before relying on them.

**Last updated:** 2026-05-08

---

## 1. Risk landscape

### 1.1 Copyright in embedded videos

- The site does **not** host videos directly. Instagram (`blockquote` embed)
  and YouTube (`iframe` embed) provide an implicit license for embedding via
  their platform ToS, supported by EU case law (CJEU *BestWater*, 2014).
- That license assumes the original upload was **lawful**. If the source
  account had no rights, embedding still propagates the infringement.
- Editorial curation (which we do) is closer to *publication* than *passive
  linking* (CJEU *Renckhoff*, *YouTube/Cyando* 2021), increasing risk.

### 1.2 Locally stored thumbnails (BIGGEST EXPOSURE)

Instagram thumbnails are committed under [assets/images/thumbs/](../assets/images/thumbs/).
This is **reproduction + distribution + making available**, all exclusive
rights of the copyright holder (UrhG §16/§19a, EU InfoSoc art. 2). Attribution
does **not** create a license.

| Source | Risk | Why |
|---|---|---|
| YouTube hot-link via `img.youtube.com` | Low | Served from YouTube CDN |
| Instagram thumbs in repo | **High** | Reproduced and served from our domain |

### 1.3 GDPR / personal data

We publish names and handles (`author`, `handle`) → personal data under GDPR.

- Lawful basis: art. 6(1)(f) **legitimate interest**. Requires a documented
  Legitimate Interest Assessment (LIA).
- "Household exception" art. 2(2)(c) does **not** apply to a public site.

### 1.4 Embeds = third-party data transfer

When a visitor loads a post page, IP + tracking cookies go to Meta / Google
on first paint. Implications:

- **Schrems II + Planet49**: prior **informed consent** required.
- **CJEU IAB Europe 2024**: tightens consent quality.
- **EU-US DPF**: currently valid but contested.
- Mitigation: **two-click / Shariff pattern** — placeholder until user opt-in.

### 1.5 Right of personality (Recht am eigenen Bild, KUG §22)

People in videos can demand removal even if the original Instagram post is
still public. Editorial-style republication raises this risk.

### 1.6 DACH-specific obligations

- **Impressum** (Germany TMG / MStV §5; Switzerland: art. 3 UWG) — operator
  identification page is mandatory.
- **DSA contact point** (Digital Services Act art. 11, since Feb 2024) — a
  notice address reachable in the EU.
- **Datenschutzerklärung** (privacy policy) — required content listed below.

### 1.7 Database right & Instagram ToS

Systematic extraction of Instagram metadata violates Meta ToS and may
trigger the EU sui-generis database right (Database Directive). Remedy
typically contractual (account ban, C&D), but real if noticed.

### 1.8 Trademark / licensing of own content

- "Goalie Vault" trademark search recommended.
- Coaching notes correctly marked CC BY 4.0 in [_layouts/post.html](../_layouts/post.html).
- [LICENSE](../LICENSE) (code) and [LICENSE-CONTENT](../LICENSE-CONTENT) split is in place.

### 1.9 Accessibility (forward-looking)

European Accessibility Act enforceable since June 2025 for commercial sites.
Hobby sites currently out of scope; if monetization happens, alt text /
keyboard nav / ARIA become required.

---

## 2. Prioritized action plan

| # | Action | Owner | Status |
|---|---|---|---|
| 1 | Two-click / Shariff embed pattern in [_layouts/post.html](../_layouts/post.html) | dev | TODO |
| 2 | Stop committing new Instagram thumbnails; default to gradient placeholder in [scripts/generate_posts.py](../scripts/generate_posts.py) | dev | TODO |
| 3 | Plan migration of existing IG thumbs (delete from repo or replace with oEmbed-on-demand) | dev | TODO |
| 4 | `/impressum/` page — operator name, contact, accountable address | content | TODO |
| 5 | `/privacy/` page — Datenschutzerklärung covering data collected, basis, retention, recipients (Meta, Google), rights, contact | content | TODO |
| 6 | DSA contact point in footer (`abuse@…` or similar) + documented takedown procedure | content | TODO |
| 7 | Footer link "Report content / Remove my video" with `mailto:` template | dev | TODO |
| 8 | Write LIA for processing names/handles; keep on file | content | TODO |
| 9 | Add `robots.txt` directive blocking AI scrapers if desired | dev | OPTIONAL |
| 10 | Trademark search for "Goalie Vault" | content | OPTIONAL |

## 3. Implementation notes

### 3.1 Two-click embeds (priority 1)

Replace the inline Instagram `blockquote` and YouTube `iframe` in
[_layouts/post.html](../_layouts/post.html) with a placeholder element that
loads the embed only after a user click.

- Placeholder: existing `drill-card__thumb--ig` gradient (Instagram) or the
  YouTube hot-link thumbnail (YouTube — still LSO neutral).
- A "Load video (sends data to Instagram/YouTube)" button replaces the
  embed until clicked.
- Once clicked, inject the embed script and let it run; remember the choice
  per session via `sessionStorage` (no persistent cookie needed).
- Reference pattern: heise's "Shariff" buttons, embetty.

### 3.2 Thumbnails (priority 2 + 3)

- New posts: stop fetching IG thumbs in [scripts/generate_posts.py](../scripts/generate_posts.py)
  and [scripts/fetch_instagram_thumbs.py](../scripts/fetch_instagram_thumbs.py).
- Existing posts: bulk-update front matter `thumbnail` to `skip` (already
  supported in layouts) and remove the JPEGs from
  [assets/images/thumbs/](../assets/images/thumbs/) in a follow-up commit.
- Optional: keep YouTube hot-linking via `img.youtube.com/vi/<id>/hqdefault.jpg`
  (already in use for `platform: youtube` posts).

### 3.3 Privacy policy content checklist

Cover: controller identity, contact, data categories (server logs, embed
provider data), purposes, legal bases (art. 6(1)(f); art. 6(1)(a) for the
two-click consent), recipients (Meta, Google, GitHub Pages CDN), retention,
international transfers (EU-US DPF), data subject rights (access/erasure/
objection/portability/complaint to supervisory authority), no automated
decision-making.

### 3.4 Takedown / DSA flow

1. Public e-mail address listed in footer + Impressum.
2. Submission template (mailto pre-fill): URL, claimed right, contact,
   declaration of good faith.
3. Internal log (private file) of received notices, action taken, date.
4. Acknowledge in 24h, act in 7 days, decline only with reason.

---

## 4. Open questions

- Is the site monetized or planned to be? (changes risk profile materially)
- Is the operator a registered business? (affects Impressum content)
- Hosting target — currently GitHub Pages. Adequate for the analysis above.
- Audience size and geography — affects DSA classification thresholds.

## 5. Disclaimer

This document captures engineering-level legal awareness. Final wording for
Impressum, privacy policy, and any takedown response **must** be reviewed by
qualified counsel before publication.
