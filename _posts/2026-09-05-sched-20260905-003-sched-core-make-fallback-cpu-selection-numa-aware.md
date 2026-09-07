---
id: sched-20260905-003
date: '2026-09-05'
subject: 'sched/core: Make fallback CPU selection NUMA-aware'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/core+Make+fallback+CPU+selection+NUMA-aware
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Yury Norov
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
- sched/core
- numa_balancing
- topology
title: 'sched/core: Make fallback CPU selection NUMA-aware'
layout: article
---

## TL;DR

select_fallback_rq() 先查本地节点，再按任务亲和性掩码的数值顺序扫描。目前作者 Yury Norov（NVIDIA），本日首次出现（新系列）。- 关注点：多 NUMA 节点下的 fallback 局部性。

## 背景与问题

`select_fallback_rq()` 先查本地节点，再按任务亲和性掩码的数值顺序扫描。在超过两个 NUMA 节点的系统上，可能选中比必要更远（跨更多 hop）的 CPU。本补丁改为遍历调度器的 NUMA hop 掩码，每次只考察新到达的 CPU，在整段 fallback 搜索中保持 locality；并在亲和性放宽后保持同样顺序。

## 技术方案

- 用 NUMA hop 掩码驱动 fallback 选择，保留 locality。
- 拓扑重建期间 hop 掩码可能不可用/不完整，此时在放宽亲和性前先扫描掩码未覆盖的在线 CPU，保证该窗口内 fallback 仍可靠。

## 版本演进与当前进展

- 作者 Yury Norov（NVIDIA），本日首次出现（新系列）。
- 关注点：多 NUMA 节点下的 fallback 局部性；拓扑重建过渡期的健壮性。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关代码/commit：
  - `kernel/sched/core.c` `select_fallback_rq()`
