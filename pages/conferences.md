---
layout: default
title: 论文笔记
permalink: /conferences/
---

<div class="conf-page">
  <div class="hero">
    <h1>论文笔记</h1>
    <p class="hero-desc">会议与论文分析 · LPC / OSDI / OSPM / LSFMM …</p>
    <div class="stats-bar">
      <div class="stat"><span class="stat-num">{{ site.conferences | size }}</span><span class="stat-label">篇分析</span></div>
      {% assign conf_names = '' | split: '' %}
      {% for c in site.conferences %}
        {% unless conf_names contains c.conf %}{% assign conf_names = conf_names | push: c.conf %}{% endunless %}
      {% endfor %}
      <div class="stat"><span class="stat-num">{{ conf_names | size }}</span><span class="stat-label">个会议</span></div>
    </div>
  </div>

  <div class="filter-bar">
    <div class="filter-group">
      <label>会议:</label>
      <select id="cf-conf">
        <option value="">全部</option>
        {% assign sorted_confs = conf_names | sort %}
        {% for cn in sorted_confs %}<option value="{{ cn }}">{{ cn }}</option>{% endfor %}
      </select>
    </div>
    <div class="filter-group">
      <label>年份:</label>
      <select id="cf-year">
        <option value="">全部</option>
        {% assign conf_years = '' | split: '' %}
        {% for c in site.conferences %}
          {% assign ystr = c.year | append: '' %}
          {% unless conf_years contains ystr %}{% assign conf_years = conf_years | push: ystr %}{% endunless %}
        {% endfor %}
        {% assign conf_years = conf_years | sort | reverse %}
        {% for y in conf_years %}<option value="{{ y }}">{{ y }}</option>{% endfor %}
      </select>
    </div>
    <div class="filter-group">
      <label>方向:</label>
      <select id="cf-dir">
        <option value="">全部</option>
        {% assign conf_dirs = '' | split: '' %}
        {% for c in site.conferences %}
          {% if c.direction %}
          {% unless conf_dirs contains c.direction %}{% assign conf_dirs = conf_dirs | push: c.direction %}{% endunless %}
          {% endif %}
        {% endfor %}
        {% assign sorted_dirs = conf_dirs | sort %}
        {% for d in sorted_dirs %}
        {% case d %}
        {% when 'sched' %}{% assign dlabel = '调度' %}
        {% when 'mm' %}{% assign dlabel = '内存' %}
        {% when 'perf' %}{% assign dlabel = '性能' %}
        {% when 'android' %}{% assign dlabel = 'Android' %}
        {% when 'arch' %}{% assign dlabel = '体系结构' %}
        {% when 'mixed' %}{% assign dlabel = '总览' %}
        {% else %}{% assign dlabel = d %}{% endcase %}
        <option value="{{ d }}">{{ dlabel }}</option>
        {% endfor %}
      </select>
    </div>
    <button class="btn-reset" id="cf-reset">重置</button>
    <span class="filter-count" id="cf-count"></span>
  </div>

  <div class="conf-list" id="conf-list">
    {% assign groups = '' | split: '' %}
    {% for c in site.conferences %}
      {% assign ystr = c.year | append: '' %}
      {% assign gkey = ystr | append: '|' | append: c.conf %}
      {% unless groups contains gkey %}{% assign groups = groups | push: gkey %}{% endunless %}
    {% endfor %}
    {% assign groups = groups | sort | reverse %}
    {% for gkey in groups %}
      {% assign g_year = gkey | split: '|' | first %}
      {% assign g_conf = gkey | split: '|' | last %}
      <div class="conf-group" data-conf="{{ g_conf }}" data-year="{{ g_year }}">
        <h2 class="date-header">{{ g_conf }} {{ g_year }}</h2>
        {% for a in site.conferences %}
          {% assign ay = a.year | append: '' %}
          {% if a.conf == g_conf and ay == g_year %}
          <div class="article-card conf-card" data-conf="{{ a.conf }}" data-year="{{ ay }}" data-direction="{{ a.direction }}">
            <h3 class="card-title"><a href="{{ a.url | relative_url }}">{{ a.title }}</a></h3>
            <div class="card-badges">
              <span class="badge conf-{{ a.conf | downcase | replace: ' ', '_' }}">{{ a.conf }} {{ ay }}</span>
              <span class="badge dir-{{ a.direction }}">{{ a.direction }}</span>
              {% if a.overview %}<span class="badge overview-badge">总览</span>{% endif %}
              {% if a.source_type %}<span class="badge source-{{ a.source_type }}">{{ a.source_type }}</span>{% endif %}
              <span class="card-date">{{ a.date | date: "%Y-%m-%d" }}</span>
            </div>
            {% if a.speakers %}
            <div class="card-authors">{{ a.speakers | join: ', ' }}</div>
            {% endif %}
            {% if a.tldr %}
            <div class="card-authors">{{ a.tldr }}</div>
            {% endif %}
            {% if a.tags %}
            <div class="card-tags">
              {% for tag in a.tags limit:5 %}
              <a href="{{ '/pages/tags/' | append: tag | replace: '/', '_' | append: '.html' | relative_url }}" class="tag-link">{{ tag | replace: '_', ' ' }}</a>
              {% endfor %}
            </div>
            {% endif %}
          </div>
          {% endif %}
        {% endfor %}
      </div>
    {% endfor %}
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  var fConf = document.getElementById('cf-conf');
  var fYear = document.getElementById('cf-year');
  var fDir = document.getElementById('cf-dir');
  var resetBtn = document.getElementById('cf-reset');
  var countEl = document.getElementById('cf-count');
  if (!fConf) return;

  function apply() {
    var c = fConf.value, y = fYear.value, d = fDir.value;
    var total = 0;
    document.querySelectorAll('.conf-group').forEach(function(g) {
      var n = 0;
      g.querySelectorAll('.conf-card').forEach(function(card) {
        var ok = (!c || card.dataset.conf === c) &&
                 (!y || card.dataset.year === y) &&
                 (!d || card.dataset.direction === d);
        card.style.display = ok ? '' : 'none';
        if (ok) n++;
      });
      g.style.display = n ? '' : 'none';
      total += n;
    });
    if (countEl) countEl.textContent = '共 ' + total + ' 篇';
  }

  [fConf, fYear, fDir].forEach(function(el) { el.addEventListener('change', apply); });
  if (resetBtn) resetBtn.addEventListener('click', function() {
    fConf.value = ''; fYear.value = ''; fDir.value = '';
    apply();
  });
  apply();
});
</script>
