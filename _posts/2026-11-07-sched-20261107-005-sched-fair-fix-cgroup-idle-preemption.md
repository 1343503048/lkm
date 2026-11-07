---
id: sched-20261107-005
date: '2026-11-07'
subject: 'sched/fair: Fix cgroup::idle preemption'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261105165525.011876858@infradead.org>
lore_url: https://lore.kernel.org/all/20261107113639.GK2668200@noisy.programming.kicks-ass.net/
authors:
- Peter Zijlstra
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261105165525.011876858@infradead.org>
  date: '2026-11-06'
  summary: 3 补丁：guard 清理 + cfs_rq::idle 祖先求和 + RFC 携带 Vincent 的 idle 组抢占修复
  review_outcome: patch 1 Reviewed-by；patch 2 有竞态需 v2；patch 3 find_matching_se 被作者质疑
upstream_commit: null
fixes_commit: 85570f10a4c6
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - patch 3 的 find_matching_se 语义待作者自己敲定
  - patch 2 是否补 Fixes 标签待定
  next_action: 作者敲定 patch 3 方向并决定 patch 2 的 Fixes 标签
contribution_opportunities:
- kind: review
  description: 独立评估 patch 3 find_matching_se 语义是否合理或存在更简单实现
- kind: testing
  description: 验证 patch 2 v2 在新组创建期间父组 idle 翻转场景下 h_nr_idle 一致性
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 5
related_articles:
- sched-20261106-003
tags:
- cfs
- eevdf
- cgroup
title: 'sched/fair: Fix cgroup::idle preemption'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-003-sched-fair-fix-cgroup-idle-preemption.html">sched-20261106-003</a>：Peter Zijlstra 发出 3 补丁系列修复 cgroup SCHED_IDLE 任务组的抢占问题：patch 1 用 guard 清理 `sched_group_set_idle()`、patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」、patch 3（RFC）携带 Vincent Guittot 的 `sched/eevdf: Fix sched idle task group preemption` 修复。Kayra 指出 patch 2 有任务组创建竞态（Peter 确认需 rq->lock 并给修正）、并追问 `se_is_idle()` 任务路径处理。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-005-sched-fair-fix-cgroup-idle-preemption.html">sched-20261107-005</a>（今天）：Peter 发出 **patch 2 的 v2**（`sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle`，并入竞态修正）。Kayra 给 patch 2 v2 与 patch 3 RFC 双 Reviewed-by（称「我最初的老顾虑已解决」），并建议 patch 2 补 Fixes 标签；Vincent Guittot 给 patch 1 Reviewed-by，并确认 patch 2「对 `wakeup_preempt_sched_idle()` 第一处检查是必要的，可避免对 `find_matching_se()` 的无谓调用」。系列明显收敛，patch 1/2 基本可收，patch 3 仍为 RFC。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-003-sched-fair-fix-cgroup-idle-preemption.html">sched-20261106-003</a>）cgroup 标为 `SCHED_IDLE` 的任务组应当「不抢占、也不抢占别的任务」，但 EEVDF 扁平化后并入单一 runqueue（commit `85570f10a4c6`）改变了抢占路径解析层级的方式，导致 idle 任务组抢占语义出错（Jakub Okoński 报告）。Peter 重拾该问题，把 Vincent 此前单独迭代的修复放在系列末尾改造。

今日进展：patch 2 的竞态修正落地为 v2；Kayra 此前对 patch 2 的「任务组创建竞态」顾虑与对 patch 3 的「idle 组内非 idle 策略任务行为」顾虑均得到解决。

## 技术方案

（承接）三补丁方案不变：

- **Patch 1**（`Use guard in sched_group_set_idle()`）：scope-guard 清理锁处理，纯重构——今日 Vincent Guittot 给 Reviewed-by。
- **Patch 2 v2**（`Make cfs_rq::idle the sum of ancestor tg::idle`）：让 `cfs_rq->idle` 累积整棵子树的 idle 状态，使「任一祖先 idle」时 `cfs_rq_is_idle()` 成立。v2 把 `cfs_rq->idle` 赋值挪进持 rq->lock 的路径（修 Kayra 指出的新组创建竞态：父组 idle 先置 1 再置 0 会得到「GB idle=-1 而 GA idle=0」的失真状态、腐坏 `h_nr_idle`）。Kayra Reviewed-by 并建议补 Fixes 标签；Vincent 确认其对 `wakeup_preempt_sched_idle()` 第一处检查的必要性（避免对 `find_matching_se()` 的无谓调用）。
- **Patch 3**（RFC，`sched/eevdf: Fix sched idle task group preemption`，From: Vincent）：新增 `find_matching_se()` 把 `se`/`pse` 上溯到同一父节点下的兄弟实体比较 idle 状态决定抢占。Kayra 今日 Reviewed-by（「我最初的老顾虑已解决」）。

## 版本演进与当前进展

*current_version: v1（patch 1/3）；patch 2 已出 v2（2026-11-07）*。今日 Peter 发 patch 2 v2（msgid 20261107113639.GK2668200@noisy.programming.kicks-ass.net），其余无新版本。patch 3 仍为 RFC。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**：patch 2 v2 与 patch 3 RFC 均 Reviewed-by，并建议 patch 2 补 Fixes 标签（「我认为这更是一次修复」）；「我最初的老顾虑已解决」表明此前对 patch 3 的疑问已消除。
- **Vincent Guittot**（sched/fair 维护者）：patch 1 Reviewed-by；并解释 patch 2 对 `wakeup_preempt_sched_idle()` 第一处检查的必要性。

Peter（作者兼维护者）此前在 cover 中对 `find_matching_se()` 思路的保留意见（「把子树标 idle 本质是『别管它』，再去关心它在某层级怎么被抢占就很怪」）今日未见进一步表态。无 NAK。

## 合入评估

*likelihood=medium*。patch 1/2 已获 Kayra+Vincent 双 Reviewed-by、竞态修正落地，收敛明显；但 patch 3 仍为 RFC，且 Peter 本人对 `find_matching_se()` 的语义保留未消解，整个系列要合入仍需 patch 3 定调。*blocking_issues*：① patch 3 的 `find_matching_se()` 语义待作者（Peter）自己敲定；② patch 2 是否补 Fixes 标签待定。*next_action*：作者敲定 patch 3 方向（可能拆分 RFC 或放弃 find_matching_se 改造），并决定 patch 2 的 Fixes 标签。

## 效果评估

无量化性能数据。作者此前用 LLM 生成的测试用例验证「现在真的能用了」（cover 原文），patch 3 Fixes 指向 `85570f10a4c6` 回归、Reported-by Jakub Okoński。今日为评审收敛，无新 benchmark。

## 我可以参与的点

- **review**：跟进 patch 3 的 `find_matching_se()` 语义——这是 Peter 自己存疑、今日仍未定调的点，值得独立评估「上溯兄弟实体比较 idle」是否比「子树整体 idle」更合理，或是否存在更简单的等价实现。
- **testing**：验证 patch 2 v2 在「新任务组创建期间父组 idle 反复翻转」的场景下 `h_nr_idle` 是否始终一致，确认竞态修正充分。

## 参考链接

- lore thread（patch 2 v2）: https://lore.kernel.org/all/20261107113639.GK2668200@noisy.programming.kicks-ass.net/
- lore thread（系列 cover）: https://lore.kernel.org/all/20261105165525.011876858@infradead.org/
- Vincent 对 patch 1 的 Reviewed-by: https://lore.kernel.org/all/CAKfTPtCtEXmhi-b1kjmzJ08anyLUwqJKMGtGnVKBaEZ=hufThw@mail.gmail.com/
