---
id: sched-20260728-002
date: 2026-07-28
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260725005019.1297049-1-tj@kernel.org>
lore_url: https://lore.kernel.org/r/20260725005019.1297049-1-tj@kernel.org
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20260725005019.1297049-2-tj@kernel.org>
  date: 2026-07-25
  summary: 'Make exit claiming lock-free: split synchronous ->aborting sweep (RCU)
    from deferred exit_kind claim (irq_work)'
  review_outcome: Andrea Righi 给出 Reviewed-by
- version: v2
  msgid: <684ed36923a4f388b8be726cfbfc5154@kernel.org>
  date: 2026-07-28
  summary: patch 1/5 的 v2 修订版
  review_outcome: Tejun 确认 applied 1-5 到 sched_ext/for-7.3
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 sched_ext/for-7.3，等待 7.3 合并窗口
contribution_opportunities: []
generated_at: '2026-07-30T10:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Make exit claiming lock-free'
layout: article
---

## TL;DR

Tejun Heo 的 5-patch 系列让 sched_ext 的 exit claiming 变为 lock-free 且 NMI-safe，已合入 sched_ext/for-7.3 分支。这解决了 BPF kfunc 在 NMI 中触发 scx_error() 时死锁的问题。

## 背景与问题

`scx_claim_exit()` 此前在 `scx_sched_lock` 下遍历子树做 exit claiming，导致：
1. NMI 中无法调用 `scx_error()`（NMI-attached BPF prog 中的 kfunc 可能触发错误）
2. hardlockup handler 运行在 NMI 中，无法安全报错
3. `scx_link_sched()` 在持锁状态下无法报告失败

## 技术方案

将 exit claiming 拆分为两个不同紧迫度的操作：

1. **同步部分**（必须立即完成）：在 RCU 保护下 lockless 扫描 `->aborting` 标志，打破 IRQs-off dispatch-path 的活锁
2. **延迟部分**（可以稍后完成）：通过 irq_work 延迟执行 `SCX_EXIT_PARENT` 的 exit_kind claim

两侧通过 full barrier 配对：sweep 先存 `->aborting` 再读 children list；`scx_link_sched()` 先 insert 再检查 parent 的 `->aborting`——保证一方总能看见另一方的操作。

新增 `sch->linked` 字段替代 `list_empty()` 判断（因为 undo 的 `list_del_rcu()` 会让 `->sibling` 非空）。

## 版本演进与当前进展

- v1（2026-07-25）：首次发出 5-patch 系列
- v2（2026-07-28）：patch 1/5 修订
- 2026-07-28：Tejun 确认 "Applied 1-5 (1 in its v2 form) to sched_ext/for-7.3 with Andrea's Reviewed-by added"

## Maintainer 意见与讨论焦点

- Andrea Righi 给出 Reviewed-by（针对新 patch 1/5）
- Tejun 作为 sched_ext maintainer 直接 apply，无争议

## 合入评估

已合入 `sched_ext/for-7.3` 分支，将随 7.3 合并窗口进入主线。无阻塞问题。

## 效果评估

暂无性能数据。本系列主要解决正确性/可用性问题（NMI 安全性），非性能优化。

## 我可以参与的点

当前阶段暂无明显参与空间，系列已合入。可持续观察 7.3 合并窗口。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260725005019.1297049-1-tj@kernel.org
- tip-bot commit: 未获取到
- stable backport: 未获取到
