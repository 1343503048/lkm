# sched/fair: Honor asymmetric SMT priority in idle selection

## TL;DR

SD_ASYM_PACKING 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。目前作者 Andrea Righi，本日收到复审（Re），询问是否针对特定 SMT 实现（如 Olympus/Vera、Power7）。

## 背景与问题

`SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。

## 技术方案

- 空闲选择路径考虑 `SD_ASYM_PACKING` 顺序，优先把唤醒任务放到更优的 SMT 兄弟线程，减少后续负载均衡的纠正成本。

## 版本演进与当前进展

- 作者 Andrea Righi，本日收到复审（Re），询问是否针对特定 SMT 实现（如 Olympus/Vera、Power7）。
- 属拓扑/亲和性相关的唤醒放置优化。

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
  - `kernel/sched/fair.c` `select_idle_sibling()` / `SD_ASYM_PACKING` 处理

---
id: sched-20260903-009
date: '2026-09-03'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/fair+Honor+asymmetric+SMT+priority+in+idle+selection
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Dietmar Eggemann
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 3
related_articles: []
tags:
- sched/fair
- topology
- affinity
---
