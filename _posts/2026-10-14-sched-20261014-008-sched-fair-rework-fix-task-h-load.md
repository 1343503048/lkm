---
id: sched-20261014-008
subject: 'sched/fair: Rework/fix task_h_load()'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260929084923.092062266@infradead.org>
lore_url: https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- Vincent Guittot
current_version: v2
patch_series:
- version: v2
  msgid: <20260929084923.092062266@infradead.org>
  date: 2026-09-29
  summary: 4 补丁 v2：back-link 移入 for_each_sched_entity()、持锁重算 h_load
  review_outcome: Vincent 全量 Reviewed-by（3/4 附边界保留）；Kayra 1/4 Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 3/4 back-link 是否该独立成补丁待 Peter 定夺
  next_action: Peter 回应 3/4 边界后进入 tip/sched/core 收取
contribution_opportunities:
- kind: review
  description: 评估 3/4 back-link 与 task_h_load 重做的耦合、是否应独立成补丁
- kind: testing
  description: 混合负载下回归验证 v2 的 task_h_load() 与 panic 场景
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 5
related_articles:
- sched-20260902-007
- sched-20260929-012
- sched-20260930-011
- sched-20261002-011
tags:
- cfs
- cgroup
title: 'sched/fair: Rework/fix task_h_load()'
layout: article
---

> **subject**：sched/fair: Rework/fix task_h_load()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>：Peter Zijlstra 4 补丁系列中 `4/4` 重做 `task_h_load()`，v1 在 `set_next_task_fair()` 里 clobber `se`/`cfs_rq`，致 192 核启动 panic（Chen Yu、Vincent 双复现）。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>：Peter 重发 v2（完整 4 补丁），修复编译/运行期失败，back-link 机制移入 `for_each_sched_entity()`。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>：多名 reviewer 澄清 v2 设计语义（删除 `update_cfs_rq_h_load()` 是初衷、root 更新频率变化有意、`h_load` 懒传播）。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-011-sched-fair-rework-fix-task-h-load.html">sched-20261002-011</a>：Kayra 给出 root-cfs_rq 捷径 sketch（untested），Peter 未回应。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-008-sched-fair-rework-fix-task-h-load.html">sched-20261014-008</a>（今天）：**Vincent Guittot 对 v2 全部 4 个补丁给出 `Reviewed-by`**（对 3/4 附「不确定 back-link 扩展是否该放在这个 patch 里」的保留意见）；Kayra 也对 1/4 给 `Reviewed-by`（附 task_tick_stop 的 nit）。系列进入合入前的最后收尾。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>）`task_h_load()` 计算任务沿 cgroup 调度层级的层级负载。v2 把 back-link 跟踪移入 `for_each_sched_entity()` 并在持锁位点重算 h_load；09-30 讨论确认了 root 更新变少、懒传播、`update_cfs_rq_h_load()` 删除三处取舍。今日为 v2 的 review 收官，无新背景。

## 技术方案
（承接 v2 主体）今日无新代码，属 review 收官：Vincent 对 1/4（task_tick 参数改名）、2/4（`cfs_rq_of(se)` 折入 `for_each_sched_entity()`）、3/4（back-link）、4/4（重做 `task_h_load()`）全部 `Reviewed-by`；对 3/4 备注「Not sure this should be part of this patch」（back-link 扩展或可独立成补丁）。Kayra 对 1/4 给出 `Reviewed-by`，并指 nits（`task_tick_stop()` 被跳过、以及 grep 所见的一处细节）。

## 版本演进与当前进展
仍为 v2（9/29 发，4 补丁）。今日起 Vincent 全量 `Reviewed-by` + Kayra `Reviewed-by`；此前 10-02 Kayra 的 root 捷径 sketch 未见吸收，无 v3。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（sched 维护者，今日）：v2 四补丁全数 `Reviewed-by`；唯一保留是 3/4 的 back-link「是否该并入此 patch」。
- **Kayra Cizmeci**（reviewer，今日）：1/4 `Reviewed-by` + 小 nit（task_tick_stop 被跳过）。
- **Peter Zijlstra**（作者/维护者）：当日未回帖。
- 无 NAK；唯一待决是 3/4 的补丁边界问题（back-link 是否拆出）。

## 合入评估
*likelihood=high*。v2 由 Peter 本人署名、修复 192 核 panic 实证故障，如今获 Vincent 全量 `Reviewed-by`，属收取前最后阶段。*blocking_issues*：3/4 back-link「是否该并入」的边界待 Peter 定夺；Peter 本人对后续动作未明。*next_action*：Peter 回应 3/4 边界（就地保留或拆出），随后进入 tip/sched/core 收取。

## 效果评估
无新 benchmark；本系列为正确性修复（v1 panic → v2 修复），收益为机制性而非性能数字。Kayra 10-02 的 root 捷径曾提「少一次除法与陈旧读」，无量化。

## 我可以参与的点
- review：评估 3/4 back-link 扩展与 `task_h_load()` 重做的耦合度，判断是否如 Vincent 所言应独立成补丁。
- testing：在深 cgroup 层级 + 根队列混合负载下跑 v2，验证 `task_h_load()` 返回值与调度决策无异常（此前 panic 场景重点回归）。

## 参考链接
- Peter 的 v2 cover：https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
- Vincent 对 4/4 的 RB：https://lore.kernel.org/all/CAKfTPtCrb4_JkH=-hnoabrqix14B+kizwLDWnuOaLa6374tfxw@mail.gmail.com/
