---
id: sched-20261012-027
date: '2026-10-12'
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260922082432.2987855-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20260922082432.2987855-1-albin_yang@163.com>
  date: '2026-09-22'
  summary: 修 sched_delayed 任务跨 CPU 迁移时 run_delay 重复累计
  review_outcome: K Prateek 已 Reviewed-by + Tested-by；Peter 未最终拍板
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 是否接受「仅 delayed dequeue、proxy exec 另议」的拆分未定
  next_action: Peter 拍板收原样（delayed-dequeue only）或要求 v4 覆盖 proxy exec
contribution_opportunities:
- kind: testing
  description: 复现 proxy exec 的 re-arm 场景，评估是否需 v4 加 !task_is_blocked() 条件
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20260923-007
tags:
- cfs
- sched_debug
title: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-007-sched-stats-fix-run-delay-over-count-for-migrated-sched-dela.html">sched-20260923-007</a>（及更早 20260921-006/20260922-015）：Wei Yang 的 run_delay 多计数修复——sched_delayed 任务跨 CPU 迁移时 run_delay 重复累计；v2 获 K Prateek Nayak 的 Reviewed-by + Tested-by，v3 已收集 tags。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-027-sched-stats-fix-run-delay-over-count-for-migrated-sched-dela.html">sched-20261012-027</a>（今天）：作者向 Peter 友好 ping 并补充论证——proxy exec 确有同样的 re-arm 问题但 `t->is_blocked` 无法门控（ttwu_runnable 的真实唤醒 enqueue 在 `p->is_blocked` 分支内、之后才清除，`!is_blocked` 会压掉本补丁依赖的 re-arm）；且 bug 早于 proxy exec（DELAY_DEQUEUE v6.12，proxy exec v6.17），若与 `task_is_blocked()` 耦合将无法原样回移植到 v6.12.y..v6.16.y。建议先按原样收（delayed dequeue only）、proxy exec 另议。

## 背景与问题

（承接 20260923-007）`sched_delayed` 任务在跨 CPU 迁移时 `run_delay` 被重复累计，导致 schedstats 数据虚高。

## 技术方案

（承接 20260923-007）补丁以 `se.sched_delayed` 门控 re-arm。今日作者论证为何不能用 `task_is_blocked()` 替代：delayed sleeper 没有 `blocked_on`；且与 proxy exec 耦合会破坏 v6.12–v6.16 的回移植能力。

## 版本演进与当前进展

v3（09-22，已带 R-b/Tested-by）→ 今日（10-12）作者 ping + 补充拆分论证；Peter 未回应。

## Maintainer 意见与讨论焦点

作者明确建议「先按原样收（delayed dequeue only）、proxy exec 侧另议」，并自愿「若要一并覆盖则发 v4（`!sched_delayed && !task_is_blocked()`，先复现 proxy 场景再复核 Prateek 的 Tested-by）」。Peter 尚未拍板。

## 合入评估

*likelihood=high*。有 R-b + Tested-by、作者给出回移植论证，仅等 Peter 决定拆分口径。*blocking_issues*：拆分口径未定。*next_action*：Peter 拍板。

## 效果评估

无新 benchmark；正确性修复，此前已有 Prateek 的 Tested-by（见 related）。

## 我可以参与的点

- `testing`：复现 proxy exec 的 re-arm 场景，为「是否需 v4 一并覆盖」提供实测依据。

## 参考链接

- lore（v3）: https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/
- lore（作者 ping + 论证）: https://lore.kernel.org/all/20261012042622.1488555-1-albin_yang@163.com/
