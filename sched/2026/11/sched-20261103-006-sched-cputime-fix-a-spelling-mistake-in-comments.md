# sched/cputime: Fix a spelling mistake in comments

## TL;DR

bajing 的纯注释拼写修正：`kernel/sched/cputime.c` 里 "substract" 在两处应拼作 "subtract"。无功能变化，单补丁，当日无人回帖。

## 背景与问题

`kcpustat_idle_stop()` 的注释里把 "subtract" 错拼成 "substract"（两处）。

## 技术方案

纯注释改动（comment-only，+2/−2），把 "substracting"/"substract" 改为 "subtracting"/"subtract"，无任何功能影响。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103070429.5666-1-bajing@cmss.chinamobile.com）*。当日无回帖。

## Maintainer 意见与讨论焦点

无表态。

## 合入评估

*likelihood=high*。纯注释拼写修正、零风险，此类改动通常被 trivial 收取，只是优先级低。

## 效果评估

无效果数据（注释修正）。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103070429.5666-1-bajing@cmss.chinamobile.com/

---
id: sched-20261103-006
date: 2026-11-03
subject: "sched/cputime: Fix a spelling mistake in comments"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261103070429.5666-1-bajing@cmss.chinamobile.com>"
lore_url: "https://lore.kernel.org/all/20261103070429.5666-1-bajing@cmss.chinamobile.com/"
authors: [bajing]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103070429.5666-1-bajing@cmss.chinamobile.com>"
    date: 2026-11-03
    summary: "cputime.c 注释把 substract 改为 subtract（纯注释）。"
    review_outcome: "暂无 review。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 trivial 收取。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: []
---