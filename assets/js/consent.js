/**
 * Hybrid embed-consent flow.
 *
 * - Site banner sets a global `vault-consent` flag (`allow` | `deny`).
 * - When `allow` -> any `.embed-slot` on the page is auto-activated on load.
 * - When `deny` (or unset) -> placeholders stay; user can click each one
 *   individually to load that single embed without changing the global flag.
 * - Footer "Privacy choices" link clears the flag and shows the banner again.
 *
 * Flag storage: localStorage (persists across sessions and tabs).
 */
(function () {
  'use strict';
  var KEY = 'vault-consent';

  function getConsent() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setConsent(value) {
    try { localStorage.setItem(KEY, value); } catch (e) { /* ignore */ }
  }
  function clearConsent() {
    try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ }
  }

  // ---- Embed activation ----
  var igScriptInjected = false;

  function activate(slot) {
    if (slot.dataset.activated === '1') return;
    var platform = slot.dataset.platform;
    var videoId = slot.dataset.videoId;
    if (!videoId) return;
    if (platform === 'youtube') {
      slot.innerHTML =
        '<div class="video-wrapper video-wrapper--youtube">' +
          '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(videoId) +
            '?autoplay=1" allowfullscreen ' +
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">' +
          '</iframe>' +
        '</div>';
    } else if (platform === 'instagram') {
      slot.innerHTML =
        '<div class="video-wrapper video-wrapper--instagram">' +
          '<blockquote class="instagram-media" ' +
            'data-instgrm-permalink="https://www.instagram.com/p/' + encodeURIComponent(videoId) + '/" ' +
            'data-instgrm-version="14"></blockquote>' +
        '</div>';
      if (!igScriptInjected) {
        var s = document.createElement('script');
        s.src = 'https://www.instagram.com/embed.js';
        s.async = true;
        document.body.appendChild(s);
        igScriptInjected = true;
      } else if (window.instgrm && window.instgrm.Embeds) {
        window.instgrm.Embeds.process();
      }
    }
    slot.dataset.activated = '1';
  }

  function activateAll() {
    document.querySelectorAll('.embed-slot').forEach(activate);
  }

  function wirePlaceholderClicks() {
    document.querySelectorAll('.embed-slot__btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var slot = btn.closest('.embed-slot');
        if (slot) activate(slot);
      });
    });
  }

  // ---- Banner ----
  function showBanner() {
    var banner = document.getElementById('consent-banner');
    if (banner) banner.hidden = false;
  }
  function hideBanner() {
    var banner = document.getElementById('consent-banner');
    if (banner) banner.hidden = true;
  }
  function wireBanner() {
    var banner = document.getElementById('consent-banner');
    if (!banner) return;
    banner.querySelectorAll('[data-consent-action]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var action = btn.dataset.consentAction;
        setConsent(action === 'allow' ? 'allow' : 'deny');
        hideBanner();
        if (action === 'allow') activateAll();
      });
    });
  }
  function wireRevoke() {
    document.querySelectorAll('[data-consent-revoke]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        clearConsent();
        showBanner();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    wireBanner();
    wireRevoke();
    wirePlaceholderClicks();
    var c = getConsent();
    if (c === 'allow') {
      activateAll();
    } else if (c === 'deny') {
      // keep placeholders, banner stays hidden
    } else {
      showBanner();
    }
  });
})();
