/* ============================================================
   GOALIE VAULT — Quiz Engine
   ============================================================ */

(function () {
  'use strict';

  // ── State ──────────────────────────────────────────────────
  let playerName = '';
  let currentIndex = 0;
  let userAnswers = []; // each entry: array of selected indices

  // ── DOM helpers ────────────────────────────────────────────
  const $ = id => document.getElementById(id);

  // ── Splash screen ──────────────────────────────────────────
  const nameInput  = $('quiz-name');
  const startBtn   = $('quiz-start');

  nameInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') startQuiz();
  });
  startBtn.addEventListener('click', startQuiz);

  function startQuiz() {
    playerName   = nameInput.value.trim();
    currentIndex = 0;
    userAnswers  = [];
    $('quiz-splash').style.display    = 'none';
    $('quiz-question').style.display  = 'block';
    $('quiz-results').style.display   = 'none';
    renderQuestion(0);
  }

  // ── Question rendering ─────────────────────────────────────
  function renderQuestion(idx) {
    const q      = QUIZ_DATA[idx];
    const total  = QUIZ_DATA.length;

    // Progress bar
    const pct = Math.round((idx / total) * 100);
    $('quiz-progress-bar').style.width = pct + '%';

    // Counter
    $('quiz-counter').textContent = `Question ${idx + 1} of ${total}`;

    // Question text
    $('quiz-q-text').textContent = q.text;

    // Clear previous state
    $('quiz-options').innerHTML   = '';
    $('quiz-explanation').style.display = 'none';
    $('quiz-explanation').innerHTML = '';
    $('quiz-next').disabled = true;
    $('quiz-next').textContent = idx === total - 1 ? 'See Results' : 'Next';

    // Render options
    if (q.type === 'truefalse') {
      [['True', true], ['False', false]].forEach(([label, val]) => {
        const btn = makeOptionBtn(label, val, q.type);
        $('quiz-options').appendChild(btn);
      });
    } else {
      q.options.forEach((opt, i) => {
        const btn = makeOptionBtn(opt, i, q.type);
        $('quiz-options').appendChild(btn);
      });
    }
  }

  function makeOptionBtn(label, value, type) {
    const btn = document.createElement('button');
    btn.className = 'quiz-option';
    btn.textContent = label;
    btn.dataset.value = JSON.stringify(value);
    btn.addEventListener('click', () => onOptionClick(btn, type));
    return btn;
  }

  function onOptionClick(btn, type) {
    const optionBtns = $('quiz-options').querySelectorAll('.quiz-option');

    if (type === 'multi') {
      btn.classList.toggle('selected');
    } else {
      // single / truefalse — deselect others
      optionBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    }

    const anySelected = [...optionBtns].some(b => b.classList.contains('selected'));
    $('quiz-next').disabled = !anySelected;
  }

  // ── Next / submit ──────────────────────────────────────────
  $('quiz-next').addEventListener('click', onNext);

  function onNext() {
    const q      = QUIZ_DATA[currentIndex];
    const optionBtns = [...$('quiz-options').querySelectorAll('.quiz-option')];
    const selected   = optionBtns
      .filter(b => b.classList.contains('selected'))
      .map(b => JSON.parse(b.dataset.value));

    userAnswers.push(selected);

    // Reveal correct/wrong states
    markOptions(optionBtns, q);

    // Show inline explanation only when the answer is wrong
    const answeredCorrectly = isCorrect(q, selected);
    if (SHOW_INLINE && q.explanation && !answeredCorrectly) {
      const box = $('quiz-explanation');
      box.innerHTML = '<strong>💡 Explanation:</strong> ' + escapeHtml(q.explanation);
      box.style.display = 'block';
    }

    // Disable all options
    optionBtns.forEach(b => b.disabled = true);

    // Change button to advance
    const isLast = currentIndex === QUIZ_DATA.length - 1;
    $('quiz-next').disabled = false;
    $('quiz-next').textContent = isLast ? 'See Results' : 'Next →';
    $('quiz-next').removeEventListener('click', onNext);
    $('quiz-next').addEventListener('click', isLast ? showResults : advanceQuestion, { once: true });
    $('quiz-next').addEventListener('click', onNext); // re-attach for future questions handled below
  }

  // Simpler approach — track state with a flag
  let waitingForAdvance = false;

  $('quiz-next').removeEventListener('click', onNext); // clear
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
      box.innerHTML = '<strong>💡 Explanation:</strong> ' + escapeHtml(q.explanation);
      box.style.display = 'block';
    }

    // Disable all options
    optionBtns.forEach(b => b.disabled = true);

    const isLast = currentIndex === QUIZ_DATA.length - 1;
    $('quiz-next').disabled = false;
    $('quiz-next').textContent = isLast ? 'See Results' : 'Next →';
    waitingForAdvance = true;
  }

  function markOptions(btns, q) {
    const correct = Array.isArray(q.answer) ? q.answer : [q.answer];

    btns.forEach(btn => {
      const val = JSON.parse(btn.dataset.value);
      const isCorrectOption = correct.some(c => JSON.stringify(c) === JSON.stringify(val));
      const wasSelected     = btn.classList.contains('selected');

      btn.classList.remove('selected');

      if (isCorrectOption && wasSelected)  btn.classList.add('option-correct');
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

    QUIZ_DATA.forEach((q, i) => {
      if (isCorrect(q, userAnswers[i])) score++;
    });

    const pct = Math.round((score / total) * 100);

    // Score label in chart hole
    $('quiz-score-label').textContent = pct + '%';
    $('quiz-score-text').textContent  = `${score} out of ${total} correct — ${
      pct >= 80 ? 'Excellent! 🏆' : pct >= 60 ? 'Good effort! 👍' : 'Keep practising! 💪'
    }`;

    // Chart
    new Chart($('quiz-chart'), {
      type: 'doughnut',
      data: {
        labels: ['Correct', 'Incorrect'],
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

    // Breakdown
    const bd = $('quiz-breakdown');
    bd.innerHTML = '<h3 class="quiz-breakdown__title">Question Breakdown</h3>';

    QUIZ_DATA.forEach((q, i) => {
      const correct = isCorrect(q, userAnswers[i]);
      const card    = document.createElement('div');
      card.className = 'quiz-bd-card ' + (correct ? 'quiz-bd-card--correct' : 'quiz-bd-card--wrong');

      const icon    = correct ? '✅' : '❌';
      const userAns = formatAnswer(q, userAnswers[i]);
      const corrAns = formatAnswer(q, normaliseAnswer(q.answer));

      let html = `<div class="quiz-bd-top">${icon} <span class="quiz-bd-q">${escapeHtml(q.text)}</span></div>`;
      html    += `<div class="quiz-bd-detail">`;
      html    += `<span class="quiz-bd-label">Your answer:</span> <span class="${correct ? 'quiz-ans-correct' : 'quiz-ans-wrong'}">${escapeHtml(userAns)}</span>`;
      if (!correct) {
        html  += `<br><span class="quiz-bd-label">Correct answer:</span> <span class="quiz-ans-correct">${escapeHtml(corrAns)}</span>`;
      }
      html    += `</div>`;
      if (q.explanation) {
        html  += `<div class="quiz-bd-explanation">${escapeHtml(q.explanation)}</div>`;
      }

      card.innerHTML = html;
      bd.appendChild(card);
    });

    // Send to Google Sheets
    sendToSheets(score, total);
  }

  function isCorrect(q, selected) {
    if (!selected || selected.length === 0) return false;
    const correct = normaliseAnswer(q.answer);
    return JSON.stringify([...selected].sort((a,b)=>JSON.stringify(a)<JSON.stringify(b)?-1:1)) ===
           JSON.stringify([...correct].sort((a,b)=>JSON.stringify(a)<JSON.stringify(b)?-1:1));
  }

  function normaliseAnswer(answer) {
    return Array.isArray(answer) ? answer : [answer];
  }

  function formatAnswer(q, values) {
    if (!values || values.length === 0) return '(no answer)';
    if (q.type === 'truefalse') return values[0] ? 'True' : 'False';
    return values.map(v => {
      if (typeof v === 'number' && q.options) return q.options[v] || v;
      return v;
    }).join(', ');
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Google Sheets submission ────────────────────────────────
  function sendToSheets(score, total) {
    if (!QUIZ_CONFIG || !QUIZ_CONFIG.action) return;
    try {
      fetch(QUIZ_CONFIG.action, {
        method: 'POST',
        mode: 'no-cors',
        body: new URLSearchParams({
          [QUIZ_CONFIG.fields.name]:       playerName,
          [QUIZ_CONFIG.fields.quiz_title]: QUIZ_TITLE,
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
