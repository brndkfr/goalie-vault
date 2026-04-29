---
layout: default
title: Programs
description: "Structured training programs for floorball goalies."
---

<div class="vault-main">
  <div class="vault-hero">
    <h1 class="vault-hero__title">Programs</h1>
    <p class="vault-hero__sub">Structured goalie training</p>
  </div>

  <div class="quiz-grid">
    {% for article in site.articles %}
    <a class="quiz-card" href="{{ site.baseurl }}{{ article.url }}">
      <div class="quiz-card__thumb quiz-card__thumb--placeholder">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#00f2ff" stroke-width="1.5">
          <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>
      </div>
      <div class="quiz-card__body">
        {% if article.phases %}<span class="quiz-card__count">{{ article.phases.size }} phases</span>{% endif %}
        <h2 class="quiz-card__title">{{ article.title }}</h2>
        {% if article.description %}
          <p class="quiz-card__desc">{{ article.description.de }}</p>
        {% endif %}
      </div>
    </a>
    {% endfor %}
  </div>
</div>
