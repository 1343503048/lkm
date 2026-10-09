# sched/cache: Remove the old cache group footprint on exec

## TL;DR
Jemmy Wong 修 `sched_cache_exec_mmap()` 的一个记账遗漏：exec 换掉任务的 cache group 后，旧 group 的 footprint 只在 exit 路径被减掉，导致「CLONE_VM 无 CLONE_THREAD」共享 mm 的任务在 exec 后旧贡献残留、抑制 cache-aware 聚合的 LLC capacity 检查。补丁把 footprint 减法抽成 helper，在 exec 与 exit 两处都用。当日无回帖。

## 背景与问题
`exec` 会在重置 NUMA fault 统计**之前**换掉任务的 cache group，但只有 exit 路径会从旧 group 的 footprint 里减去任务的贡献。`de_thread()` 虽移除执行任务线程组的其它成员，但以 `CLONE_VM` 而非 `CLONE_THREAD` 创建的任务能保留旧 mm 与 cache group——于是执行任务的贡献会残留在那个 group 里、既不更新也不衰减，可能通过 LLC capacity 检查抑制 cache-aware 聚合。

## 技术方案
把既有的 footprint 减法逻辑抽成 `sched_cache_footprint_sub()`（保留无锁与 underflow clamp 语义），在「离开 cache group」的 exec 与 exit 两条路径都调用；在 drop 旧 group 引用之前先减。`kernel/sched/fair.c` +29/-22。

## 版本演进与当前进展
v1 首发（`<20261009151215.62878-1-jemmywong512@gmail.com>`）。当日无回帖、无维护者 review。

## Maintainer 意见与讨论焦点
当日无回帖。该补丁与作者同日另发的 proxy-exec 修复（见 sched-20261009-015 的增量）同源——都是 cache-aware 记账的收尾，但本枚针对 exec 路径、独立成篇。

## 合入评估
*likelihood=unknown*。v1 当日无回帖，无 cache-aware 系列维护者表态。*blocking_issues*：无 review；`total_numa_faults` 在 exec 路径的时序（换组 vs 重置统计）需要 reviewer 确认。*next_action*：等维护者 review。

## 效果评估
无性能数据，纯记账正确性修复。作者描述的影响是「CLONE_VM 无 CLONE_THREAD 任务 exec 后旧贡献残留、可能抑制 cache-aware 聚合」，属正确性/公平性问题，无量化表现。

## 我可以参与的点
- `review`：审 exec 换组与 NUMA fault 统计重置的时序，确认 `sched_cache_footprint_sub` 在 exec 路径不会 double-subtract。
- `testing`：CLONE_VM 多线程共享 mm + exec 场景下验证 footprint 收敛与 cache-aware 聚合行为。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261009151215.62878-1-jemmywong512@gmail.com/

---
id: sched-20261009-007
date: '2026-10-09'
subject: 'sched/cache: Remove the old cache group footprint on exec'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261009151215.62878-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261009151215.62878-1-jemmywong512@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261009151215.62878-1-jemmywong512@gmail.com>'
    date: '2026-10-09'
    summary: '抽 footprint 减法 helper，exec 与 exit 都减旧 group 贡献'
    review_outcome: '当日无回帖'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'v1 无 review'
  next_action: '等维护者 review'
contribution_opportunities:
  - kind: review
    description: '审 exec 换组与 NUMA fault 重置时序，防 double-subtract'
  - kind: testing
    description: 'CLONE_VM 共享 mm + exec 场景验证 footprint 收敛'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles: []
tags:
  - numa_balancing
  - load_balance
---