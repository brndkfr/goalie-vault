---
layout: default
title: Quizzes
description: "Test your floorball goalie knowledge with these quizzes."
---

<div class="vault-main">
  <div class="vault-hero">
    <h1 class="vault-hero__title">Quizzes</h1>
    <p class="vault-hero__sub">Test your goalie knowledge</p>
  </div>

  <div class="quiz-grid">
    {% for quiz in site.quizzes %}
    <a class="quiz-card" href="{{ site.baseurl }}{{ quiz.url }}">
      {% assign quiz_title = quiz.title.en | default: quiz.title %}
      {% assign quiz_desc  = quiz.description.en | default: quiz.description %}
      {% if quiz.cover_image and quiz.cover_image != "" %}
        <img class="quiz-card__thumb" src="{{ quiz.cover_image }}" alt="{{ quiz_title }}" loading="lazy">
      {% else %}
        <div class="quiz-card__thumb quiz-card__thumb--placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#00f2ff" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
      {% endif %}
      <div class="quiz-card__body">
        <span class="quiz-card__count">{{ quiz.questions.size }} questions</span>
        <h2 class="quiz-card__title">{{ quiz_title }}</h2>
        {% if quiz_desc %}
          <p class="quiz-card__desc">{{ quiz_desc }}</p>
        {% endif %}
      </div>
    </a>
    {% endfor %}
  </div>
</div>
