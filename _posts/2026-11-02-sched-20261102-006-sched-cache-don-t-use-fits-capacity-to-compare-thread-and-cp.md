---
type: fix
status: under_review
severity: none
thread_root_msgid: <20261102021536.1026143-1-zhanxusheng1024@gmail.com>
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261102021536.1026143-1-zhanxusheng1024@gmail.com>
  date: '2026-11-02'
  summary: 抽出 fits_llc_nr() helper，避免误用 fits_capacity() 比较线程/CPU 数，保持 20% margin
  review_outcome: 暂无直接 review；Qais 在相邻线程认可拆分方向
merge_assessment:
  likelihood: medium
  blocking_issues:
  - margin 去留未定，需 Tim Chen/Chen Yu 拍板
  next_action: 等 Tim/Chen Yu 决定是否删 margin，并与 Qais fits_capacity 系列对齐
contribution_opportunities:
- kind: review
  description: 核对 fits_llc_nr 与 get_sched_cache_scale() 的溢出/scale bail 交互
- kind: discussion
  description: 提供 20% margin 去留的实测依据
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
- topology
id: sched-20261102-006
subject: 'sched/cache: Don''t use fits_capacity() to compare thread and CPU counts'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched/cache: Don''t use fits_capacity() to compare thread and CPU counts'
layout: article
---

## TL;DR

Zhan Xusheng 把 cache-aware 调度里 `invalid_llc_nr()` 对 `fits_capacity()` 的误用（用「线程数 vs CPU 数」比较却只为借它 20% 的 margin）抽成独立 helper `fits_llc_nr()`（`x*5 < y*4`，与旧的 `x*1280 < y*1024` 严格等价），无功能变化。动机是 Qais Yousef 的 series 会把 `fits_capacity()` 第二参数改成「CPU 编号」，届时该调用会静默把 CPU 数当 CPU 编号传入。作者也抛给 Tim/Chen Yu：是否直接去掉这 20% margin。

## 背景与问题

`invalid_llc_nr()` 用 `fits_capacity()` 比较「线程数」与「CPU 数」，只是借用其 20% margin。Qais Yousef 的 capacity-aware 系列（lore 20260504020003.71306-5-qyousef@layalina.io）将把 `fits_capacity()` 的第二参数改为 CPU 编号——此调用会把「CPU 数」当「CPU 编号」传进去却不告警，属于静默绑定错误。作者顺手指出 `llc_aggr_tolerance` 已在缩放 LLC 大小，这个 margin 也许可以去掉（Qais 也不希望再引入硬编码 margin）。

## 技术方案

新增 `fits_llc_nr(nr_threads, nr_cpus)`：`nr_threads * 5 < (u64)nr_cpus * 4`（等价于旧 `x*1280 < y*1024`）。`invalid_llc_nr()` 改调用它，无功能变化。作者注：要不要进一步删掉 margin 会改变聚合停止的时机，需 Tim/Chen Yu 拍板。

## 版本演进与当前进展

v1 刚发出（2026-11-02），暂无 review。同日 Qais 在另一封（`sched/fair: Remove magic hardcoded margin in fits_capacity()`）里对此表示「happy to split，但不想看到新的 magic number 用户」，可见两封有直接联动。

## Maintainer 意见与讨论焦点

无维护者直接回本文；Qais（原作者）在相邻线程表达了「认同拆分方向、反对继续引入 magic margin」的立场（见同窗口 fits_capacity 文章）。

## 合入评估

likelihood=medium。作为 Qais fits_capacity 系列的前置/协作补丁，方向被原作者接受，但 margin 去留未定、需 Tim Chen/Chen Yu 确认。

## 效果评估

无功能变化，无性能数据；作者说明 `x*5 < y*4` 与旧比较严格等价。

## 我可以参与的点

- review：确认 `fits_llc_nr` 与 `get_sched_cache_scale()` 的 INT_MAX 提前 bail 交互（scale≤99 论证）仍成立。
- discussion：就「是否保留 20% margin」给出实测（聚合行为何时变化）依据。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102021536.1026143-1-zhanxusheng1024@gmail.com/
