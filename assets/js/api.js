/* ============================================================
   GOALIE VAULT — Static REST API Fetcher
   Base URL is injected by Jekyll via the global BASE_URL constant
   (defined in _layouts/default.html and quiz.html as a <script> block).
   ============================================================ */

const GoalieAPI = (function () {
  'use strict';

  // BASE_URL is expected to be defined globally by the Jekyll layout,
  // e.g.: <script>const BASE_URL = "{{ site.baseurl }}";</script>
  const base = (typeof BASE_URL !== 'undefined' ? BASE_URL : '') + '/api/v1';

  /**
   * Fetch all drills (full schema).
   * @returns {Promise<Array>}
   */
  function fetchAll() {
    return fetch(base + '/all.json').then(r => {
      if (!r.ok) throw new Error('GoalieAPI: failed to fetch all.json (' + r.status + ')');
      return r.json();
    });
  }

  /**
   * Fetch drills for a single category.
   * @param {string} category - e.g. "warmup", "strength", "goal-technical"
   * @returns {Promise<Array>}
   */
  function fetchCategory(category) {
    return fetch(base + '/categories/' + encodeURIComponent(category) + '.json').then(r => {
      if (!r.ok) throw new Error('GoalieAPI: failed to fetch category "' + category + '" (' + r.status + ')');
      return r.json();
    });
  }

  /**
   * Fetch lightweight search index (title, category, url only).
   * @returns {Promise<Array>}
   */
  function fetchSearch() {
    return fetch(base + '/search.json').then(r => {
      if (!r.ok) throw new Error('GoalieAPI: failed to fetch search.json (' + r.status + ')');
      return r.json();
    });
  }

  return { fetchAll, fetchCategory, fetchSearch };
})();

/*
  ── Usage examples ───────────────────────────────────────────

  // Load every drill:
  GoalieAPI.fetchAll().then(drills => console.log(drills));

  // Load only warmup drills:
  GoalieAPI.fetchCategory('warmup').then(drills => console.log(drills));

  // Power a search bar:
  GoalieAPI.fetchSearch().then(index => {
    const query = 'reaction';
    const results = index.filter(d =>
      d.title.toLowerCase().includes(query) ||
      d.category.includes(query)
    );
    console.log(results);
  });
*/
