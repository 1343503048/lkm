---
layout: default
title: 首页
---

# Linux 内核调度子系统 LKML 日报

每日自动分析 LKML 中 `kernel/sched/*` 相关邮件，按 patch 系列聚合，
识别 bug、跟踪合入进展，生成结构化摘要报告。

---

## 日报索引

{% assign posts_by_date = site.posts | group_by_exp: "p: p.date | date: '%Y-%m-%d'" %}
{% for group in posts_by_date %}
### {{ group.name }} ({{ group.items | size }} 篇)

{% for post in group.items %}
- [{{ post.title }}]({{ post.url | relative_url }}) `{{ post.type }}/{{ post.status }}`
{% endfor %}

{% endfor %}

---

*共 {{ site.posts | size }} 篇文章*
