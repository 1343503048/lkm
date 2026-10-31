---
id: sched-20261030-005
date: 2026-10-30
subject: 'sched/debug: Introduce per-CPU debugfs files'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261030151307.768523-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/all/20261030151307.768523-1-atomlin@atomlin.com/
authors:
- Aaron Tomlin
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v11
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 无技术阻塞，卡在维护者（Peter/Juri/Ingo/Vincent）对 v11 的合入动作
  next_action: 等维护者将 v11 合入 tip/sched/core
contribution_opportunities:
- kind: review
  description: 读 patch 5 的 for_each_leaf_cfs_rq_rcu() 熔断上限，确认 list churn 下无 RCU stall
- kind: testing
  description: 大批量 cgroup + CONFIG_SCHED_DEBUG 下读 per-CPU debug 文件，观察截断提示与稳定性
generated_at: '2026-10-31T09:00:00'
source_email_count: 19
related_articles:
- sched-20260728-004
- sched-20260809-001
- sched-20260827-001
- sched-20260828-005
- sched-20261029-002
tags:
- sched_debug
title: 'sched/debug: Introduce per-CPU debugfs files'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-004-sched-debug-introduce-per-cpu-debugfs-files.html">sched-20260728-004</a> / 20260809-001（v1–v3）：Aaron Tomlin 发起「按 CPU 暴露调度调试信息」系列，最初单补丁把 `/proc/sched_debug` 部分内容下放到 per-CPU debugfs 文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，并顺手修掉并发读 `/sys/kernel/debug/sched/debug` 时几处 lockless 解引用 UAF。
- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-001-sched-annotate-rq-rd-with-rcu-and-update-lockless-readers.html">sched-20260827-001</a> / 20260828-005（v8/v9）：扩成 6 补丁，前置补丁给 `struct rq->rd` 补 `__rcu` 并引入 `rcu_dereference_root_domain()` helper；v9 修掉 Sashiko 查出的 `dl_task_needs_bw_move()` suspicious RCU usage。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-002-sched-debug-introduce-per-cpu-debugfs-files.html">sched-20261029-002</a>（RESEND v9）：声明 cleanly applies 于 tip/sched/core `b99b7f60c5b4`，无功能变更，向维护者重新 ping。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-005-sched-debug-introduce-per-cpu-debugfs-files.html">sched-20261030-005</a>（今天）：作者同一天连发 **v10** 与 **v11**（均 0/6 封面 + 6 补丁）。v10 吸收 Sparse 报告——`rq->rd = rd` 改用 `rcu_assign_pointer(rq->rd, rd)` 消除 address-space 警告；K Prateek Nayak 对 v10 密集提 style nit（rq_rd()/cpu_rd() 简写、rd 顶部初始化、reverse x-mas、guard(rq_lock_irqsave)、删冗余警告），v11 据此微调并丢弃冗余 `RCU_LOCKDEP_WARN`。仍在等 Peter/Juri/Ingo/Vincent 收取。

## 背景与问题
（承接 v1–v9）两类既有问题不变：

1. **调试效率**：排查特定 CPU 的延迟异常时 `/sys/kernel/debug/sched/debug` 会 dump 所有 online CPU，无法定点看单个 runqueue；per-CPU debug 文件（offline 返回 `-ENODEV`）解决定位问题。
2. **内存安全/并发正确性**（5 个补丁）：`print_dl_rq()` 无锁解引用 `cpu_rq(cpu)->rd`、`print_cpu()` 无锁解引用 `rq->curr`、`sched_show_numa()` 的 `p->mm` TOCTOU+UAF、`print_cfs_stats()` 用非 RCU 的 `list_for_each_entry_safe()` 遍历 `leaf_cfs_rq_list`。今日无新背景，是 v10/v11 的技术打磨与重 ping。

## 技术方案
（承接 v9，6 补丁结构不变，今日打磨）关键演进：

- **patch 1** 写侧 `rq_attach_root()` 新增 `rcu_assign_pointer(rq->rd, rd)`（回应 Sparse 在 `topology.c:512` 的 `incorrect type in assignment` 警告），读侧统一 `rcu_dereference_root_domain()`。
- **patch 2/3/4**（`print_dl_rq`/`print_cpu`/`sched_show_numa`）与 v9 相同：`guard(rcu)()` + `rcu_dereference`、`rcu_read_lock()`、`task_lock()`。
- **patch 5** `print_cfs_stats()`：新增 `for_each_leaf_cfs_rq_rcu()`（`list_for_each_entry_rcu`）、`guard(rcu)()`、每 CPU 迭代上限熔断 + 截断提示。
- **patch 6** `debugfs_cpu_init()` 建 per-CPU debug 文件。
- **K Prateek 的 nit（v11 部分吸收）**：`rcu_dereference_root_domain()` 太啰嗦，建议 `rq_rd(rq)`/`cpu_rd(cpu)` 简写；`rd` 顶部初始化；reverse x-mas；`guard(rq_lock_irqsave)(rq)` 化。Aaron 回：显式 helper 名是有意为之（镜像 `rcu_dereference_sched_domain()`、让 RCU 读临界区要求一眼可见），简写会模糊同步要求，故不引入 `rq_rd`；`guard(rq_lock)` 迁移留作独立 tree-wide 清理；冗余 `RCU_LOCKDEP_WARN` 会删（`rcu_dereference_all_check()` 已覆盖）。`debugfs_create_dir()` 返回值不检查是内核惯例/有意设计，维持现状。

## 版本演进与当前进展
*current_version: v11*（2026-10-30 发出，msgid `<20261030151307.768523-1-atomlin@atomlin.com>`）。v10 → v11 主要为 style/清理：吸收 `rcu_assign_pointer`、`rd` 声明位置与 reverse x-mas 微调、删除冗余 RCU 警告；结构性无变更。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak（非 maintainer，深入 review）**：6 封 review 覆盖 patch 1、6 等的 style nit 与 error-handling 疑问。
- **Aaron Tomlin（作者）**：对多数 nit 采纳或明确拒绝并给出理由，态度专业。
- **未解决/待观察**：实质合入仍卡在**维护者（Peter/Juri/Ingo/Vincent）对 v10/v11 的最终收取**——本系列 7 月以来多轮重 ping 仍未获 apply；`guard(rq_lock_irqsave)` 迁移被推后。

## 合入评估
*likelihood=high*。方向获普遍认可、Sparse/RCU 问题已收敛、应用与 tip 干净，唯一缺的是维护者合入动作；但鉴于跨月多次重 ping 未合，存在「优先级不高被继续搁置」的风险。*blocking_issues*：无技术阻塞，卡在维护者带宽与优先级。*next_action*：等 Peter/Juri/Ingo/Vincent 合入 tip/sched/core。

## 效果评估
无性能数据；系列价值主要在正确性（消除 debugfs 读路径的 UAF/RCU stall 隐患）与调试可用性（per-CPU 定点查看）。K Prateek 未提出功能性问题，v11 已 cleanly applies。

## 我可以参与的点
- **review**：读 per-CPU debugfs 输出与本系列 patch 5 的 `for_each_leaf_cfs_rq_rcu()` 熔断上限实现，确认 list churn 下无回跳/长遍历。
- **testing**：在启用 `CONFIG_SCHED_DEBUG` + 大量 cgroup 的场景读 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，观察截断提示与 RCU stall 是否消失。

## 参考链接
- lore thread（v11 封面）: https://lore.kernel.org/all/20261030151307.768523-1-atomlin@atomlin.com/
