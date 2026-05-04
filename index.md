---
layout: default
title: "Goalie Vault"
---

<div class="vault-main">

  <!-- Hero -->
  <div class="vault-hero">
    <h1 class="vault-hero__title">Goalie Vault</h1>
  </div>

  <!-- Filter bar -->
  <div class="filter-bar" id="filterBar">
    <button class="filter-btn active" data-filter="all">All</button>
    <a class="filter-btn" href="{{ site.baseurl }}/warmup/">Warmup</a>
    <a class="filter-btn" href="{{ site.baseurl }}/coordination/">Coordination</a>
    <a class="filter-btn" href="{{ site.baseurl }}/strength/">Strength</a>
    <a class="filter-btn" href="{{ site.baseurl }}/stretching/">Stretching</a>
    <a class="filter-btn" href="{{ site.baseurl }}/goal-technical/">Goal Technical</a>
    <a class="filter-btn" href="{{ site.baseurl }}/reaction/">Reaction</a>
    <a class="filter-btn" href="{{ site.baseurl }}/movement/">Movement</a>
    <a class="filter-btn" href="{{ site.baseurl }}/theory/">Theory</a>
  </div>

  <!-- Drill grid -->
  <div class="drill-grid" id="drillGrid">
    {% for post in site.posts %}
    <div class="drill-card" data-categories="{{ post.category | join: ',' | downcase }}">
      <a class="drill-card__link" href="{{ site.baseurl }}{{ post.url }}">

        {% if post.thumbnail and post.thumbnail != "" and post.thumbnail != "skip" %}
          {% if post.thumbnail contains "://" %}
            {% assign thumb_src = post.thumbnail %}
          {% else %}
            {% capture thumb_src %}{{ site.baseurl }}{{ post.thumbnail }}{% endcapture %}
          {% endif %}
          <img class="drill-card__thumb"
               src="{{ thumb_src }}"
               alt="{{ post.title }}"
               loading="lazy">
        {% elsif post.platform == "youtube" %}
          <img class="drill-card__thumb"
               src="https://img.youtube.com/vi/{{ post.video_id }}/mqdefault.jpg"
               alt="{{ post.title }}"
               loading="lazy">
        {% else %}
          <div class="drill-card__thumb drill-card__thumb--ig">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
          </div>
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
