/* ============================================================
   GOALIE VAULT — Quiz Engine (bilingual: dual data-lang spans)
   ============================================================ */

(function () {
  'use strict';

  // ── i18n for chrome strings ─────────────────────────────────
  const UI = {
    counter:        { de: (n,t) => `Frage ${n} von ${t}`, en: (n,t) => `Question ${n} of ${t}` },
    next:           { de: 'Weiter',                en: 'Next' },
    nextArrow:      { de: 'Weiter →',              en: 'Next →' },
    seeResults:     { de: 'Ergebnisse anzeigen',   en: 'See Results' },
    true:           { de: 'Wahr',                  en: 'True' },
    false:          { de: 'Falsch',                en: 'False' },
    explanation:    { de: '💡 Erklärung:',         en: '💡 Explanation:' },
    breakdownTitle: { de: 'Fragenübersicht',       en: 'Question Breakdown' },
    yourAnswer:     { de: 'Deine Antwort:',        en: 'Your answer:' },
    correctAnswer:  { de: 'Richtige Antwort:',     en: 'Correct answer:' },
    noAnswer:       { de: '(keine Antwort)',       en: '(no answer)' },
    namePlaceholder:{ de: 'Namen eingeben…',       en: 'Enter your name…' },
    excellent:      { de: 'Exzellent! 🏆',         en: 'Excellent! 🏆' },
    good:           { de: 'Gut gemacht! 👍',       en: 'Good effort! 👍' },
    keep:           { de: 'Weiter üben! 💪',       en: 'Keep practising! 💪' },
    legendCorrect:  { de: 'Richtig',               en: 'Correct' },
    legendWrong:    { de: 'Falsch',                en: 'Incorrect' },
    scoreText:      {
      de: (s,t,c) => `${s} von ${t} richtig — ${c.de}`,
      en: (s,t,c) => `${s} out of ${t} correct — ${c.en}`,
    },
  };

  // ── State ───────────────────────────────────────────────────
  let playerName = '';
  let currentIndex = 0;
  let userAnswers = [];     // each entry: array of selected indices/values
  let waitingForAdvance = false;
  let chart = null;

  const $ = id => document.getElementById(id);

  // ── Helpers ────────────────────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function pickLang(value, fallback) {
    if (value && typeof value === 'object' && ('de' in value || 'en' in value)) {
      return value[fallback] ?? value.en ?? value.de ?? '';
    }
    return value == null ? '' : String(value);
  }
  /** Render a {de,en} object (or plain string) as dual <span data-lang> tags. */
  function dual(value) {
    if (value && typeof value === 'object' && ('de' in value || 'en' in value)) {
      return `<span data-lang="de">${escHtml(value.de ?? value.en ?? '')}</span>`
           + `<span data-lang="en">${escHtml(value.en ?? value.de ?? '')}</span>`;
    }
    // Plain string — show in both languages.
    return `<span data-lang="de">${escHtml(value ?? '')}</span>`
         + `<span data-lang="en">${escHtml(value ?? '')}</span>`;
  }
  /** Like `dual` but each side is computed from a {de,en} input via fn(value, lang). */
  function dualFn(value, fn) {
    return `<span data-lang="de">${escHtml(fn(value, 'de'))}</span>`
         + `<span data-lang="en">${escHtml(fn(value, 'en'))}</span>`;
  }
  function applyLang() { if (window.applyLang) window.applyLang(); }
  function currentLang() { return localStorage.getItem('vault-lang') || 'de'; }

  /** Get options array for a question in a specific language (handles both schemas). */
  function optionsFor(q, lang) {
    if (!q.options) return [];
    if (Array.isArray(q.options)) return q.options;          // legacy single-lang
    return q.options[lang] ?? q.options.en ?? q.options.de ?? [];
  }

  // ── Splash screen ──────────────────────────────────────────
  const nameInput = $('quiz-name');
  const startBtn  = $('quiz-start');

  function setNamePlaceholder() {
    nameInput.placeholder = UI.namePlaceholder[currentLang()] || UI.namePlaceholder.en;
  }
  setNamePlaceholder();
  document.addEventListener('langchange', setNamePlaceholder);

  nameInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') startQuiz();
  });
  startBtn.addEventListener('click', startQuiz);

  function startQuiz() {
    playerName   = nameInput.value.trim();
    currentIndex = 0;
    userAnswers  = [];
    waitingForAdvance = false;
    $('quiz-splash').style.display    = 'none';
    $('quiz-question').style.display  = 'block';
    $('quiz-results').style.display   = 'none';
    renderQuestion(0);
  }

  // ── Question rendering ─────────────────────────────────────
  function renderQuestion(idx) {
    const q     = QUIZ_DATA[idx];
    const total = QUIZ_DATA.length;

    // Progress bar
    const pct = Math.round((idx / total) * 100);
    $('quiz-progress-bar').style.width = pct + '%';

    // Counter — bilingual
    $('quiz-counter').innerHTML =
      `<span data-lang="de">${escHtml(UI.counter.de(idx + 1, total))}</span>` +
      `<span data-lang="en">${escHtml(UI.counter.en(idx + 1, total))}</span>`;

    // Question text — bilingual
    $('quiz-q-text').innerHTML = dual(q.text);

    // Reset state
    $('quiz-options').innerHTML       = '';
    $('quiz-explanation').style.display = 'none';
    $('quiz-explanation').innerHTML   = '';
    const isLast = idx === total - 1;
    $('quiz-next').disabled = true;
    $('quiz-next').innerHTML = isLast ? dual(UI.seeResults) : dual(UI.next);

    // Render options
    if (q.type === 'truefalse') {
      [['true', true], ['false', false]].forEach(([key, val]) => {
        const btn = makeOptionBtn({ de: UI[key].de, en: UI[key].en }, val, q.type);
        $('quiz-options').appendChild(btn);
      });
    } else {
      const optsDe = optionsFor(q, 'de');
      const optsEn = optionsFor(q, 'en');
      const len = Math.max(optsDe.length, optsEn.length);
      for (let i = 0; i < len; i++) {
        const btn = makeOptionBtn(
          { de: optsDe[i] ?? optsEn[i] ?? '', en: optsEn[i] ?? optsDe[i] ?? '' },
          i,
          q.type
        );
        $('quiz-options').appendChild(btn);
      }
    }
    applyLang();
  }

  function makeOptionBtn(label, value, type) {
    const btn = document.createElement('button');
    btn.className = 'quiz-option';
    btn.innerHTML = dual(label);
    btn.dataset.value = JSON.stringify(value);
    btn.addEventListener('click', () => onOptionClick(btn, type));
    return btn;
  }

  function onOptionClick(btn, type) {
    const optionBtns = $('quiz-options').querySelectorAll('.quiz-option');
    if (type === 'multi') {
      btn.classList.toggle('selected');
    } else {
      optionBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    }
    const anySelected = [...optionBtns].some(b => b.classList.contains('selected'));
    $('quiz-next').disabled = !anySelected;
  }

  // ── Next / submit ──────────────────────────────────────────
  $('quiz-next').addEventListener('click', handleNextClick);

  function handleNextClick() {
    if (waitingForAdvance) {
      waitingForAdvance = false;
      const isLast = currentIndex === QUIZ_DATA.length - 1;
      if (isLast) {
        showResults();
      } else {
        currentIndex++;
        renderQuestion(currentIndex);
      }
      return;
    }

    // Record answer
    const q = QUIZ_DATA[currentIndex];
    const optionBtns = [...$('quiz-options').querySelectorAll('.quiz-option')];
    const selected   = optionBtns
      .filter(b => b.classList.contains('selected'))
      .map(b => JSON.parse(b.dataset.value));

    userAnswers.push(selected);

    // Reveal correct/wrong visual states
    markOptions(optionBtns, q);

    // Show inline explanation only when the answer is wrong
    const answeredCorrectly = isCorrect(q, selected);
    if (SHOW_INLINE && q.explanation && !answeredCorrectly) {
      const box = $('quiz-explanation');
      box.innerHTML =
        `<strong>${dual(UI.explanation)}</strong> ${dual(q.explanation)}`;
      box.style.display = 'block';
      applyLang();
    }

    // Disable all options
    optionBtns.forEach(b => b.disabled = true);

    const isLast = currentIndex === QUIZ_DATA.length - 1;
    $('quiz-next').disabled = false;
    $('quiz-next').innerHTML = isLast ? dual(UI.seeResults) : dual(UI.nextArrow);
    applyLang();
    waitingForAdvance = true;
  }

  function markOptions(btns, q) {
    const correct = Array.isArray(q.answer) ? q.answer : [q.answer];
    btns.forEach(btn => {
      const val = JSON.parse(btn.dataset.value);
      const isCorrectOption = correct.some(c => JSON.stringify(c) === JSON.stringify(val));
      const wasSelected     = btn.classList.contains('selected');
      btn.classList.remove('selected');
      if      (isCorrectOption && wasSelected)  btn.classList.add('option-correct');
      else if (!isCorrectOption && wasSelected) btn.classList.add('option-wrong');
      else if (isCorrectOption && !wasSelected) btn.classList.add('option-missed');
    });
  }

  // ── Results ────────────────────────────────────────────────
  function showResults() {
    $('quiz-question').style.display = 'none';
    $('quiz-results').style.display  = 'block';
    $('quiz-progress-bar').style.width = '100%';

    const total = QUIZ_DATA.length;
    let score = 0;
    QUIZ_DATA.forEach((q, i) => { if (isCorrect(q, userAnswers[i])) score++; });
    const pct = Math.round((score / total) * 100);

    $('quiz-score-label').textContent = pct + '%';
    const comment = pct >= 80 ? UI.excellent : pct >= 60 ? UI.good : UI.keep;
    $('quiz-score-text').innerHTML =
      `<span data-lang="de">${escHtml(UI.scoreText.de(score, total, comment))}</span>` +
      `<span data-lang="en">${escHtml(UI.scoreText.en(score, total, comment))}</span>`;

    // Chart — re-render label set on lang change
    function chartLabels() {
      const lang = currentLang();
      return [UI.legendCorrect[lang], UI.legendWrong[lang]];
    }
    if (chart) chart.destroy();
    chart = new Chart($('quiz-chart'), {
      type: 'doughnut',
      data: {
        labels: chartLabels(),
        datasets: [{
          data: [score, total - score],
          backgroundColor: ['#00f2ff', '#c0392b'],
          borderWidth: 0,
        }],
      },
      options: {
        cutout: '70%',
        plugins: {
          legend: { position: 'bottom', labels: { color: '#e8e8e8', font: { family: 'Inter' } } },
          tooltip: { enabled: true },
        },
        animation: { duration: 800 },
      },
    });
    document.addEventListener('langchange', () => {
      if (!chart) return;
      chart.data.labels = chartLabels();
      chart.update();
    });

    // Breakdown
    const bd = $('quiz-breakdown');
    bd.innerHTML = `<h3 class="quiz-breakdown__title">${dual(UI.breakdownTitle)}</h3>`;

    QUIZ_DATA.forEach((q, i) => {
      const correct = isCorrect(q, userAnswers[i]);
      const card    = document.createElement('div');
      card.className = 'quiz-bd-card ' + (correct ? 'quiz-bd-card--correct' : 'quiz-bd-card--wrong');
      const icon    = correct ? '✅' : '❌';

      const userAnsHtml = formatAnswerHtml(q, userAnswers[i]);
      const corrAnsHtml = formatAnswerHtml(q, normaliseAnswer(q.answer));

      let html = `<div class="quiz-bd-top">${icon} <span class="quiz-bd-q">${dual(q.text)}</span></div>`;
      html    += `<div class="quiz-bd-detail">`;
      html    += `<span class="quiz-bd-label">${dual(UI.yourAnswer)}</span> `;
      html    += `<span class="${correct ? 'quiz-ans-correct' : 'quiz-ans-wrong'}">${userAnsHtml}</span>`;
      if (!correct) {
        html  += `<br><span class="quiz-bd-label">${dual(UI.correctAnswer)}</span> `;
        html  += `<span class="quiz-ans-correct">${corrAnsHtml}</span>`;
      }
      html    += `</div>`;
      if (q.explanation) {
        html  += `<div class="quiz-bd-explanation">${dual(q.explanation)}</div>`;
      }

      card.innerHTML = html;
      bd.appendChild(card);
    });

    applyLang();
    sendToSheets(score, total);
  }

  function isCorrect(q, selected) {
    if (!selected || selected.length === 0) return false;
    const correct = normaliseAnswer(q.answer);
    const sortKey = a => JSON.stringify(a);
    return JSON.stringify([...selected].sort((a,b)=>sortKey(a)<sortKey(b)?-1:1)) ===
           JSON.stringify([...correct].sort((a,b)=>sortKey(a)<sortKey(b)?-1:1));
  }
  function normaliseAnswer(answer) { return Array.isArray(answer) ? answer : [answer]; }

  /** Render an answer as dual <span data-lang> spans, mapping option indexes per language. */
  function formatAnswerHtml(q, values) {
    if (!values || values.length === 0) return dual(UI.noAnswer);
    if (q.type === 'truefalse') {
      const parts = values.map(v => v ? UI.true : UI.false);
      return parts.map(p => dual(p)).join(', ');
    }
    return dualFn(null, (_, lang) => {
      const opts = optionsFor(q, lang);
      return values.map(v => (typeof v === 'number' ? (opts[v] ?? v) : v)).join(', ');
    });
  }

  // ── Google Sheets submission ───────────────────────────────
  function sendToSheets(score, total) {
    if (!QUIZ_CONFIG || !QUIZ_CONFIG.action) return;
    try {
      const titleStr = pickLang(QUIZ_TITLE, currentLang()) || pickLang(QUIZ_TITLE, 'en');
      fetch(QUIZ_CONFIG.action, {
        method: 'POST',
        mode: 'no-cors',
        body: new URLSearchParams({
          [QUIZ_CONFIG.fields.name]:       playerName,
          [QUIZ_CONFIG.fields.quiz_title]: titleStr,
          [QUIZ_CONFIG.fields.score]:      `${score} / ${total}`,
          [QUIZ_CONFIG.fields.date]:       new Date().toISOString().slice(0, 10),
        }),
      });
    } catch (e) { /* silently ignore */ }
  }

  // ── Retake ─────────────────────────────────────────────────
  $('quiz-retake').addEventListener('click', () => {
    waitingForAdvance = false;
    $('quiz-results').style.display  = 'none';
    $('quiz-splash').style.display   = 'block';
    nameInput.value = playerName;
    startBtn.disabled = false;
  });

})();
