# sched: introduce for_each_process_rculock and for_each_thread_rculock

## TL;DR
Ye Liu 的进程/线程遍历 RCU 化系列发到 v4（共 15 个补丁），新增 `for_each_process_rculock()` / `for_each_thread_rculock()` / `for_each_process_thread_rculock()` 三个宏，用 `scoped_guard(rcu)` 把 RCU 读锁的作用域收敛到循环体，替代手写 `rcu_read_lock()/rcu_read_unlock()` 与 `guard(rcu)` 对，并批量转换 mm/kernel/fs/lib/security 的调用点。本日重点：v4 修正了 patch 5 标题/提交信息错误，并确认 v3 中 sashiko-bot 对 4/11/13 三个补丁的告警均为误报。已获 Michal Hocko（提出者）+ 多位维护者 Reviewed-by，合入概率高。

## 背景与问题
`for_each_process()` / `for_each_thread()` / `for_each_process_thread()` 系列宏只负责遍历，RCU 读锁需要调用者自己配对管理，容易在 `break`/`goto`/`return` 等提前退出路径上漏放锁或作用域过宽。该改进最初由 Michal Hocko 针对 oom_kill 路径提出（cover 中标注 "Suggested by Michal Hocko for the oom_kill path [2]"）。

## 技术方案
在 `include/linux/sched/signal.h` 中新增三个宏，内部用 `scoped_guard(rcu)` 包裹循环，使 RCU 读锁在进入循环前自动获取、退出循环（含 break/goto/return）时自动释放，作用域严格等于循环体。其余补丁把 mm/、kernel/、fs/、lib/、security/ 各子系统中手写的 `rcu_read_lock()/rcu_read_unlock()` 和 `guard(rcu)` 对统一替换为这三个新宏。补丁 10/15 处理 `kernel/sched/core.c`（`uclamp_sync_util_min_rt_default`）与 `kernel/sched/debug.c`（`print_rq`），均为无功能变化的机械替换。

## 版本演进与当前进展
- v1（08-13）→ v2 → v3 → **v4（09-21）**。
- v4 相对 v3 的改动：修正 patch 5（cpu/hotplug）标题与提交信息误写为 "thread iterator"/"for_each_thread_rculock"，实际代码是把 `for_each_process()` 转成 `for_each_process_rculock()`。
- v3 中 sashiko-bot 对 patch 4（folio 锁释放时机）、patch 11（`alloc_retstack_tasklist` 的 goto 与 scoped 清理混用）、patch 13（`__set_oom_adj` 的 goto 与 scoped 混用）的自动评审，经作者逐一核对确认为误报（分别误判了锁持有路径、goto 管理的是内存/互斥锁而非 RCU 锁、不同资源分开管理）。
- v4 补丁已带 Michal Hocko Acked-by，SJ Park / Gregory Price / Oleg Nesterov / Lorenzo Stoakes 的 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Michal Hocko**：改进的最初提出者，v4 已给 Acked-by。
- **Oleg Nesterov**、**SJ Park**、**Gregory Price**、**Lorenzo Stoakes**：均已 Reviewed-by。
- 讨论焦点已从"是否值得做"收敛到"自动评审告警的真伪核查"——v4 cover 明确列出三处误报及理由，说明社区对该系列方向认可、当前无实质分歧。

## 合入评估
*likelihood=high*。系列被 mm 维护者（Michal Hocko）主动提出并 Acked，核心调度与信号头改动获多位维护者 Reviewed-by，v4 只做措辞/标题修正、无方向性争议。*blocking_issues*：无。*next_action*：等待 sched/信号子系统维护者（Peter Zijlstra 等）最终 pickup，关注是否会因横跨 mm/kernel/fs 多子系统而要求拆分或按树分拍合入。

## 效果评估
纯代码清理，无功能变化、无性能数据。收益体现在可维护性与安全性（RCU 读锁作用域收敛，减少漏放锁/提前返回的隐患）。

## 我可以参与的点
当前阶段暂无明显参与空间（已获多位维护者背书、只差最终 pickup），可持续观察是否被要求按子系统拆分或合入哪棵树。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921092101.89285-1-ye.liu@linux.dev/

---
id: sched-20260921-002
date: '2026-09-21'
subject: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260921092101.89285-1-ye.liu@linux.dev>'
lore_url: 'https://lore.kernel.org/all/20260921092101.89285-1-ye.liu@linux.dev/'
authors:
  - 'Ye Liu'
maintainers_involved:
  - 'Michal Hocko'
  - 'Oleg Nesterov'
current_version: v4
patch_series:
  - version: v4
    msgid: '<20260921092101.89285-1-ye.liu@linux.dev>'
    date: '2026-09-21'
    summary: '修正 patch 5 标题/提交信息错误，确认 v3 三处 sashiko-bot 告警为误报'
    review_outcome: 'Michal Hocko Acked-by，SJ Park/Gregory Price/Oleg Nesterov/Lorenzo Stoakes Reviewed-by'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待调度/信号维护者最终 pickup，关注是否按子系统拆分合入'
contribution_opportunities: []
generated_at: '2026-09-22T01:10:00'
source_email_count: 3
related_articles:
  - sched-20260911-012
tags:
  - cfs
---
