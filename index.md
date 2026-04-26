---
layout: default
title: "Goalie Vault Home"
---

<div style="text-align: center; padding: 30px 10px; background: #1a1a1a; border-radius: 0 0 30px 30px; margin: -20px -20px 20px -20px;">
  <img src="{{ site.baseurl }}/assets/images/logo.png" alt="Goalie Vault Logo" style="width: 140px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">
  <h1 style="color: #ffffff; margin-top: 15px; font-size: 2rem;">Goalie Vault</h1>
  <p style="color: #00d4ff; font-weight: bold; letter-spacing: 1px;">BY BRNDKFR</p>
</div>

<div style="display: grid; gap: 15px; padding: 10px;">
  
  <a href="{{ site.baseurl }}/warmup" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🥅 WARMUPS
  </a>

  <a href="{{ site.baseurl }}/coordination" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🎾 COORDINATION
  </a>

  <a href="{{ site.baseurl }}/training" style="display: flex; align-items: center; justify-content: center; background: #00d4ff; color: white; padding: 25px; border-radius: 15px; text-decoration: none; font-weight: 800; font-size: 1.3rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    🏋️ TRAINING
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