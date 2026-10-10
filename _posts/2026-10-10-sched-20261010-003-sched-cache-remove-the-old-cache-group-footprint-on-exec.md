---
id: sched-20261010-003
date: '2026-10-10'
subject: 'sched/cache: Remove the old cache group footprint on exec'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261009151215.62878-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261009151215.62878-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v2
patch_series:
- version: v1
  msgid: <20261009151215.62878-1-jemmywong512@gmail.com>
  date: '2026-10-09'
  summary: 抽 sched_cache_footprint_sub()，exec/exit 两处减旧 group 贡献
  review_outcome: 当日无回帖
- version: v2
  msgid: <20261010111612.31345-1-jemmywong512@gmail.com>
  date: '2026-10-10'
  summary: '补 vfork 说明、Fixes: tag、时序注释，加 Tim Chen R-b'
  review_outcome: Tim Chen 给 R-b；Chen Yu 提出残余并发竞争、建议 cmpxchg
upstream_commit: null
fixes_commit: b636fef85bda
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Chen Yu 的并发竞争质疑待作者回应/修复
  next_action: 作者回应 cmpxchg 建议，必要时发 v3
contribution_opportunities:
- kind: review
  description: 复核 execve 与 CLONE_VM task_numa_placement() 的并发竞争是否可实际触发
- kind: testing
  description: 用 NUMA 密集长命 CLONE_VM 负载验证 fix 后 footprint 收敛正确
generated_at: '2026-10-11T09:00:00'
source_email_count: 4
related_articles:
- sched-20261009-007
tags:
- cfs
- numa_balancing
title: 'sched/cache: Remove the old cache group footprint on exec'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-007-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261009-007</a>：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换掉 cache group 后旧 group 的 footprint 只在 exit 路径被减，导致「CLONE_VM 无 CLONE_THREAD」共享 mm 的任务在 exec 后旧贡献残留、抑制 cache-aware 聚合的 LLC capacity 检查；把 footprint 减法抽成 helper，exec 与 exit 两处都用。当日无回帖。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-003-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261010-003</a>（今天）：**发出 v2**（加 Tim Chen 的 `Reviewed-by` 与 `Fixes:` tag，补 vfork/长命 CLONE_VM 任务说明），Tim Chen 正式 review 并给 R-b；但 **Chen Yu 发现 v2 仍有一处竞争**——execve()（CPU0）与 CLONE_VM 任务的 `task_numa_placement()`（CPU1）并发读写 footprint、无锁保护，减法可能被覆盖丢失；建议把裸写改成 cmpxchg，并给出了（仅编译验证的）示意 diff。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-007-sched-cache-remove-the-old-cache-group-footprint-on-exec.html">sched-20261009-007</a>）`exec` 在重置 NUMA fault 统计**之前**换掉任务的 cache group，但只有 exit 路径会从旧 group 的 footprint 减去任务贡献；`CLONE_VM` 而非 `CLONE_THREAD` 创建的任务能保留旧 mm 与 cache group，使执行任务的贡献残留在旧 group、既不更新也不衰减，可能抑制 cache-aware 聚合的 LLC capacity 检查。v1 已抽 `sched_cache_footprint_sub()` 在 exec/exit 两处调用。今天的新增点是 Chen Yu 指出的**并发竞争**：即使打上 v2，footprint 仍可能因 CPU0 的减法被 CPU1 的重写的并发行为覆盖而丢失。

## 技术方案
（承接）v2 保持 v1 的 helper 化减法，并补上：vfork 说明、`Fixes: b636fef85bda`、footprint 减法须先于 `task_numa_free()` 的注释、Tim Chen 的 `Reviewed-by`。今天 Chen Yu 提出的加固方向：把 footprint 的裸 `READ_ONCE`/`WRITE_ONCE` 读写改成 `try_cmpxchg` 循环（`sched_cache_footprint_update(grp, delta, add)`），消除 CPU0 减法与 CPU1 `task_numa_placement()` 加法之间的覆盖竞争。他附的 diff（仅编译验证）把 exec 与 exit 两处都走该 cmpxchg 更新。

## 版本演进与当前进展
- v1（10-09）：`sched_cache_footprint_sub()` 抽 helper，exec/exit 两处减法。
- v2（今天，`<20261010111612.31345-1-jemmywong512@gmail.com>`）：补 vfork/长命 CLONE_VM 任务说明、`Fixes:` tag、时序注释、Tim Chen R-b。
- 今天同期讨论：Tim Chen 回帖（`<b73d47b04b62d2637920f59134b632d607a71aee.camel@linux.intel.com>`）给 R-b；Chen Yu 回帖（`<aspT_A1vl-RwKmoP@chenyu-dev>`）提出残余竞争并给 cmpxchg 示意 diff。

## Maintainer 意见与讨论焦点
- **Tim Chen**（Intel）：v1 即认可方向，今天正式给 `Reviewed-by: Tim Chen`；此前要求补 vfork 说明与 `Fixes:` tag。
- **Chen Yu**（Intel）：发现 v2 仍存在 execve 与 CLONE_VM 任务并发读写 footprint 的竞争（无锁保护），CPU1 的重写会覆盖 CPU0 的减法；给出 cmpxchg 版的加固 diff（仅编译验证）。指出 `numa_scan_period` 不小，用原子写的开销可接受。
- 分歧点：v2 的裸写是否足够——Chen Yu 认为需要 cmpxchg 才能关掉竞争窗口；作者尚未回应。

## 合入评估
*likelihood=medium*。已有 Tim Chen 的 R-b、真实 `Fixes:` tag；但 Chen Yu 刚提出一个并发修正点（review 意见），作者需回应（采纳 cmpxchg 或论证竞争无害）后再收。*blocking_issues*：Chen Yu 的并发竞争质疑待作者回应/修复。*next_action*：Jemmy Wong 回应 cmpxchg 建议，必要时发 v3。

## 效果评估
本补丁为记账正确性修复，无 benchmark 数据；v2 自述「found by code inspection, not a workload reproducer」（作者在回帖中向 Tim Chen 确认）。Chen Yu 的竞争分析也是代码级推演，未见实测复现。

## 我可以参与的点
- 复核 Chen Yu 提出的 execve vs CLONE_VM `task_numa_placement()` 竞争时序是否可实际触发；
- 若有 NUMA 密集的长命 CLONE_VM 负载，可检验 fix 后 footprint 是否正确收敛。

## 参考链接
- v1: https://lore.kernel.org/all/20261009151215.62878-1-jemmywong512@gmail.com/
- v2: https://lore.kernel.org/all/20261010111612.31345-1-jemmywong512@gmail.com/
- Tim Chen R-b: https://lore.kernel.org/all/b73d47b04b62d2637920f59134b632d607a71aee.camel@linux.intel.com/
- Chen Yu 竞争分析: https://lore.kernel.org/all/aspT_A1vl-RwKmoP@chenyu-dev/
