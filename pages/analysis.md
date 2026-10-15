---
layout: default
title: 深度分析
permalink: /analysis/
---

<div class="ana-page">
  <div class="hero">
    <h1>深度分析</h1>
    <p class="hero-desc">超越日报粒度的整场深析：周期性补丁梳理、技术论坛议题、顶会论文</p>
    <div class="stats-bar">
      <div class="stat"><span class="stat-num">{{ site.data.analyses.entries | size }}</span><span class="stat-label">篇分析</span></div>
      {% for c in site.data.analyses.categories %}
      {% assign n = site.data.analyses.entries | where: "category", c.id | size %}
      <div class="stat"><span class="stat-num">{{ n }}</span><span class="stat-label">{{ c.name }}</span></div>
      {% endfor %}
    </div>
  </div>

  {% for c in site.data.analyses.categories %}
  {% assign cat_entries = site.data.analyses.entries | where: "category", c.id | sort: "date" | reverse %}
  <section class="ana-section" id="{{ c.id }}">
    <div class="ana-section-head ana-{{ c.id }}">
      <div class="ana-section-title">
        <h2>{{ c.name }}</h2>
        <p>{{ c.desc }}</p>
      </div>
      {% if c.more %}
      <a class="ana-more" href="{{ c.more.url | relative_url }}">{{ c.more.label }} →</a>
      {% endif %}
    </div>
    {% if cat_entries.size > 0 %}
    <div class="ana-grid">
      {% for e in cat_entries %}
      <a class="ana-card ana-{{ c.id }}" href="{{ e.url | relative_url }}">
        <div class="ana-card-top">
          <span class="ana-date">{{ e.date }}</span>
          <span class="ana-cat-badge">{{ c.name }}</span>
        </div>
        <h3>{{ e.title }}</h3>
        <p class="ana-note">{{ e.note }}</p>
        <span class="ana-go">阅读全文 →</span>
      </a>
      {% endfor %}
    </div>
    {% else %}
    <div class="ana-empty">
      <p>暂无整场分析。</p>
      {% if c.more %}
      <a href="{{ c.more.url | relative_url }}">{{ c.more.label }} →</a>
      {% endif %}
    </div>
    {% endif %}
  </section>
  {% endfor %}
</div>
