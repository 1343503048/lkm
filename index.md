---
layout: default
title: 首页
---

<div class="hero">
  <h1>Linux 内核调度子系统 LKML 日报</h1>
  <p class="hero-desc">每日自动分析 LKML 中 kernel/sched/* 相关邮件</p>
  <div class="stats-bar">
    <div class="stat"><span class="stat-num">{{ site.posts | size }}</span><span class="stat-label">篇文章</span></div>
    <div class="stat"><span class="stat-num">{{ site.tags | size }}</span><span class="stat-label">个标签</span></div>
  </div>
</div>

<div class="filter-bar">
  <div class="filter-group">
    <label>类型:</label>
    <select id="filter-type">
      <option value="">全部</option>
      <option value="bug">bug</option>
      <option value="fix">fix</option>
      <option value="feature">feature</option>
      <option value="discussion">discussion</option>
      <option value="cleanup">cleanup</option>
      <option value="docs">docs</option>
    </select>
  </div>
  <div class="filter-group">
    <label>状态:</label>
    <select id="filter-status">
      <option value="">全部</option>
      <option value="under_review">under review</option>
      <option value="merged_tip">merged (tip)</option>
      <option value="merged_stable">merged (stable)</option>
      <option value="stalled">stalled</option>
      <option value="superseded">superseded</option>
      <option value="rfc">rfc</option>
    </select>
  </div>
  <button class="btn-reset" id="filter-reset">重置</button>
</div>

<div class="article-list" id="article-list">
{% assign current_date = '' %}
{% for post in site.posts %}
  {% assign post_date = post.date | date: '%Y-%m-%d' %}
  {% if post_date != current_date %}
    {% unless current_date == '' %}
    </div>
    {% endunless %}
    {% assign current_date = post_date %}
    <div class="date-group">
    <h3 class="date-header">{{ current_date }}</h3>
  {% endif %}
  <div class="article-card" data-type="{{ post.type }}" data-status="{{ post.status }}">
    <div class="card-header">
      <span class="badge type-{{ post.type }}">{{ post.type }}</span>
      <span class="badge status-{{ post.status }}">{{ post.status | replace: '_', ' ' }}</span>
      {% if post.severity and post.severity != 'none' %}
      <span class="badge severity-{{ post.severity }}">{{ post.severity }}</span>
      {% endif %}
    </div>
    <h4 class="card-title"><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h4>
    <div class="card-meta">
      {% if post.authors %}<span>{{ post.authors | join: ', ' }}</span>{% endif %}
      {% if post.current_version %}<span>{{ post.current_version }}</span>{% endif %}
    </div>
    {% if post.tags %}
    <div class="card-tags">
      {% for tag in post.tags limit:5 %}
      <a href="{{ '/pages/tags/' | append: tag | replace: '/', '_' | append: '.html' | relative_url }}" class="tag-link">{{ tag }}</a>
      {% endfor %}
    </div>
    {% endif %}
  </div>
{% endfor %}
{% unless current_date == '' %}
</div>
{% endunless %}
</div>
