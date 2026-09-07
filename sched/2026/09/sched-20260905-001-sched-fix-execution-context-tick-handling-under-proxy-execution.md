# sched: Fix execution-context tick handling under proxy execution

## TL;DR

延续前几日的系列，本日 v3 收到多封复审（Re v2 1/2：81773/80952/80942/80406。目前v3 复审中；与 09-04 001 / 09-03 001 同源演进。- 属「代理执行执行上下文修正」主线。

## 背景与问题

延续前几日的系列，本日 v3 收到多封复审（Re v2 1/2：81773/80952/80942/80406；以及 v3 1/2：80559），讨论集中在 NUMA task tick 从执行上下文驱动、在 fair 任务替 RT/deadline donor 执行时的正确性。

## 技术方案

- v3 把 NUMA 与 cache 的执行上下文 tick 处理从 `task_tick_fair()` 移到 `sched_tick()`，并在 `rq->curr` 为 fair 任务时调用 hook。
- 本日为复审进展，焦点为 hook 调用时机与代理执行下的统计一致性。

## 版本演进与当前进展

- v3 复审中；与 09-04 001 / 09-03 001 同源演进。
- 属「代理执行执行上下文修正」主线。

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
  - [[sched-20260904-001]] 代理执行下执行上下文 tick 处理（v3，移入 sched_tick）。
  - [[sched-20260903-001]] 同系列 v2。
- 相关代码/commit：
  - `kernel/sched/core.c` `sched_tick()` / `task_tick_fair()`

---
id: sched-20260905-001
date: '2026-09-05'
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
- sched-20260904-001
- sched-20260903-001
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
---
