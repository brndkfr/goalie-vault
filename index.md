---
layout: default
title: "Goalie Vault"
---

<div class="vault-main">

  <!-- Hero -->
  <div class="vault-hero">
    <h1 class="vault-hero__title">Goalie Vault</h1>
  </div>

  <!-- Filter & search toolbar -->
  <div class="vault-toolbar" markdown="0">
    <div class="filter-bar" id="filterBar">
      <button class="filter-btn filter-btn--all active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="technique">Technique</button>
      <button class="filter-btn" data-filter="coordination">Coordination</button>
      <button class="filter-btn" data-filter="movement">Movement</button>
      <button class="filter-btn" data-filter="reaction">Reaction</button>
      <button class="filter-btn" data-filter="strength">Strength</button>
      <button class="filter-btn" data-filter="stretching">Stretching</button>
      <button class="filter-btn" data-filter="mobility">Mobility</button>
      <button class="filter-btn" data-filter="warmup">Warmup</button>
      <button class="filter-btn" data-filter="theory">Theory</button>
      <button type="button" class="filter-btn filter-btn--more" id="moreFiltersBtn" aria-expanded="false" aria-controls="moreFiltersPanel">
        <span class="more-label">More</span><span class="more-count" id="moreCount" hidden></span><span class="more-caret" aria-hidden="true">▾</span>
      </button>
    </div>

    <div class="filter-panel" id="moreFiltersPanel" hidden>
      <div class="filter-panel__group">
        <div class="filter-panel__label">Sub-skill</div>
        <div class="filter-panel__buttons">
          <button class="filter-btn" data-filter="hand-eye">Hand-Eye</button>
          <button class="filter-btn" data-filter="juggling">Juggling</button>
          <button class="filter-btn" data-filter="vision">Vision</button>
          <button class="filter-btn" data-filter="footwork">Footwork</button>
          <button class="filter-btn" data-filter="positioning">Positioning</button>
          <button class="filter-btn" data-filter="rebound-control">Rebound Control</button>
          <button class="filter-btn" data-filter="mental">Mental</button>
        </div>
      </div>
      <div class="filter-panel__group">
        <div class="filter-panel__label">Context</div>
        <div class="filter-panel__buttons">
          <button class="filter-btn" data-filter="game-situation">Game Situation</button>
          <button class="filter-btn" data-filter="match-prep">Match Prep</button>
          <button class="filter-btn" data-filter="injury-recovery">Injury Recovery</button>
        </div>
      </div>
      <div class="filter-panel__group">
        <div class="filter-panel__label">Equipment</div>
        <div class="filter-panel__buttons">
          <button class="filter-btn" data-filter="medicine-ball">Medicine Ball</button>
          <button class="filter-btn" data-filter="tennis-ball">Tennis Ball</button>
          <button class="filter-btn" data-filter="band">Band</button>
          <button class="filter-btn" data-filter="slideboard">Slideboard</button>
          <button class="filter-btn" data-filter="fitlight">Reaction Lights</button>
          <button class="filter-btn" data-filter="brock-string">Brock String</button>
        </div>
      </div>
    </div>

    <div class="search-bar">
      <span class="search-icon" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      </span>
      <input type="search"
             id="drillSearch"
             class="search-input"
             placeholder="Search drills…"
             autocomplete="off"
             aria-label="Search drills">
      <button type="button" id="drillSearchClear" class="search-clear" aria-label="Clear search" hidden>&times;</button>
    </div>
  </div>

  <!-- Active filter chips -->
  <div class="active-filters" id="activeFilters" hidden>
    <span class="active-filters__label">Active:</span>
    <div class="active-filters__chips" id="activeFiltersChips"></div>
    <button type="button" class="active-filters__clear" id="activeFiltersClear">Clear all</button>
  </div>

  <!-- Drill grid -->
  <div class="drill-grid" id="drillGrid">
    {% for post in site.posts %}
    {% capture post_filters %}{{ post.category }}{% if post.tags %},{{ post.tags | join: ',' }}{% endif %}{% endcapture %}
    <div class="drill-card"
         data-categories="{{ post_filters | downcase }}"
         data-title="{{ post.title | downcase | escape }}"
         data-author="{{ post.author | downcase | escape }}"
         data-handle="{{ post.handle | downcase | escape }}">
      <a class="drill-card__link" href="{{ site.baseurl }}{{ post.url }}">

        {% assign thumb_data = site.data.thumbnails[post.video_id] %}
        {% if thumb_data and thumb_data.url and thumb_data.status != "not_found" %}
          <img class="drill-card__thumb"
               src="{{ thumb_data.url }}"
               alt="{{ post.title }}"
               loading="lazy"
               referrerpolicy="no-referrer"
               onerror="this.parentNode.replaceChild(window.__vaultIgPlaceholder.cloneNode(true), this);">
        {% elsif post.thumbnail and post.thumbnail != "" and post.thumbnail != "skip" %}
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
          {% if post.category or post.tags %}
          <div class="drill-card__tags">
            {% if post.category %}<a class="drill-card__tag drill-card__tag--primary" href="{{ site.baseurl }}/{{ post.category }}/" onclick="event.stopPropagation();">{{ post.category }}</a>{% endif %}
            {% for tag in post.tags %}
              <a class="drill-card__tag" href="{{ site.baseurl }}/{{ tag }}/" onclick="event.stopPropagation();">{{ tag }}</a>
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
    var moreBtn = document.getElementById('moreFiltersBtn');
    var morePanel = document.getElementById('moreFiltersPanel');
    var moreCount = document.getElementById('moreCount');
    var catBtns = document.querySelectorAll('.filter-btn[data-filter]:not([data-filter="all"])');
    var cards = document.querySelectorAll('.drill-card');
    var none  = document.getElementById('noResults');
    var search = document.getElementById('drillSearch');
    var searchClear = document.getElementById('drillSearchClear');
    var activeBar = document.getElementById('activeFilters');
    var activeChips = document.getElementById('activeFiltersChips');
    var activeClear = document.getElementById('activeFiltersClear');
    var searchTerm = '';

    // Build a quick lookup: filter slug -> button label (for chip text).
    var labelOf = {};
    catBtns.forEach(function (b) {
      labelOf[b.dataset.filter] = b.textContent.trim();
    });
    // Filters in the "More" panel (so we can show a count badge).
    var moreFilters = {};
    morePanel.querySelectorAll('.filter-btn[data-filter]').forEach(function (b) {
      moreFilters[b.dataset.filter] = true;
    });

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

    function renderActiveChips(active) {
      activeChips.innerHTML = '';
      if (active.length === 0) {
        activeBar.hidden = true;
        return;
      }
      activeBar.hidden = false;
      active.forEach(function (slug) {
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'active-chip';
        chip.dataset.filter = slug;
        chip.innerHTML = '<span>' + (labelOf[slug] || slug) + '</span><span class="active-chip__x" aria-hidden="true">×</span>';
        chip.setAttribute('aria-label', 'Remove filter ' + (labelOf[slug] || slug));
        chip.addEventListener('click', function () {
          var btn = document.querySelector('.filter-btn[data-filter="' + slug + '"]');
          if (btn) btn.classList.remove('active');
          applyFilters();
        });
        activeChips.appendChild(chip);
      });
    }

    function updateMoreCount(active) {
      var n = 0;
      active.forEach(function (f) { if (moreFilters[f]) n++; });
      if (n > 0) {
        moreCount.textContent = n;
        moreCount.hidden = false;
      } else {
        moreCount.hidden = true;
      }
    }

    function applyFilters() {
      var active = getActiveFilters();
      var showAll = active.length === 0;

      allBtn.classList.toggle('active', showAll);
      renderActiveChips(active);
      updateMoreCount(active);

      var visible = 0;
      cards.forEach(function (card) {
        var cats = (card.dataset.categories || '').split(',').map(function (s) { return s.trim(); });
        var catOk = showAll || active.every(function (f) { return cats.indexOf(f) !== -1; });
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

    // Active-chip "Clear all"
    activeClear.addEventListener('click', function () {
      catBtns.forEach(function (b) { b.classList.remove('active'); });
      applyFilters();
    });

    // More-filters toggle (panel) + remember in localStorage
    function setMoreOpen(open) {
      morePanel.hidden = !open;
      moreBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      moreBtn.classList.toggle('is-open', open);
      try { localStorage.setItem('vault.moreOpen', open ? '1' : '0'); } catch (e) {}
    }
    moreBtn.addEventListener('click', function () {
      setMoreOpen(morePanel.hidden);
    });
    try {
      if (localStorage.getItem('vault.moreOpen') === '1') setMoreOpen(true);
    } catch (e) {}

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
