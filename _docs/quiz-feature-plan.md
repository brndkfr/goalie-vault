# Quiz Feature Plan

## Overview

Add a fully client-side quiz section to the Goalie Vault Jekyll site.  
Quizzes are authored as YAML files in `_quizzes/`. A JavaScript engine renders questions,
collects the user's name, and on completion shows an animated doughnut chart (Chart.js)
for the score, then silently POSTs the result to Google Sheets via a hidden Google Form submission.

## Decisions

| Topic | Decision |
|---|---|
| Question types | Mix: single-choice, multi-choice, true/false |
| Results storage | Google Sheets via hidden Google Form POST |
| Quiz authoring | YAML front matter in `_quizzes/` collection |
| Identity | User enters name before starting |
| Chart library | Chart.js via CDN (~50 kb, no build step) |

---

## Implementation Steps

### 1. Quiz YAML format

Create `_quizzes/example-goalie-rules.md` as the first quiz + template.

Front matter structure:
```yaml
---
layout: quiz
title: "Goalie Rules Quiz"
description: "Test your knowledge of floorball goalie rules."
cover_image: ""   # optional, path to image
questions:
  - type: single          # single | multi | truefalse
    text: "Can the goalie play the ball with their hand?"
    options:
      - "Yes, always"
      - "Yes, but only inside the crease"
      - "No, never"
    answer: 1             # 0-indexed; array for multi e.g. [0, 2]

  - type: truefalse
    text: "The goalie may leave the crease to play the ball."
    answer: true

  - type: multi
    text: "Which of the following apply to the goalie position?"
    options:
      - "Must wear a helmet"
      - "Can score goals"
      - "Is allowed to throw the ball"
      - "Cannot play past the centre line"
    answer: [0, 3]
---
```

### 2. Quiz index page

Create `quizzes.md` at repo root:
- `layout: default`
- Loops `site.quizzes` and renders a card grid matching the drill grid style
- Shows title, description, question count badge
- Links to each quiz's individual page

### 3. Quiz layout (`_layouts/quiz.html`)

Extends `default.html`. Structure:

1. **Name splash screen** — full-screen overlay, text input + Start button
2. **Question screen** — one question at a time, progress bar at top
   - Single-choice → radio-style option buttons
   - Multi-choice → checkbox-style option buttons (highlight on toggle)
   - True/False → two large buttons
   - "Next" button disabled until at least one option selected
3. **Results screen** — shown after last question:
   - Doughnut chart: correct (teal `#00f2ff`) vs incorrect (dark red `#c0392b`)
   - Score as `X / Y` and percentage
   - Per-question breakdown (✅ / ❌ with correct answer shown for wrong ones)
   - "Retake" button → resets to name splash

Inject quiz data from Jekyll into JS:
```html
<script>
  const QUIZ_DATA = {{ page.questions | jsonify }};
  const QUIZ_TITLE = {{ page.title | jsonify }};
</script>
<script src="{{ site.baseurl }}/assets/js/quiz.js"></script>
```

### 4. Quiz JS engine (`assets/js/quiz.js`)

State managed in a plain JS object:
```
{ name, questions, currentIndex, answers[], score }
```

Functions:
- `startQuiz(name)` — hide splash, show first question
- `renderQuestion(index)` — populate DOM from `QUIZ_DATA[index]`
- `selectOption(el)` — toggle selection; for single deselects others
- `nextQuestion()` — record answer, advance or call `showResults()`
- `showResults()` — calculate score, render chart, send to Sheets

### 5. Pie chart (Chart.js)

In `showResults()`:
```js
new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Correct', 'Incorrect'],
    datasets: [{ data: [score, total - score],
                 backgroundColor: ['#00f2ff', '#c0392b'] }]
  },
  options: { cutout: '70%', plugins: { legend: { position: 'bottom' } } }
});
```

### 6. Google Sheets submission

**One-time manual setup (by Bernd):**
1. Go to [forms.google.com](https://forms.google.com) and create a form with these 4 short-answer fields:
   - Name
   - Quiz Title
   - Score (e.g. "7 / 10")
   - Date
2. Link the form response to a Google Sheet
3. Open the form, right-click → Inspect → find the `<form action="...">` URL and the `entry.XXXXXXX` IDs for each field
4. Fill in `_data/quiz_config.yml`:

```yaml
# _data/quiz_config.yml
google_form_action: "https://docs.google.com/forms/d/e/XXXXXXXXXX/formResponse"
fields:
  name:       "entry.000000001"
  quiz_title: "entry.000000002"
  score:      "entry.000000003"
  date:       "entry.000000004"
```

**In JS** (`sendToSheets()` called from `showResults()`):
```js
fetch(QUIZ_CONFIG.action, {
  method: 'POST',
  mode: 'no-cors',         // avoids CORS error; response is opaque but POST succeeds
  body: new URLSearchParams({
    [QUIZ_CONFIG.fields.name]:       playerName,
    [QUIZ_CONFIG.fields.quiz_title]: QUIZ_TITLE,
    [QUIZ_CONFIG.fields.score]:      `${score} / ${total}`,
    [QUIZ_CONFIG.fields.date]:       new Date().toISOString().slice(0,10)
  })
});
```

Jekyll injects `quiz_config.yml` values into the layout:
```html
<script>
  const QUIZ_CONFIG = {
    action: {{ site.data.quiz_config.google_form_action | jsonify }},
    fields: {{ site.data.quiz_config.fields | jsonify }}
  };
</script>
```

### 7. Navigation

Add "Quizzes" link to the sticky header in `_layouts/default.html`:
```html
<nav>
  <a href="{{ site.baseurl }}/">Drills</a>
  <a href="{{ site.baseurl }}/quizzes">Quizzes</a>
</nav>
```

### 8. CSS additions to `assets/css/vault.css`

New selectors needed:
- `.quiz-grid` — card grid (reuse drill grid pattern)
- `.quiz-card` — individual quiz card
- `.quiz-splash` — full-screen name entry overlay
- `.quiz-progress` — thin progress bar at top (`background: var(--accent)`)
- `.quiz-option` — option button; `.quiz-option.selected` in teal
- `.quiz-results` — results screen container
- `.chart-container` — fixed-size wrapper for the doughnut

---

## Files to Create

```
_quizzes/
  example-goalie-rules.md       ← first quiz + template
_layouts/
  quiz.html                     ← quiz page layout
assets/
  js/
    quiz.js                     ← quiz engine
_data/
  quiz_config.yml               ← Google Form endpoint + field IDs (fill in manually)
quizzes.md                      ← quiz index page
```

Modified:
- `_layouts/default.html` — add Quizzes nav link + Chart.js CDN on quiz pages
- `assets/css/vault.css` — quiz styles

---

## Open Questions / Later

- Should quiz results page be shareable (URL with score param)?
- Leaderboard? (Would need a backend or Airtable)
- Should quizzes have a time limit per question?
