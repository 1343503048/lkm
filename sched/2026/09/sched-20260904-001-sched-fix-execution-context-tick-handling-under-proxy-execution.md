# sched: Fix execution-context tick handling under proxy execution

## TL;DR

延续 09-03 系列，本系列把 NUMA 与 cache 的执行上下文 tick 处理从 task_tick_fair() 移到 sched_tick()，并在 rq->curr 为 fair 任务时调用，使代理执行（proxy execution）下这些 hook 能正确基于执行上下文运行，而其余 fair-class tick 记账仍归属调度上下文（rq->donor）。目前作者 Hui Su，v3；本日多封复审（Re：numa 80097/78678/78148，cache 78599/77800）。

## 背景与问题

延续 09-03 系列，本系列把 NUMA 与 cache 的执行上下文 tick 处理从 `task_tick_fair()` 移到 `sched_tick()`，并在 `rq->curr` 为 fair 任务时调用，使代理执行（proxy execution）下这些 hook 能正确基于执行上下文运行，而其余 fair-class tick 记账仍归属调度上下文（`rq->donor`）。

## 技术方案

- v3 相对 v2 的变化：
  - 将 NUMA 与 cache 的执行上下文 tick 处理从 `task_tick_fair()` 迁到 `sched_tick()`。
  - 当 `rq->curr` 是 fair 任务时调用 hook，使 fair 任务替 RT/deadline donor 执行时这些 hook 也能运行。

## 版本演进与当前进展

- 作者 Hui Su，v3；本日多封复审（Re：numa 80097/78678/78148，cache 78599/77800）。
- 属「代理执行执行上下文修正」主线，与同日 003/007 同源。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（v2）。
- 相关代码/commit：
  - `kernel/sched/core.c` `sched_tick()` / `task_tick_fair()`

---
id: sched-20260904-001
date: '2026-09-04'
subject: 'sched: Fix execution-context tick handling under proxy execution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+Fix+execution-context+tick+handling+under+proxy+execution+v3
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- Hui Su
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 2
related_articles:
- sched-20260903-001
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
---
