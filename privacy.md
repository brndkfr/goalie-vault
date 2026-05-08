---
layout: default
title: Privacy & Contact
permalink: /privacy/
---

<div class="legal-page">

<h1>Privacy &amp; Contact</h1>

<p><em>Last updated: {{ "now" | date: "%B %Y" }}</em></p>

<h2>1. Who runs this site</h2>

<p>
  Goalie Vault is a non-commercial hobby project operated by
  <strong>brndkfr</strong> (<a href="https://github.com/brndkfr" rel="noopener">github.com/brndkfr</a>).
  No company, no advertising, no paid services.
</p>

<h2>2. Contact</h2>

<p>
  For privacy questions, takedown requests, or anything else related to this site:
</p>

<p class="legal-email">
  <a id="contact-link" href="#" rel="noopener">
    <span id="contact-text">goalie-vault [at] outlook [dot] com</span>
  </a>
</p>

<noscript>
  <p>Email: <code>goalie-vault&#64;outlook&#46;com</code></p>
</noscript>

<script>
  (function () {
    var u = 'goalie-vault', d = 'outlook.com';
    var addr = u + '@' + d;
    var link = document.getElementById('contact-link');
    var text = document.getElementById('contact-text');
    if (link && text) {
      link.href = 'mailto:' + addr;
      text.textContent = addr;
    }
  })();
</script>

<h2>3. Hosting</h2>

<p>
  This site is hosted on <strong>GitHub Pages</strong> (GitHub, Inc., USA).
  GitHub processes server logs (including the visitor's IP address and
  user-agent) for the purpose of operating the service and protecting against
  abuse. See
  <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener" target="_blank">GitHub's privacy statement</a>
  for details. We do not have access to these logs.
</p>

<h2>4. Embedded videos (Instagram &amp; YouTube)</h2>

<p>
  Drill pages embed short videos hosted on Instagram (Meta Platforms Ireland Ltd.)
  and YouTube (Google Ireland Ltd.). Loading such an embed transmits your
  IP address and may set cookies in your browser through those providers.
</p>

<p>
  To prevent this from happening without your choice, embeds are
  <strong>not loaded by default</strong>. Instead a placeholder is shown.
  You can:
</p>

<ul>
  <li>Use the consent banner shown on first visit to either allow or deny
    embeds globally for this site, or</li>
  <li>Click an individual placeholder to load only that single video.</li>
</ul>

<p>
  Your choice is stored in your browser's <code>localStorage</code> under the
  key <code>vault-consent</code>. Nothing is transmitted to us. You can change
  the choice at any time via the
  <a href="#" data-consent-revoke>Privacy choices</a> link in the footer.
</p>

<p>
  Once you load an embed, the privacy practices of Meta and Google apply.
  YouTube embeds use the <code>youtube-nocookie.com</code> domain, which
  reduces (but does not eliminate) tracking.
</p>

<h2>5. Thumbnail images</h2>

<p>
  Some preview thumbnails are loaded directly from Instagram's CDN
  (<code>cdninstagram.com</code>). This transmits your IP address to Meta
  even before you click an embed. We are working on caching these on our
  own host; until then, blocking <code>cdninstagram.com</code> in your
  browser will prevent the requests at the cost of missing previews.
</p>

<h2>6. What we do not do</h2>

<ul>
  <li>No analytics (no Google Analytics, no Plausible, no Matomo, nothing).</li>
  <li>No advertising and no advertising trackers.</li>
  <li>No newsletter and no account system &mdash; we do not collect names
    or email addresses from visitors.</li>
  <li>No first-party cookies are set by this site.</li>
</ul>

<h2>7. Content authors and handles</h2>

<p>
  Each drill page credits the original creator with their public social-media
  handle (e.g. <code>@example</code>) and links to their public profile. This
  information is sourced from the public post itself. If you are an author and
  would like your name, handle, or video removed, write to the contact address
  above and it will be taken down.
</p>

<h2>8. Your rights</h2>

<p>
  Under the Swiss Federal Act on Data Protection (revFADP) and, where
  applicable, the EU General Data Protection Regulation (GDPR), you have the
  right to:
</p>

<ul>
  <li>Request information about any personal data we hold about you,</li>
  <li>Request correction or deletion,</li>
  <li>Object to processing,</li>
  <li>Lodge a complaint with the Swiss Federal Data Protection and
    Information Commissioner (FDPIC) or, for EU residents, your national
    data protection authority.</li>
</ul>

<p>
  Since we collect no visitor data ourselves, most of these rights apply to
  data held by GitHub, Meta, or Google &mdash; please contact them directly
  for those. For anything you find on this site that concerns you, write to
  the contact address above.
</p>

<h2>9. Content removal / takedown</h2>

<p>
  If you appear in or own a video embedded here and want it removed, please
  email the contact address with:
</p>

<ul>
  <li>The URL of the page on this site, and</li>
  <li>A short note about why you are requesting removal.</li>
</ul>

<p>
  We aim to remove the post within a few days. No formal legal notice is
  required &mdash; a polite email is enough.
</p>

<h2>10. Jurisdiction</h2>

<p>
  Goalie Vault is operated from Switzerland. Swiss law applies.
</p>

</div>
