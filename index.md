---
layout: default
title: "Goalie Vault"
---

<div class="vault-main">

  <!-- Hero -->
  <div class="vault-hero">
    <img class="vault-hero__logo" src="{{ site.baseurl }}/assets/images/logo.jpg" alt="Goalie Vault">
    <h1 class="vault-hero__title">Goalie Vault</h1>
    <p class="vault-hero__sub">by brndkfr</p>
  </div>

  <!-- Filter bar -->
  <div class="filter-bar" id="filterBar">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="warmup">Warmup</button>
    <button class="filter-btn" data-filter="coordination">Coordination</button>
    <button class="filter-btn" data-filter="strength">Strength</button>
    <button class="filter-btn" data-filter="goal-technical">Goal Technical</button>
    <button class="filter-btn" data-filter="reaction">Reaction</button>
    <button class="filter-btn" data-filter="movement">Movement</button>
    <button class="filter-btn" data-filter="theory">Theory</button>
  </div>

  <!-- Drill grid -->
  <div class="drill-grid" id="drillGrid">
    {% for post in site.posts %}
    <div class="drill-card" data-categories="{{ post.category | join: ',' | downcase }}">
      <a class="drill-card__link" href="{{ site.baseurl }}{{ post.url }}">

        {% if post.platform == "youtube" %}
          <img class="drill-card__thumb"
               src="https://img.youtube.com/vi/{{ post.video_id }}/mqdefault.jpg"
               alt="{{ post.title }}"
               loading="lazy">
        {% else %}
          <div class="drill-card__thumb drill-card__thumb--ig">📸</div>
        {% endif %}

        <div class="drill-card__body">
          {% if post.category %}
          <div class="drill-card__tags">
            {% for cat in post.category %}
              <span class="drill-card__tag">{{ cat }}</span>
            {% endfor %}
          </div>
          {% endif %}
          <div class="drill-card__title">{{ post.title }}</div>
          <div class="drill-card__meta">
            {{ post.author }}{% if post.handle %} &middot; @{{ post.handle }}{% endif %}
          </div>
        </div>

      </a>
    </div>
    {% endfor %}
  </div>

  <div class="no-results" id="noResults">No drills found for this category.</div>

</div>

<script>
  (function () {
    var btns  = document.querySelectorAll('.filter-btn');
    var cards = document.querySelectorAll('.drill-card');
    var none  = document.getElementById('noResults');

    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var filter = btn.dataset.filter;

        // toggle active btn
        btns.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');

        var visible = 0;
        cards.forEach(function (card) {
          var cats = card.dataset.categories || '';
          if (filter === 'all' || cats.split(',').indexOf(filter) !== -1) {
            card.classList.remove('hidden');
            visible++;
          } else {
            card.classList.add('hidden');
          }
        });

        none.classList.toggle('visible', visible === 0);
      });
    });
  })();
</script>


<div style="text-align: center; padding: 30px 10px; background: #1a1a1a; border-radius: 0 0 30px 30px; margin: -20px -20px 20px -20px;">
  <img src="{{ site.baseurl }}/assets/images/logo.jpg" alt="Goalie Vault Logo" style="width: 140px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">
  
  <!-- 
    <h1 style="color: #ffffff; margin-top: 15px; font-size: 2rem;">Goalie Vault</h1>
    <p style="color: #00d4ff; font-weight: bold; letter-spacing: 1px;">BY BRNDKFR</p>
  -->
  
<div style="display: grid; gap: 15px; padding: 10px;">
  
  <a href="{{ site.baseurl }}/warmup" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🏋️ WARMUPS
  </a>

  <a href="{{ site.baseurl }}/coordination" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🧤 COORDINATION
  </a>

  <a href="{{ site.baseurl }}/training" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🥅  TRAINING
  </a>

  <a href="{{ site.baseurl }}/articles" style="display: flex; align-items: center; justify-content: center; background: #333; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    📖 THEORY & GEAR
  </a>

</div>

<hr style="margin: 40px 0; border: 0; border-top: 2px solid #eee;">

<h2 style="padding-left: 10px; color: #333;">Latest Additions</h2>
<div style="padding: 10px;">
  {% for post in site.posts limit:5 %}
    <div style="margin-bottom: 15px; background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
      <a href="{{ site.baseurl }}{{ post.url }}" style="text-decoration: none; display: block; padding: 15px;">
        <span style="color: #00d4ff; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">{{ post.category }}</span>
        <h3 style="margin: 5px 0; color: #222; font-size: 1.1rem;">{{ post.title }}</h3>
        <p style="margin: 0; color: #666; font-size: 0.9rem;">{{ post.description | truncate: 80 }}</p>
      </a>
    </div>
  {% endfor %}