---
layout: default
title: 标签总览
permalink: /pages/tags.html
---

<div class="tag-page">
  <h1>标签总览</h1>
  <p class="hero-desc">按标签浏览所有文章</p>
  
  <div class="tags-cloud">
    {% assign sorted_tags = site.tags | sort %}
    {% for tag in sorted_tags %}
    <a href="{{ '/pages/tags/' | append: tag[0] | replace: '/', '_' | append: '.html' | relative_url }}" class="tag-link">
      {{ tag[0] }} <span class="tag-count">({{ tag[1] | size }})</span>
    </a>
    {% endfor %}
  </div>
</div>
