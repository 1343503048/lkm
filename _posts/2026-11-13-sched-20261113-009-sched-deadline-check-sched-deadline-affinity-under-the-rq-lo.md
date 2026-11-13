---
id: sched-20261113-009
subject: 'sched/deadline: Check SCHED_DEADLINE affinity under the rq lock'
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261105164856.29698-1-parri.andrea@gmail.com>
lore_url: https://lore.kernel.org/all/20261105164856.29698-1-parri.andrea@gmail.com/
authors:
- Andrea Parri
maintainers_involved:
- Sebastian Andrzej Siewior
current_version: v1
patch_series:
- version: v1
  msgid: <20261105164856.29698-1-parri.andrea@gmail.com>
  date: 2026-11-05
  summary: 把 SCHED_DEADLINE 亲和性检查移到 rq lock 下，消除检查-设置竞态
  review_outcome: 今日 Sebastian 给 Reviewed-by；与 Mathieu v5 系列 patch 18 重叠待协调
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 与 Mathieu Desnoyers 的 v5 29-patch 系列 patch 18 改同一代码段，落地顺序待协调
  next_action: 等待 Juri Lelli 表态，并确定与 Mathieu v5 系列的合并/落地顺序
contribution_opportunities:
- kind: review
  description: 审阅 SCA_DL_CHECK/SCA_DL_BW_RESERVED 在 cpuset retry 路径的置位/清除时机
- kind: testing
  description: 在 arm64 非对称 32 位系统验证 relax_compatible_cpus_allowed_ptr() 路径
generated_at: '2026-11-14T01:30:00'
source_email_count: 2
related_articles:
- sched-20261106-011
tags:
- deadline
- affinity
title: 'sched/deadline: Check SCHED_DEADLINE affinity under the rq lock'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-011-sched-deadline-check-sched-deadline-affinity-under-the-rq-lo.html">sched-20261106-011</a>：Andrea Parri 提交单补丁，把 SCHED_DEADLINE 任务的亲和性检查移到持有 rq lock 下进行，修掉「检查通过后、实际设置前亲和性被并发修改」的竞态窗口（`SCA_DL_CHECK` / `SCA_DL_BW_RESERVED` 标志位配套）。发出后暂无回复。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-009-sched-deadline-check-sched-deadline-affinity-under-the-rq-lo.html">sched-20261113-009</a>（今天）：**Andrea 温和催审（gentle ping）并提示其补丁与 Mathieu Desnoyers 的 v5 系列（patch 18）重叠**；**Sebastian Andrzej Siewior 补上 Reviewed-by**，认为方案正确，只对「rewrite 到不在 domain 内的 CPU mask」一处保留意见（作者已注释说明缘由）。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-011-sched-deadline-check-sched-deadline-affinity-under-the-rq-lo.html">sched-20261106-011</a>）`sched_setaffinity()` 对 SCHED_DEADLINE 任务做亲和性检查时存在竞态：检查通过与实际设置之间、或与 cpuset 并发重试之间，亲和性可能被并发修改，导致带宽记账（total_bw）归属错误。补丁把检查移到持有 rq lock 的位置（`__set_cpus_allowed_ptr_locked()` 附近），并用 `SCA_DL_CHECK` / `SCA_DL_BW_RESERVED` 标志位协调 retry 与 cpuset 路径。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-011-sched-deadline-check-sched-deadline-affinity-under-the-rq-lo.html">sched-20261106-011</a>）核心是把 SCHED_DEADLINE 亲和性检查放进 rq lock 保护区间，使检查所见的状态在设置完成前不会被并发改动；与 cpuset 竞态时通过标志位尝试回退/drop check 标志。Sebastian 确认「在 rq lock 下做检查，检查过的一切之后都不会变」，并指出与 cpuset race 时回退 drop check-flag 的语义他无法置评但作者已注释说明；另外建议把检查留在 `__sched_setaffinity()` 以便早期 bail out，但也表示没有强观点。

## 版本演进与当前进展
v1（2026-11-05）→ 今日：无新版本，作者 gentle ping；Sebastian 给 Reviewed-by（`Reviewed-by: Sebastian Andrzej Siewior <bigeasy@linutronix.de>`）。作者同时指出该补丁与 Mathieu 的 v5 系列 patch 18（"Move a task's bandwidth only where room was made"）重叠，并已就重叠另帖说明。

## Maintainer 意见与讨论焦点
- **Sebastian Andrzej Siewior**：Reviewed-by，认为方案正确；唯一保留在「set 到不在 domain 内的 CPU mask看起来不对」，但作者已注释原因，他不再坚持；并建议考虑在 `__sched_setaffinity()` 早期 bail out（无强观点）。
- **Juri Lelli**：作者 ping 的对象之一，当日未回帖。
- 重叠问题：本补丁与 Mathieu v5 系列 patch 18 改同一代码段，Mathieu 已在 patch 18 帖中回应「下版携带该补丁、放在 patch 18 之前」。

## 合入评估
已有 Sebastian 的 Reviewed-by，合入概率高。主要待决点是与 Mathieu v5 大片系列（29 补丁）的落地顺序——若 Mathieu 的系列先行，本补丁可能被其吸收。

## 效果评估
无 benchmark 数据（竞态正确性修复）。Sebastian 确认「报告的触发问题看起来已解决」。

## 我可以参与的点
- **review**：审阅 `SCA_DL_CHECK`/`SCA_DL_BW_RESERVED` 标志位在 cpuset retry 路径上的置位/清除时机（此前文章即留下的 review 缺口）。
- **testing**：在 arm64 非对称 32 位系统上验证 `relax_compatible_cpus_allowed_ptr()` 路径（此前未测缺口）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261105164856.29698-1-parri.andrea@gmail.com/
- 今日 Reviewed-by（Sebastian）: https://lore.kernel.org/all/20261113153549.Z8XPohWU@linutronix.de/
- 作者 ping + 重叠说明: https://lore.kernel.org/all/20261113150608.9233-1-parri.andrea@gmail.com/
