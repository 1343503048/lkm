# sched/rt: Fix RT watchdog accounting for proxy execution

## TL;DR

代理执行下 task_tick_rt() 针对调度上下文 rq->donor 调用，而 rq->curr 才是真正执行任务。目前单 patch，重点修正在代理执行下 RT 限额与 posix CPU 定时器的一致性。

## 背景与问题

代理执行下 `task_tick_rt()` 针对调度上下文 `rq->donor` 调用，而 `rq->curr` 才是真正执行任务。RT watchdog 通过 `task` 参数查 `RLIMIT_RTTIME` 并更新该任务的 `rt.timeout` 与 `posix_cputimers` 状态；但运行时间记账记到 `rq->curr`，`run_posix_cpu_timers()` 检查 `current`。若不传 `rq->curr`，watchdog 状态更新会跟随错误的（donor）上下文，导致 `RLIMIT_RTTIME` 误触发/漏触发与 posix 定时器状态错乱。

## 技术方案

- `watchdog()` 改传 `rq->curr`，使 `rt.timeout` / `posix_cputimers` 状态更新跟随真实执行上下文。
- 当 non-RT 执行任务借用 RT 任务的带宽而阻塞时，重置 `rt.timeout`。

## 版本演进与当前进展

- 单 patch，重点修正在代理执行下 RT 限额与 posix CPU 定时器的一致性。
- 属「代理执行执行上下文修正」主线，与同日 001/008 同源。

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
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（同源主线）。
- 相关代码/commit：
  - `kernel/sched/rt.c` `task_tick_rt()` / `watchdog()`

---
id: sched-20260903-005
date: '2026-09-03'
subject: 'sched/rt: Fix RT watchdog accounting for proxy execution'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/rt+Fix+RT+watchdog+accounting+for+proxy+execution
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
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
source_email_count: 1
related_articles:
- sched-20260903-001
tags:
- rt
- proxy_execution
- sched/core
---
