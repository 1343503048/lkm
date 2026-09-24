---
id: sched-20260911-012
subject: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260911075800.491472-1-ye.liu@linux.dev>
lore_url: https://lore.kernel.org/all/20260911075800.491472-1-ye.liu@linux.dev/
authors:
- Ye Liu
maintainers_involved:
- Michal Hocko
- Oleg Nesterov
current_version: v3
patch_series:
- version: v1
  msgid: <20260813092933.562028-1-ye.liu@linux.dev>
  date: 2026-08-13
  summary: OOM kill 路径的 RCU 迭代可读性改造起点。
  review_outcome: Michal Hocko 建议推广为通用宏。
- version: v2
  msgid: <20260907081334.1152889-1-ye.liu@linux.dev>
  date: 2026-09-07
  summary: 宏改名 *_rculock（Rostedt/tglx）；修 hung_task 标签等。
  review_outcome: PeterZ/Rostedt 要求拆分合并的 kernel/ 补丁；Lorenzo 要求 changelog 下移与缩进调整。
- version: v3
  msgid: <20260911075800.491472-1-ye.liu@linux.dev>
  date: 2026-09-11
  summary: 15 补丁 per-subsystem 拆分；sched 转换（10/15）带 mhocko Acked-by 与 Oleg/Lorenzo/SJ
    Park Reviewed-by。
  review_outcome: 当日缓存无新意见；等待各子系统维护者表态。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 15 补丁跨多树，各子系统 ack 状态大部分未获取到
  - patch 1（宏定义）需 sched 树先收，其余补丁依赖它
  next_action: 等各子系统维护者对 v3 的表态；sched 侧 10/15 有望先走
contribution_opportunities:
- kind: review
  description: 排查 sched/ 内剩余手工 rcu_read_lock+for_each 组合，作补充转换候选
- kind: new_patch
  description: 宏被接受后为 sched/ 剩余调用点发补充转换补丁
- kind: testing
  description: PROVE_RCU 下跑 oom_kill/hung_task 场景验证宏展开
generated_at: '2026-09-14T11:35:00'
source_email_count: 3
related_articles:
- sched-20260907-004
- sched-20260908-009
tags:
- cfs
title: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
layout: article
---

## TL;DR
Ye Liu（kylinos）的 RCU 迭代宏系列发到 v3：新增 for_each_process_rculock()/for_each_thread_rculock()/for_each_process_thread_rculock()（scoped_guard(rcu) 包裹的迭代宏），并把 mm/kernel/fs/lib/security 各处的手工 rcu_read_lock/unlock 转换过去（15 个补丁、无功能变化）。v3 落实了 PeterZ/Rostedt 的拆分要求，sched 部分已带 mhocko Acked-by 与 Oleg/Lorenzo/SJ Park Reviewed-by。本文为增量更新，v1/v2 进展见 <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-004-sched-introduce-for-each-process-rculock-and-for-each-thread.html">sched-20260907-004</a>、<a class="article-ref" href="/lkm/2026/09/08/sched-20260908-009-sched-introduce-for-each-process-rculock-and-for-each-thread.html">sched-20260908-009</a>。

## 背景与问题
遍历进程/线程时需要配对 rcu_read_lock()/rcu_read_unlock() 或 guard(rcu)，与 for_each_process_thread() 混写易错（尤其循环内 break/return 提前退出时的解锁路径）；OOM kill 路径曾被 Michal Hocko 指出可读性问题（系列起源，2026-08-13）。宏把 RCU 读锁的生命周期绑定到循环体上，break/goto/return 都安全退出。

## 技术方案
- 宏实现：for_each_*_rculock() = 现有迭代宏 + scoped_guard(rcu)，定义在 include/linux/sched/signal.h；
- v3 结构：patch 1 引入宏，patch 2-15 按子系统逐个转换（mm/oom_kill、mm/ksm、mm/memory-failure、cpu/hotplug、freezer、hung_task、locking/lockdep、rcu、sched、tracing/fgraph、unwind、fs、lib、security/landlock）；
- sched 部分（10/15）：core.c 的 uclamp_sync_util_min_rt_default() 与 debug.c 的 print_rq() 两处 guard(rcu)+for_each 组合换成单宏，-5/+2 行。

## 版本演进与当前进展
*current_version: v3（cover msgid `<20260911075800.491472-1-ye.liu@linux.dev>`，09-11 15:57 入缓存；当日缓存含 00/15、01/15、10/15 三封，其余补丁未入缓存）*。

- v1（08-13 起，oom_kill 单点）：Michal Hocko 建议推广为宏；
- v2（09-07）：宏改名 *_rcu → *_rculock（Steven Rostedt 提出、Thomas Gleixner 认可，避免与要求调用方持锁的 *_rcu() 迭代器混淆）；hung_task 标签改名等；
- v3（09-11）：按 PeterZ/Rostedt 意见把合并的 kernel/ 补丁拆成 per-subsystem；changelog 移到 --- 之下（Lorenzo Stoakes）；宏定义内循环体缩进体现 scoped_guard 作用域（Lorenzo）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra / Steven Rostedt**：拒绝把多个子系统塞进一个大补丁，要求按子系统拆分——v3 已落实；
- **Michal Hocko**：10/15（sched 转换）Acked-by；此前对 oom_kill 路径的建议是系列起点；
- **Thomas Gleixner**：认可改名，并要求文档写明 break 只退内层循环、需 goto 才能同时退出两层；
- **Oleg Nesterov / Lorenzo Stoakes / SJ Park**：10/15 带 Reviewed-by；
- 当前无未解决分歧；剩余风险是 15 个补丁逐个过各子系统维护者的进度。

## 合入评估
*likelihood=medium*：宏设计与转换无功能变化、review 意见逐条落实、sched 补丁已有 A-b + 3 个 R-b；但 15 补丁的收取路径复杂（跨 mm/sched/fs/lib/security 多树），单系列合入周期长。*blocking_issues*：各子系统补丁需各自维护者 ack（sched 之外的状态未获取到）；patch 1 的宏进入 include/linux/sched/signal.h 需要 sched 树先收。*next_action*：等待各子系统维护者对 v3 对应补丁的表态；sched 侧 10/15 可望先走。

## 效果评估
无性能数据（作者明确 No functional change）；收益是正确性/可读性：break/goto/return 不再可能漏解锁。效果为设计主张，无量化对比。

## 我可以参与的点
- kind=review：核对 sched 两处转换（uclamp 同步路径、print_rq）之外，sched/ 内是否还有手工 rcu_read_lock + for_each_process_thread 组合未被覆盖（可作 v4 的补充转换补丁）。
- kind=new_patch：若宏被接受，为 sched/ 剩余调用点发补充转换补丁。
- kind=testing：CONFIG_PROVE_RCU 下跑含 oom_kill/hung_task 场景的 boot 测试，确认 scoped_guard 展开无误。

## 参考链接
- v3 cover：https://lore.kernel.org/all/20260911075800.491472-1-ye.liu@linux.dev/
- v3 10/15（sched 转换）：https://lore.kernel.org/all/20260911075800.491472-11-ye.liu@linux.dev/
- v3 01/15：https://lore.kernel.org/all/20260911075800.491472-2-ye.liu@linux.dev/
- v2：https://lore.kernel.org/all/20260907081334.1152889-1-ye.liu@linux.dev/
- v1（oom_kill 起点）：https://lore.kernel.org/all/20260813092933.562028-1-ye.liu@linux.dev/
