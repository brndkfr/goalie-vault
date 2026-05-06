---
layout: default
title: "Goalie Vault"
---

<div class="vault-main">

  <!-- Hero -->
  <div class="vault-hero">
    <h1 class="vault-hero__title">Goalie Vault</h1>
  </div>

  <!-- Filter bar (multi-select: toggle any combination) -->
  <div class="filter-bar" id="filterBar">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="warmup">Warmup</button>
    <button class="filter-btn" data-filter="coordination">Coordination</button>
    <button class="filter-btn" data-filter="strength">Strength</button>
    <button class="filter-btn" data-filter="stretching">Stretching</button>
    <button class="filter-btn" data-filter="goal-technical">Goal Technical</button>
    <button class="filter-btn" data-filter="reaction">Reaction</button>
    <button class="filter-btn" data-filter="movement">Movement</button>
    <button class="filter-btn" data-filter="theory">Theory</button>
  </div>

  <!-- Search bar -->
  <div class="search-bar">
    <input type="search"
           id="drillSearch"
           class="search-input"
           placeholder="Search drills by title, author, or tag…"
           autocomplete="off"
           aria-label="Search drills">
    <button type="button" id="drillSearchClear" class="search-clear" aria-label="Clear search" hidden>&times;</button>
  </div>

  <!-- Drill grid -->
  <div class="drill-grid" id="drillGrid">
    {% for post in site.posts %}
    <div class="drill-card"
         data-categories="{{ post.category | join: ',' | downcase }}"
         data-title="{{ post.title | downcase | escape }}"
         data-author="{{ post.author | downcase | escape }}"
         data-handle="{{ post.handle | downcase | escape }}">
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
              <a class="drill-card__tag" href="{{ site.baseurl }}/{{ cat }}/" onclick="event.stopPropagation();">{{ cat }}</a>
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
    var allBtn = document.querySelector('.filter-btn[data-filter="all"]');
    var catBtns = document.querySelectorAll('.filter-btn:not([data-filter="all"])');
    var cards = document.querySelectorAll('.drill-card');
    var none  = document.getElementById('noResults');
    var search = document.getElementById('drillSearch');
    var searchClear = document.getElementById('drillSearchClear');
    var searchTerm = '';

    function getActiveFilters() {
      var active = [];
      catBtns.forEach(function (b) {
        if (b.classList.contains('active')) active.push(b.dataset.filter);
      });
      return active;
    }

    function cardMatchesSearch(card, term) {
      if (!term) return true;
      var hay = (card.dataset.title || '') + ' ' +
                (card.dataset.author || '') + ' ' +
                (card.dataset.handle || '') + ' ' +
                (card.dataset.categories || '');
      return hay.indexOf(term) !== -1;
    }

    function applyFilters() {
      var active = getActiveFilters();
      var showAll = active.length === 0;

      // sync "All" button state
      allBtn.classList.toggle('active', showAll);

      var visible = 0;
      cards.forEach(function (card) {
        var cats = (card.dataset.categories || '').split(',');
        var catOk = showAll || active.some(function (f) { return cats.indexOf(f) !== -1; });
        var searchOk = cardMatchesSearch(card, searchTerm);
        if (catOk && searchOk) {
          card.classList.remove('hidden');
          visible++;
        } else {
          card.classList.add('hidden');
        }
      });
      none.classList.toggle('visible', visible === 0);
    }

    // "All" resets everything
    allBtn.addEventListener('click', function () {
      catBtns.forEach(function (b) { b.classList.remove('active'); });
      applyFilters();
    });

    // Category buttons toggle on/off
    catBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btn.classList.toggle('active');
        allBtn.classList.remove('active');
        applyFilters();
      });
    });

    // Search input (debounced)
    var searchTimer = null;
    function onSearchInput() {
      searchTerm = search.value.trim().toLowerCase();
      searchClear.hidden = searchTerm.length === 0;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(applyFilters, 120);
    }
    if (search) {
      search.addEventListener('input', onSearchInput);
      search.addEventListener('search', onSearchInput);
    }
    if (searchClear) {
      searchClear.addEventListener('click', function () {
        search.value = '';
        searchTerm = '';
        searchClear.hidden = true;
        applyFilters();
        search.focus();
      });
    }
  })();
</script>
