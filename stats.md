---
layout: default
title: Site stats
permalink: /stats/
noindex: true
---

<style>
  .stats { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; color: var(--color-text, #e8e8e8); }
  .stats h1 { margin: 0 0 4px; font-size: 1.8rem; }
  .stats .stats__sub { color: #999; font-size: 0.9rem; margin-bottom: 24px; }
  .stats__kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 28px; }
  .kpi { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px 16px; }
  .kpi__label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: #aaa; }
  .kpi__value { font-size: 1.6rem; font-weight: 800; margin-top: 4px; }
  .kpi__hint { font-size: 0.75rem; color: #888; margin-top: 2px; }
  .stats__grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
  @media (min-width: 900px) { .stats__grid { grid-template-columns: 1fr 1fr; } }
  .panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 16px; }
  .panel h2 { margin: 0 0 12px; font-size: 1.05rem; }
  .panel canvas { width: 100% !important; height: 240px !important; }
  .stats__tables { display: grid; grid-template-columns: 1fr; gap: 24px; margin-top: 24px; }
  @media (min-width: 900px) { .stats__tables { grid-template-columns: 1fr 1fr; } }
  table.stats-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  table.stats-table th, table.stats-table td { padding: 8px 6px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); }
  table.stats-table th { color: #aaa; font-weight: 600; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; }
  table.stats-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
  table.stats-table a { color: var(--color-accent, #00f2ff); text-decoration: none; }
  table.stats-table a:hover { text-decoration: underline; }
  .stats__empty { padding: 24px; text-align: center; color: #888; background: rgba(255,255,255,0.03); border-radius: 10px; }
</style>

<div class="stats">
  <h1>Site stats</h1>
  {% assign meta = site.data.traffic.meta %}
  <div class="stats__sub">
    {% if meta %}
      Last updated <strong>{{ meta.last_run }}</strong> &middot; source: GitHub Traffic API for <code>{{ meta.repo }}</code>
    {% else %}
      No data collected yet. The daily workflow will populate this page once it runs.
    {% endif %}
  </div>

  {% if meta %}
    {% comment %} ---- KPIs computed from CSV files ---- {% endcomment %}
    {% assign views_csv = site.data.traffic.views %}
    {% assign clones_csv = site.data.traffic.clones %}

    {% assign total_views = 0 %}
    {% assign total_uniques_views = 0 %}
    {% for r in views_csv %}
      {% assign total_views = total_views | plus: r.views %}
      {% assign total_uniques_views = total_uniques_views | plus: r.uniques %}
    {% endfor %}

    {% assign total_clones = 0 %}
    {% assign total_uniques_clones = 0 %}
    {% for r in clones_csv %}
      {% assign total_clones = total_clones | plus: r.clones %}
      {% assign total_uniques_clones = total_uniques_clones | plus: r.uniques %}
    {% endfor %}

    <div class="stats__kpis">
      <div class="kpi">
        <div class="kpi__label">Total views</div>
        <div class="kpi__value">{{ total_views }}</div>
        <div class="kpi__hint">{{ views_csv | size }} days tracked</div>
      </div>
      <div class="kpi">
        <div class="kpi__label">Unique visitors</div>
        <div class="kpi__value">{{ total_uniques_views }}</div>
        <div class="kpi__hint">sum of daily uniques</div>
      </div>
      <div class="kpi">
        <div class="kpi__label">Total clones</div>
        <div class="kpi__value">{{ total_clones }}</div>
        <div class="kpi__hint">{{ clones_csv | size }} days tracked</div>
      </div>
      <div class="kpi">
        <div class="kpi__label">Unique cloners</div>
        <div class="kpi__value">{{ total_uniques_clones }}</div>
        <div class="kpi__hint">sum of daily uniques</div>
      </div>
    </div>

    <div class="stats__grid">
      <div class="panel">
        <h2>Page views</h2>
        <canvas id="viewsChart"></canvas>
      </div>
      <div class="panel">
        <h2>Git clones</h2>
        <canvas id="clonesChart"></canvas>
      </div>
    </div>

    {% comment %} ---- latest snapshots ---- {% endcomment %}
    {% assign paths_keys = site.data.traffic.paths | sort %}
    {% assign refs_keys = site.data.traffic.referrers | sort %}
    {% assign latest_paths_key = paths_keys | last %}
    {% assign latest_refs_key = refs_keys | last %}
    {% assign latest_paths = site.data.traffic.paths[latest_paths_key] %}
    {% assign latest_refs = site.data.traffic.referrers[latest_refs_key] %}

    <div class="stats__tables">
      <div class="panel">
        <h2>Top paths (last 14d, snapshot {{ latest_paths_key }})</h2>
        {% if latest_paths and latest_paths.size > 0 %}
          <table class="stats-table">
            <thead><tr><th>Path</th><th class="num">Views</th><th class="num">Uniques</th></tr></thead>
            <tbody>
              {% for p in latest_paths %}
              <tr>
                <td><a href="{{ p.path }}">{{ p.title | default: p.path }}</a></td>
                <td class="num">{{ p.count }}</td>
                <td class="num">{{ p.uniques }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <div class="stats__empty">No path data yet.</div>
        {% endif %}
      </div>
      <div class="panel">
        <h2>Top referrers (last 14d, snapshot {{ latest_refs_key }})</h2>
        {% if latest_refs and latest_refs.size > 0 %}
          <table class="stats-table">
            <thead><tr><th>Referrer</th><th class="num">Views</th><th class="num">Uniques</th></tr></thead>
            <tbody>
              {% for r in latest_refs %}
              <tr>
                <td>{{ r.referrer }}</td>
                <td class="num">{{ r.count }}</td>
                <td class="num">{{ r.uniques }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        {% else %}
          <div class="stats__empty">No referrer data yet.</div>
        {% endif %}
      </div>
    </div>

    <script id="viewsData" type="application/json">[{% for r in views_csv %}{"date":"{{ r.date }}","views":{{ r.views }},"uniques":{{ r.uniques }}}{% unless forloop.last %},{% endunless %}{% endfor %}]</script>
    <script id="clonesData" type="application/json">[{% for r in clones_csv %}{"date":"{{ r.date }}","clones":{{ r.clones }},"uniques":{{ r.uniques }}}{% unless forloop.last %},{% endunless %}{% endfor %}]</script>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"
            integrity="sha384-JUh163oCRItcbPme8pYnROHQMC6fNKTBWtRG3I3I0erJkzNgL7uxKlNwcrcFKeqF"
            crossorigin="anonymous"></script>
    <script>
      (function () {
        if (typeof Chart === 'undefined') return;
        var common = {
          type: 'line',
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
              x: { ticks: { color: '#aaa' }, grid: { color: 'rgba(255,255,255,0.05)' } },
              y: { beginAtZero: true, ticks: { color: '#aaa', precision: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            plugins: { legend: { labels: { color: '#ddd' } } }
          }
        };
        function build(canvasId, dataId, primaryKey, primaryLabel) {
          var el = document.getElementById(canvasId);
          if (!el) return;
          var raw = JSON.parse(document.getElementById(dataId).textContent || '[]');
          if (!raw.length) return;
          new Chart(el.getContext('2d'), Object.assign({}, common, {
            data: {
              labels: raw.map(function (r) { return r.date; }),
              datasets: [
                { label: primaryLabel, data: raw.map(function (r) { return r[primaryKey]; }),
                  borderColor: '#00f2ff', backgroundColor: 'rgba(0,242,255,0.15)', tension: 0.25, fill: true },
                { label: 'Uniques', data: raw.map(function (r) { return r.uniques; }),
                  borderColor: '#ff6ec7', backgroundColor: 'rgba(255,110,199,0.10)', tension: 0.25, fill: false, borderDash: [4, 4] }
              ]
            }
          }));
        }
        build('viewsChart', 'viewsData', 'views', 'Views');
        build('clonesChart', 'clonesData', 'clones', 'Clones');
      })();
    </script>
  {% endif %}
</div>
