---
layout: default
title: 首页
---

<div class="home-layout">
  <div class="home-list-panel">
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
      <div class="filter-group">
        <label>排序:</label>
        <select id="filter-sort">
          <option value="date-desc">最新优先</option>
          <option value="severity">严重度优先</option>
        </select>
      </div>
      <button class="btn-reset" id="filter-reset">重置</button>
      <span class="filter-count" id="filter-count"></span>
    </div>

    <div class="article-list" id="article-list">
    {% assign current_date = '' %}
    {% assign day_index = 0 %}
    {% assign recent_days = 3 %}
    {% for post in site.posts %}
      {% assign post_date = post.date | date: '%Y-%m-%d' %}
      {% if post_date != current_date %}
        {% unless current_date == '' %}
        </div>
        {% endunless %}
        {% assign current_date = post_date %}
        {% assign day_index = day_index | plus: 1 %}
        {% if day_index <= recent_days %}
        <div class="date-group date-group-expanded" data-date="{{ current_date }}">
        {% else %}
        <div class="date-group date-group-collapsed" data-date="{{ current_date }}">
        {% endif %}
        <h2 class="date-header">{{ current_date }}</h2>
      {% endif %}
      <div class="article-card" data-type="{{ post.type }}" data-status="{{ post.status }}" data-severity="{{ post.severity }}" data-article-id="{{ post.id | slugify }}">
        <h3 class="card-title"><a href="{{ post.url | relative_url }}" data-url="{{ post.url | relative_url }}" class="article-link">{{ post.title }}</a></h3>
        <div class="card-badges">
          <span class="badge type-{{ post.type }}">{{ post.type }}</span>
          <span class="badge status-{{ post.status }}">{{ post.status | replace: '_', ' ' }}</span>
          {% if post.severity and post.severity != 'none' %}
          <span class="badge severity-{{ post.severity }}">{{ post.severity }}</span>
          {% endif %}
          {% if post.current_version %}<span class="badge version-badge">{{ post.current_version }}</span>{% endif %}
          <span class="card-date">{{ post.date | date: "%m-%d" }}</span>
        </div>
        {% if post.authors %}
        <div class="card-authors">{{ post.authors | join: ', ' }}</div>
        {% endif %}
        {% if post.tags %}
        <div class="card-tags">
          {% for tag in post.tags limit:5 %}
          <a href="{{ '/pages/tags/' | append: tag | replace: '/', '_' | append: '.html' | relative_url }}" class="tag-link">{{ tag | replace: '_', ' ' }}</a>
          {% endfor %}
        </div>
        {% endif %}
      </div>
    {% endfor %}
    {% unless current_date == '' %}
    </div>
    {% endunless %}
    </div>

    {% assign total_days = day_index %}
    {% if total_days > recent_days %}
    <div class="show-more-bar">
      <button class="btn-show-more" id="btn-show-all">展开全部 {{ total_days }} 天</button>
    </div>
    {% endif %}
  </div>

  <div class="home-read-panel" id="read-panel">
    <div class="read-placeholder">
      <div class="placeholder-icon"></div>
      <p>点击左侧文章卡片开始阅读</p>
    </div>
  </div>
</div>
