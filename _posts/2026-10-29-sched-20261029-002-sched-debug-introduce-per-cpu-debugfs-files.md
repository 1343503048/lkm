---
id: sched-20261029-002
date: 2026-10-29
subject: 'sched/debug: Introduce per-CPU debugfs files'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261029132511.712391-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/all/20261029132511.712391-1-atomlin@atomlin.com/
authors:
- Aaron Tomlin
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v9
patch_series:
- version: v1
  msgid: null
  date: 2026-07-28
  summary: 单补丁：per-CPU debugfs 文件 sched/cpu/cpu<N>/debug，offline 返回 -ENODEV
  review_outcome: Peter Zijlstra + Zhan Xusheng 建议围绕大 SMP 拓扑定向调试重写动机
- version: v3
  msgid: null
  date: 2026-08-09
  summary: per-CPU debugfs + 修复并发读取的 UAF
  review_outcome: under_review，暂无维护者明确表态
- version: v8
  msgid: null
  date: 2026-08-27
  summary: 引入 rcu_dereference_root_domain() helper，替换错误用法
  review_outcome: Peter Zijlstra 指出 rcu_dereference_protected 用法错误，要求 helper 化
- version: v9
  msgid: <20261029132511.712391-1-atomlin@atomlin.com>
  date: 2026-10-29
  summary: RESEND v9：相对 8/27 v9 无功能变更，仅重新验证 applies cleanly against tip/sched/core
    b99b7f60c5b4
  review_outcome: 今日无人回帖，等待维护者收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Peter/Juri/Ingo 合入 tip/sched/core
contribution_opportunities:
- kind: review
  description: 对照主干核对 rcu_dereference_root_domain() 替换是否还有漏网的 rq->rd 直读
- kind: testing
  description: 在 CONFIG_PROVE_RCU=y 下反复 hotplug/cpuset 重分区并读写 per-CPU debugfs，回帖 Tested-by
generated_at: '2026-10-30T09:30:00'
source_email_count: 7
related_articles:
- sched-20260728-004
- sched-20260809-001
- sched-20260827-001
- sched-20260828-005
tags:
- sched_debug
title: 'sched/debug: Introduce per-CPU debugfs files'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-004-sched-debug-introduce-per-cpu-debugfs-files.html">sched-20260728-004</a> / 20260809-001（v1–v3）：Aaron Tomlin 发起「按 CPU 暴露调度调试信息」系列，最初是单补丁——把 `/proc/sched_debug` 的一部分内容下放到 per-CPU debugfs 文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，并顺手修掉并发读取 `/sys/kernel/debug/sched/debug` 时几处 lockless 解引用导致的 UAF。
- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-001-sched-annotate-rq-rd-with-rcu-and-update-lockless-readers.html">sched-20260827-001</a> / 20260828-005（v8/v9）：系列扩成 6 补丁，新增前置补丁给 `struct rq->rd` 补 `__rcu` 标注、引入 `rcu_dereference_root_domain()` helper，统一 `kernel/sched/` 里所有无锁直读 `rq->rd` 的路径；v9 修掉 Sashiko 查出的 `dl_task_needs_bw_move()` `suspicious RCU usage`。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-002-sched-debug-introduce-per-cpu-debugfs-files.html">sched-20261029-002</a>（今天）：作者发 **RESEND v9**（0/6 封面 + 6 补丁），声明已对照 tip/sched/core 最新 commit `b99b7f60c5b4` 重新验证、**cleanly applies**，相对 8/27 的 v9 **无任何功能或语义变更**——本质是一次向维护者（Peter/Juri/Ingo/Vincent）的重新 ping，等待收取。

## 背景与问题
（承接 v1–v9）系列要解决两类既有问题：

1. **调试效率**：排查特定 CPU 的延迟异常/调度问题时，读 `/sys/kernel/debug/sched/debug` 会 dump 所有 online CPU，无法定点看某个 runqueue；新增 `/sys/kernel/debug/sched/cpu/cpu<N>/debug` 按需只 `print_cpu()` 目标 CPU（offline 时返回 `-ENODEV`）。
2. **内存安全/并发正确性**（5 个补丁）：`print_dl_rq()` 无锁解引用 `cpu_rq(cpu)->rd`（hot-unplug/cpuset 重分区时 `rq_attach_root()` 经 `call_rcu` 释放 root_domain，可 UAF）；`print_cpu()` 无锁解引用 `rq->curr`（任务并发退出时 `put_task_struct()` → `call_rcu` 释放，可 UAF）；`sched_show_numa()` 的 `p->mm` TOCTOU + UAF；`print_cfs_stats()` 用非 RCU 的 `list_for_each_entry_safe()` 遍历 `leaf_cfs_rq_list`（list churn 下可回跳/无限遍历触发 RCU stall）。

## 技术方案
（承接 v9）6 补丁结构（RESEND 无变更）：

- **patch 1** `sched: Annotate rq->rd with __rcu and update lockless readers`：给 `struct rq->rd` 加 `__rcu`，引入 `rcu_dereference_root_domain()` helper（对称于 `rcu_dereference_sched_domain()`，便于 grep），把 `kernel/sched/` 下所有直读 `rq->rd` 换成该 helper；`sched_init()` 用 `RCU_INIT_POINTER` 初始化 `rq->sd`/`rq->rd`。
- **patch 2** `print_dl_rq()`：写侧 `rq_attach_root()` 用 `rcu_assign_pointer()` 发布；读侧 `guard(rcu)()` + `rcu_dereference`。
- **patch 3** `print_cpu()`：`rcu_read_lock()` + `rcu_dereference(rq->curr)`。
- **patch 4** `sched_show_numa()`：`task_lock(p)`/`task_unlock(p)` 包裹 `p->mm` 检查与解引用，消除 TOCTOU+UAF。
- **patch 5** `print_cfs_stats()`：新增 `for_each_leaf_cfs_rq_rcu()` 宏（`list_for_each_entry_rcu`）、`guard(rcu)()`、每 CPU 迭代上限 `SCHED_DEBUG_MAX_ITER`（4096）熔断 + 截断提示。
- **patch 6**：`debugfs_cpu_init()` 建 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`。

## 版本演进与当前进展
*current_version: v9 (RESEND)*（2026-10-29，cover `<20261029132511.712391-1-atomlin@atomlin.com>`）。

本 RESEND 相对 8/27 v9 **无功能/语义变更**，仅重新验证并声明 cleanly applies against tip/sched/core `b99b7f60c5b4`。作者在封面完整复述 v1→v8 的 changelog：v2 起加 RCU 读锁修 `print_cpu()`/`print_dl_rq()` 并引入 `for_each_leaf_cfs_rq_rcu()`（Peter Zijlstra + Zhan Xusheng 方向）；v4 起新增 `__rcu` 前置补丁、`task_lock()` 修 `sched_show_numa()`、`SCHED_DEBUG_MAX_ITER` 提到 4096；v7 起按 Peter Zijlstra 意见用 `rcu_dereference_root_domain()` 替换错误的 `rcu_dereference_protected()`（Vincent Guittot 要求恢复 `check_update_overutilized_status()` 注释）；v9 补 `guard(rcu)()` 到 `dl_task_needs_bw_move()` 等四处遗漏。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（维护者）**：v7 阶段指出 `rcu_dereference_protected(..., lockdep_is_held(&rq->__lock))` 用法错误，要求换成在 `sched_domains_mutex` 或 RCU-sched 读侧临界区下验证的 `rcu_dereference_root_domain()` helper——已落实；v1 阶段与 Zhan Xusheng 共同把 commit 动机 reframe 为「大 SMP 拓扑上的定向交互调试」。
- **Vincent Guittot（维护者）**：要求恢复 `check_update_overutilized_status()` 里的注释——已落实。
- 其余 reviewer（Daniel Vacek、K Prateek Nayak、Zhan Xusheng）意见均已吸收进 v4–v9.
- **今日无人回帖**：RESEND 是为模型对齐（applies cleanly）后重新 ping，讨论焦点仍是「系列已就绪、等维护者收取」。

## 合入评估
*likelihood=high*。系列经 v1–v9 多轮 review，Peter Zijlstra / Vincent Guittot 的实质意见均已落实，v9 已解决全部已知 RCU 正确性问题，今日 re-verify 声称对 tip/sched/core cleanly applies。*blocking_issues*：无实质技术分歧，唯一卡点是「尚无维护者显式 Ack/合并」，系列自 8/27 v9 起一直处于待收取状态。*next_action*：等待 Peter/Juri/Ingo 之一合入 tip/sched/core；若继续无响应，作者可能需再次 resend 或在 sched 会议窗口前提醒。

## 效果评估
无性能数据——系列是调试能力（per-CPU debugfs）+ 内存安全修复，正确性由 Sashiko 静态分析（`Reported-by: sashiko-bot`）与作者的 virtme-ng 复现驱动；v8→v9 的 `dl_task_needs_bw_move()` `suspicious RCU usage` 即作者用 virtme-ng 实测复现后修复。per-CPU 文件带来的「定点调试效率提升」属主观判断，未见量化数据。

## 我可以参与的点
- **review**：可对照 `/home/zq/code/linux/` 的 `kernel/sched/debug.c`、`topology.c` 核对 patch 1–5 的 `rcu_dereference_root_domain()` 替换是否还有漏网的 `rq->rd` 直读（Sparse 未覆盖的路径）。
- **testing**：在 `CONFIG_PROVE_RCU=y` + 反复 CPU hotplug/cpuset 重分区下读写 `/sys/kernel/debug/sched/cpu/cpu<N>/debug` 与 `/sys/kernel/debug/sched/debug`，确认无 UAF/RCU 告警，回帖 Tested-by 可加速合入。

## 参考链接
- lore thread（RESEND v9 cover）: https://lore.kernel.org/all/20261029132511.712391-1-atomlin@atomlin.com/
- v9 原始提交（8/27）: https://lore.kernel.org/lkml/20260827221809.988394-1-atomlin@atomlin.com/（封面正文所引）
- tip/sched/core 当前基线 commit: b99b7f60c5b4（封面声明）
