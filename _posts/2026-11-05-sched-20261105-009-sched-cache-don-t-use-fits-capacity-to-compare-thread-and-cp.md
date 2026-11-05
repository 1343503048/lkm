---
id: sched-20261105-009
date: 2026-11-05
subject: 'sched/cache: Don''t use fits_capacity() to compare thread and CPU counts'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261104020954.2388172-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/all/20261104020954.2388172-1-zhanxusheng1024@gmail.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20261102021536.1026143-1-zhanxusheng1024@gmail.com>
  date: 2026-11-02
  summary: 抽 fits_llc_nr() 防 Qais 系列改 fits_capacity 第二参数时静默误传。
  review_outcome: 暂无 review。
- version: v2
  msgid: <20261104020954.2388172-1-zhanxusheng1024@gmail.com>
  date: 2026-11-04
  summary: v2 具体 diff 未获取到；Kayra 确认等价并给 Reviewed-by。
  review_outcome: Kayra Cizmeci Reviewed-by。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 是否保留 20% margin 需 Tim Chen/Chen Yu 定
  next_action: 作者就 margin 去留给实测或立场，等 Tim Chen/Chen Yu 确认
contribution_opportunities:
- kind: review
  description: 确认 fits_llc_nr 与 get_sched_cache_scale 的 INT_MAX bail 交互仍成立
- kind: discussion
  description: 就 20% margin 去留给出聚合行为实测依据
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261102-006
tags:
- cfs
- topology
title: 'sched/cache: Don''t use fits_capacity() to compare thread and CPU counts'
layout: article
---

## TL;DR

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-006-sched-cache-don-t-use-fits-capacity-to-compare-thread-and-cp.html">sched-20261102-006</a>：Zhan Xusheng 把 `invalid_llc_nr()` 对 `fits_capacity()` 的误用（「线程数 vs CPU 数」只借其 20% margin）抽成独立 helper `fits_llc_nr()`（`x*5 < y*4`，与旧 `x*1280 < y*1024` 严格等价），以防 Qais 的 capacity-aware 系列把 `fits_capacity()` 第二参数改成「CPU 编号」时静默误传。
- sched-20261105（今天）：作者发出 v2，Kayra Cizmeci 评审后给 `Reviewed-by`（对其中「magic of 256」的写法确认「两者行为等价」）。

## 背景与问题

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-006-sched-cache-don-t-use-fits-capacity-to-compare-thread-and-cp.html">sched-20261102-006</a>：`invalid_llc_nr()` 用 `fits_capacity()` 比较线程数与 CPU 数，只为借 20% margin；Qais Yousef 的 capacity-aware 系列将把 `fits_capacity()` 第二参数改为 CPU 编号，届时该调用会把 CPU 数当 CPU 编号传入却不告警。作者同时指出 `llc_aggr_tolerance` 已在缩放 LLC 大小，这个 margin 也许可以去掉。

今天的新进展：v2（msgid 20261104020954.2388172-1）已发，Kayra 评审回复确认其中「magic of 256」相关的比较「behave the same」并给出 `Reviewed-by`。v2 相对 v1 的具体 diff 未获取到（当日缓存仅含 Kayra 的评审回复，不含 v2 补丁正文）。

## 技术方案

- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-006-sched-cache-don-t-use-fits-capacity-to-compare-thread-and-cp.html">sched-20261102-006</a>：新增 `fits_llc_nr(nr_threads, nr_cpus)`，`nr_threads * 5 < (u64)nr_cpus * 4`，`invalid_llc_nr()` 改调用之，无功能变化；是否进一步删掉 margin 需 Tim/Chen Yu 拍板。
- 今天：Kayra 确认 v2 中「magic of 256」写法的等价性，无功能语义变化。

## 版本演进与当前进展

*current_version: v2*。v1（11-02）为初版 helper 抽取，暂无 review；v2（11-04 发出）今日获 Kayra Cizmeci `Reviewed-by`。仍未到维护者（Tim Chen / Chen Yu）的 margin 去留定论。

## Maintainer 意见与讨论焦点

无调度维护者直接表态；Kayra Cizmeci 给 `Reviewed-by`。跨线程的实质分歧仍是：Qais 不希望再出现新的 magic number user（倾向删 margin），而是否删 margin 会改变聚合停止时机，需 Tim Chen / Chen Yu 拍板——这一分歧今日未解决。

## 合入评估

*likelihood=medium*。已获一名 reviewer 的 `Reviewed-by`，方向（防静默误传）无争议；但 margin 去留未定、且尚无维护者 Acked。*blocking_issues*：① 是否保留 20% margin 仍需 Tim/Chen Yu 定；② 与 Qais capacity-aware 系列的入列顺序未明。*next_action*：作者就 margin 去留给出实测或明确立场，等待 Tim Chen / Chen Yu 确认。

## 效果评估

无功能变化（等价重写），无性能数据。

## 我可以参与的点

- review：确认 `fits_llc_nr` 与 `get_sched_cache_scale()` 的 INT_MAX 提前 bail 交互（scale≤99 论证）在 v2 中仍成立。
- discussion：就「是否保留 20% margin」给出实测（聚合行为何时变化）依据。

## 参考链接

- lore thread（v2 补丁）: https://lore.kernel.org/all/20261104020954.2388172-1-zhanxusheng1024@gmail.com/
- Kayra 的 Reviewed-by 回帖: https://lore.kernel.org/all/aut98iS5gqInpZ2-@scheduler.schedules/
