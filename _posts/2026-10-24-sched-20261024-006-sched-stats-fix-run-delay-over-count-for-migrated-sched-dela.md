---
id: sched-20261024-006
date: 2026-10-24
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261024042753.2276779-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved:
- Peter Zijlstra
current_version: v4
patch_series:
- version: v3
  msgid: <20260922082432.2987855-1-albin_yang@163.com>
  date: 2026-09-22
  summary: 修 sched_delayed 任务跨 CPU 迁移时 run_delay 重复累计
  review_outcome: K Prateek Reviewed-by + Tested-by
- version: v4
  msgid: <20261024042753.2276779-1-albin_yang@163.com>
  date: 2026-10-24
  summary: 无代码改动，重发以浮出补丁 + 补 Chen Yu/Kayra R-b 与 K Prateek T-b；重申与 proxy exec 解耦
  review_outcome: 多 R-b/T-b；Peter 未拍板
upstream_commit: null
fixes_commit: 152e11f6df29
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 是否接受「仅 delayed dequeue、proxy exec 另议」的拆分未定
  next_action: Peter 拍板收原样或要求 v4 覆盖 proxy exec
contribution_opportunities:
- kind: testing
  description: 复现 proxy exec 的 re-arm 场景，评估是否需 v4 一并覆盖
- kind: review
  description: 核对 sched_delayed 迁移路径（active load balance migrate_load）的实际触发条件
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
- sched-20261012-027
tags:
- cfs
- sched_debug
title: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-027-sched-stats-fix-run-delay-over-count-for-migrated-sched-dela.html">sched-20261012-027</a>（及更早 20260923-007）：Wei Yang 的 run_delay 多计数修复——`sched_delayed` 任务跨 CPU 迁移时 `run_delay` 重复累计；v2 获 K Prateek Nayak Reviewed-by + Tested-by，v3 已收集 tags；作者 10-12 向 Peter 补充「为何不能与 proxy exec 耦合」的论证并等拍板。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-006-sched-stats-fix-run-delay-over-count-for-migrated-sched-dela.html">sched-20261024-006</a>（今天，v4）：Wei Yang 发 v4（`Fixes: 152e11f6df29`），**无代码改动**，仅在 proxy exec 讨论后重发以再次浮出补丁；新增 Kayra Cizmeci、Chen Yu 的 Reviewed-by 与 K Prateek 的 Tested-by。作者重申 proxy exec 的同类 re-arm 问题另议、保持本补丁仅 delayed dequeue、以便回移植 v6.12.y..v6.16.y。

## 背景与问题
（承接 20261012-027）`DELAY_DEQUEUE` 下 blocked 任务留在 runqueue 且 `sched_info.last_queued` 被清，睡眠不计入 run_delay；但当该 sched_delayed 任务经普通迁移路径（move_queued_task / move_queued_task_locked）跨 CPU 时，`activate_task(dst, 0)` 不带 `ENQUEUE_RESTORE` 地调用 enqueue_task，把 last_queued 重装到迁移时刻，导致后续真实唤醒的 re-arm 被抑制，`sched_info_arrive()` 把整个迁移到唤醒的睡眠时长折进 run_delay。负载均衡也受影响：`can_migrate_task()` 的 sched_delayed 检查只在 `env->migration_type != migrate_load` 时 bails out，active load balance 的 migrate_load 不拦。今日无新背景，作者补充了与 proxy exec 解耦、便于回移植的论证。

## 技术方案
（承接 20261012-027 + 今日 v4）单补丁：`sched_info_enqueue()` 不再为 sched_delayed 任务重装 last_queued；唤醒路径在到达 sched_info_enqueue 前已清 sched_delayed，故真实唤醒时仍正常 re-arm，普通 runnable 任务不受影响。v4 **无代码改动**，仅在正文重述 proxy exec 侧为何单独处理：`t->is_blocked` 无法门控（ttwu_runnable 的真实唤醒 enqueue 在 `p->is_blocked` 分支内、之后才清除），`task_is_blocked()` 无法替代 `se.sched_delayed`（delayed sleeper 无 blocked_on），且耦合会破坏 v6.12.y..v6.16.y（有 DELAY_DEQUEUE、无 proxy exec）的回移植能力。

## 版本演进与当前进展
*current_version: v4*（`<20261024042753.2276779-1-albin_yang@163.com>`）。v3（`<20260922082432.2987855-1-albin_yang@163.com>`，09-22）→ v4（10-24，无代码改动，重发 + 补 tags）。

## Maintainer 意见与讨论焦点
v4 新收集：Chen Yu、Kayra Cizmeci 各 *Reviewed-by*，K Prateek Nayak *Tested-by*（此前已有 K Prateek Reviewed-by）。作者重申「先按原样收（delayed dequeue only）、proxy exec 侧另议」。Peter 仍未在当日缓存内拍板。

## 合入评估
*likelihood=high*。已累计多位 Reviewed-by + Tested-by、带明确 `Fixes: 152e11f6df29` 与 `Reported-by`，作者给出回移植论证，仅等 Peter 决定拆分口径。*blocking_issues*：Peter 是否接受「仅 delayed dequeue、proxy exec 另议」的拆分未定。*next_action*：Peter 拍板收原样（delayed-dequeue only）或要求 v4 一并覆盖 proxy exec。

## 效果评估
无新 benchmark；正确性修复，此前已有 K Prateek 的 Tested-by（见 related）。无量化数据。

## 我可以参与的点
- *kind: testing*：复现 proxy exec 的 re-arm 场景，为「是否需 v4 一并覆盖 proxy exec」提供实测依据。
- *kind: review*：核对 v4 对 sched_delayed 迁移路径（active load balance 的 migrate_load）的实际触发条件。

## 参考链接
- v4: https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/
- v3: https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-027-sched-stats-fix-run-delay-over-count-for-migrated-sched-dela.html">sched-20261012-027</a>
