---
id: sched-20260929-016
date: 2026-09-29
subject: 'sched/debug: Add migration stats due to non preferred CPUs'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260928053728.797539-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/4cd3d839-ac67-43ac-9b22-0ded9c3d1f41@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved:
- Nathan Chancellor
current_version: v14
patch_series:
- version: v13
  msgid: <20260909135617.871006-10-sshegde@linux.ibm.com>
  date: 2026-09-09
  summary: 新增 nr_migrations_cpu_non_preferred 迁移统计，经 /proc/<pid>/sched 暴露
  review_outcome: Peter 提 changelog 语义 + schedstat 版本两条
- version: v14
  msgid: <20260928053728.797539-10-sshegde@linux.ibm.com>
  date: 2026-09-28
  summary: 重发；8/13 的 context_unsafe_alias(rq) 位置触发 clang 线程安全分析构建失败
  review_outcome: Nathan 报构建失败；Shrikanth 给 context_unsafe_alias 提前的修复 diff
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - clang 线程安全分析构建失败待修复并确认
  - 系列层入队 sched/core、目标 7.4 未获 Peter 拍板
  next_action: 作者折入 context_unsafe_alias 位置修复重发，等 Nathan 确认 clang 构建通过
contribution_opportunities:
- kind: review
  description: 核对 context_unsafe_alias 提前是否覆盖 push 路径其它锁获取点
- kind: testing
  description: 用 clang-23+ 构建打过本片的分支确认构建失败消失
source_email_count: 3
related_articles:
- sched-20260926-002
tags:
- sched_debug
- load_balance
- affinity
title: 'sched/debug: Add migration stats due to non preferred CPUs'
layout: article
---

> **subject**：`sched/debug: Add migration stats due to non preferred CPUs`

## TL;DR

本文为增量更新，完整脉络见 related_articles（steal_governor 系列）。

- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>：Peter Zijlstra 首次逐枚细读，对 09/13 提两条——迁移计数语义需在 changelog 写清、以及「改了输出格式是否该 bump schedstat 版本」。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-002-sched-debug-add-migration-stats-due-to-non-preferred-cpus.html">sched-20260926-002</a>：Shrikanth 回答 schedstat 版本问题——该统计落在 `/proc/<pid>/sched`（无版本号）而非 `/proc/schedstat`，无需 bump。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-016-sched-debug-add-migration-stats-due-to-non-preferred-cpus.html">sched-20260929-016</a>（今天）：Nathan Chancellor 报 v14 的 09/13 在 clang-23+（默认开启 thread-safety analysis）下构建失败——`__migrate_task` 需持 `rq_lock` 独占；Shrikanth 定位到 patch 8/13 的 `context_unsafe_alias(rq)` 位置，把 `context_unsafe_alias(rq)` 移到 `rq_lock(rq, &rf)` 之前修复。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-002-sched-debug-add-migration-stats-due-to-non-preferred-cpus.html">sched-20260926-002</a>）steal_governor 系列引入 preferred CPU 机制后，任务会因 CPU 非 preferred 被推走或在唤醒时避开，此前无独立统计口径。本片在 sched/debug 补 `nr_migrations_cpu_non_preferred` 计数。今天的新问题是 v14 的该补丁引入了 clang 线程安全分析的构建失败。

## 技术方案

（承接）per-task 迁移统计经 `/proc/<pid>/sched` 暴露（无版本语义）。今天的修复是针对 8/13 在 `sched_non_preferred_cpu_push_stop()` 里 `context_unsafe_alias(rq)` 的位置——Nathan 报的错误（`kernel/sched/core.c:11292` 调 `__migrate_task` 需持 `rq_lock` 独占、`11298` 释放未持有的锁），Shrikanth 给出 diff：把 `context_unsafe_alias(rq)` 从 `rq_lock(rq, &rf)` 之后移到**之前**，使 clang 能看到锁获取前已声明 unsafe alias。「I will write a changelog and send it across soon.」

## 版本演进与当前进展

- v13（09-09）：本片随系列发版。
- v14（09-28，cover `<20260928053728.797539-1-sshegde@linux.ibm.com>`）：重发，其中 8/13 的 `context_unsafe_alias(rq)` 位置触发 clang 构建失败。
- 09-29：Nathan 报错（`<20260929121838.GA1814129@ax162>`）→ Shrikanth 先回「let me try locally」（`<2964a7d8-...>`）→ 再给修复 diff（`<4cd3d839-...>`），并 cc Marco（context_unsafe_alias 相关）求确认。

## Maintainer 意见与讨论焦点

- **Nathan Chancellor**（kernel 构建/Distro 维护者）：用 clang-23+（默认开 thread-safety analysis）复现 v14 构建失败，3 个 error 均指向 `__migrate_task`/`rq_unlock` 的锁持有分析，建议「maybe another context_unsafe_alias()?」，cc Marco。
- **Shrikanth Hegde**（作者）：定位到 patch 8/13 把 rq 标为 `context_unsafe_alias` 的时机（在取锁之后才标），给出把 `context_unsafe_alias(rq)` 提前到 `rq_lock` 之前的修复，并「Let me know if it works for you」。
- 无 NAK；这是 v14 新引入的构建正确性问题，尚未看到 Nathan 对修复的确认。

## 合入评估

*likelihood=medium*。本片的两条 review 点（changelog、schedstat 版本）此前已收敛，但 v14 引入的 clang 构建失败需修复并确认，且系列层「入队 sched/core、目标 7.4」仍待 Peter 拍板。*blocking_issues*：clang 线程安全分析构建失败待作者修复并确认；系列层入队时点未定。*next_action*：作者把 `context_unsafe_alias` 位置修复折进重发（已给 diff），并等 Nathan 确认 clang 构建通过。

## 效果评估

无 benchmark 数据；本片为可观测性统计新增，效果体现在能定位 preferred CPU 机制的实际触发次数。

## 我可以参与的点

- `review`：核对 `context_unsafe_alias(rq)` 提前到 `rq_lock` 之前是否也覆盖 push 路径的其它锁获取点，避免 clang 分析继续报新位置。
- `testing`：用 clang-23+（开 thread-safety analysis）构建打过本片的分支，确认构建失败消失。

## 参考链接

- lore（Nathan 报错）: https://lore.kernel.org/all/20260929121838.GA1814129@ax162/
- lore（Shrikanth 修复 diff）: https://lore.kernel.org/all/4cd3d839-ac67-43ac-9b22-0ded9c3d1f41@linux.ibm.com/
- v14 封面: https://lore.kernel.org/all/20260928053728.797539-1-sshegde@linux.ibm.com/
