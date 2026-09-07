# sched_ext: Generalize the reject DSQ reenqueue path

## TL;DR

作为某个 18 补丁 sched_ext 系列的第 12 个（[PATCH 12/18]），泛化 reject DSQ 的重入队（reenqueue）路径。目前补丁系列的一部分，本日收到 Tejun nits。- 与代理执行/DSQ 语义调整相关（被代理任务的 DSQ 归属在 reject 路径需正确判断）。

## 背景与问题

作为某个 18 补丁 sched_ext 系列的第 12 个（[PATCH 12/18]），泛化 reject DSQ 的重入队（reenqueue）路径。Tejun 给出 nits 评审，引用 Andrea Righi 在 `scx_dispatch_enqueue()` 中将 `is_rq_owned` 改为 `dsq_is_rq_owned(dsq)` 的改动。

## 技术方案

- 泛化 reject DSQ reenqueue，使 `scx_dispatch_enqueue()` 的 RQ-owned DSQ 判定统一走 `dsq_is_rq_owned()`，减少特殊分支。

## 版本演进与当前进展

- 18 补丁系列的一部分，本日收到 Tejun nits。
- 与代理执行/DSQ 语义调整相关（被代理任务的 DSQ 归属在 reject 路径需正确判断）。

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
  - [[sched-20260902-001]] 代理执行与 sched_ext 兼容（影响 DSQ 路径）。
- 相关代码/commit：
  - `kernel/sched/ext.c` `scx_dispatch_enqueue()` / `dsq_is_rq_owned()`

---
id: sched-20260904-008
date: '2026-09-04'
subject: 'sched_ext: Generalize the reject DSQ reenqueue path'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+Generalize+the+reject+DSQ+reenqueue+path
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Andrea Righi
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 6
related_articles:
- sched-20260902-001
tags:
- sched_ext
---
