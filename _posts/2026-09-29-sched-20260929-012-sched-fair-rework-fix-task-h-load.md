---
id: sched-20260929-012
date: '2026-09-29'
subject: 'sched/fair: Rework/fix task_h_load()'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260929084923.092062266@infradead.org>
lore_url: https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: <20260828074059.232353141@infradead.org>
  date: '2026-08-28'
  summary: 4 补丁，4/4 重做 task_h_load()，引入 for_each_sched_entity_bl() 触发启动 panic
  review_outcome: Chen Yu/Vincent 双复现 panic；Peter 给 fixlet 后「I'll fold it in」
- version: v2
  msgid: <20260929084923.092062266@infradead.org>
  date: '2026-09-29'
  summary: 修复 FAIR_GROUP_SCHED=n 编译失败与运行期失败；back-link 移入 for_each_sched_entity；重做
    h_load 更新；rebase 到当前树
  review_outcome: 无新回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 的 FAIR_GROUP_SCHED 运行期修复尚未见 Vincent 实测确认
  - 1/4-3/4 前置清理需在 v2 语境下重新审阅
  next_action: 等 Vincent 对 v2 重新测试确认无 panic，其余补丁 review 后由 Peter 收进 sched/core
contribution_opportunities:
- kind: testing
  description: 在 192 核 + autogroup + +cpu 场景验证 v2 不再启动 panic（两种 GROUP_SCHED 配置）
- kind: review
  description: 审计 v2 for_each_sched_entity_bl 与 4/4 rework 的 clobber 残留与 h_load 更新线程安全
generated_at: '2026-09-30T01:15:00'
source_email_count: 5
related_articles:
- sched-20260902-007
- sched-20260831-003
tags:
- cfs
title: 'sched/fair: Rework/fix task_h_load()'
layout: article
---

> **subject**：`sched/fair: Rework/fix task_h_load()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/31/sched-20260831-003-sched-fair-rework-fix-task-h-load.html">sched-20260831-003</a>：Peter Zijlstra 8/28 发的 4 补丁系列中 `4/4` 重做 `task_h_load()`，8/31 当天只剩注释措辞分歧，方向与实现均无异议。
- <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>：Chen Yu 报告整套在 192 核机器启动即 panic，Peter 定位到 `for_each_sched_entity_bl()` 改写循环变量导致 `cfs_rq->curr = se` 写到中间层 cfs_rq，给出移动遍历位置的 fixlet，Vincent 独立复现并确认「this fixes it for me too」。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>（今天）：Peter 重发 v2（完整 4 补丁，1/4–3/4 为前置清理、4/4 为 rework）——修复 `FAIR_GROUP_SCHED=n` 编译失败与 `FAIR_GROUP_SCHED` 运行期失败（Vincent 报的 panic），并 rebase 到当前树。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>）`task_h_load()` 计算任务沿 cgroup 调度层级的「层级负载」。旧实现有多个问题：hierarchy 遍历因 back-link 状态易 race 而破碎（本应在 rq->lock 下用但缺乏断言，使用范围蔓延后违反）；jiffies 限速与 HZ 相关而非底层 PELT 衰减；更新绑定在 `task_h_load()` 使用点上导致 `cfs_rq->h_load` 常不新鲜、sched/debug 输出近乎无用。v1 rework 引入的 `for_each_sched_entity_bl()` 会在 `set_next_task_fair()` 里 clobber `se`/`cfs_rq`，触发启动 panic（Chen Yu、Vincent 双独立复现）。

## 技术方案

（承接）v2 的 rework 核心推进：

- **1/4 `sched: Rename/clarify sched_class::task_tick(.queued) argument`**：把 `task_tick()` 里表示 hrtick 的参数 `@queued` 更名为 `@hrtick`（纯澄清，遍布 deadline/ext/fair/idle/rt/sched.h）。
- **2/4 `sched/fair: Fold cfs_rq_of(se) into for_each_sched_entity()`**：把几乎所有 `for_each_sched_entity()` 循环开头那句 `cfs_rq = cfs_rq_of(se)` 折进宏本身，为透明跟踪 backlink 铺路。
- **3/4 `sched/fair: Extend for_each_sched_entity() with a back-link`**：新增 `for_each_sched_entity_bl()`，在 `cfs_rq` 上留 backlink 轨迹以便沿层级往回走（暂无使用者，单独拆出因实现较 tricky）——从机制上规避了 v1 里遍历宏 clobber 循环变量的问题。
- **4/4 `sched/fair: Rework/fix task_h_load()`**：把 back-link 跟踪移入 `for_each_sched_entity()`（任何该宏的循环都建立回退路径），在 enqueue/dequeue/set_next/tick 这些持 rq->lock 的位点（可选地）重算 `cfs_rq->h_load`，使活跃 cgroup 的 `h_load` 保持新鲜；`__update_blocked_fair()` 对所有 cgroup 更新 `h_load`；把 jiffies 限速换成绑定 PELT 衰减的限速（`last_h_load_update` 与 `avg.last_update_time` 对齐 segment 判断）。

v2 changelog：修复 `FAIR_GROUP_SCHED=n` 编译失败、修复 `FAIR_GROUP_SCHED` 运行期失败（Vincent）、rebase 到当前树（git 分支 `git://git.kernel.org/.../peterz/queue.git sched/task_h_load`）。

## 版本演进与当前进展

- v1（8/28，`<20260828074059.232353141@infradead.org>`）：4 补丁，4/4 rework 引入 panic（对应 <a class="article-ref" href="/lkm/2026/08/31/sched-20260831-003-sched-fair-rework-fix-task-h-load.html">sched-20260831-003</a> / <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>）。
- v2（9/29，`<20260929084923.092062266@infradead.org>`）：4 补丁齐全（1/4–4/4 均在当日缓存），修复构建/运行期失败并重做 back-link 机制。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（作者/维护者）：按 v1 期间 Vincent 的运行期失败反馈重发 v2，changelog 明确「Fixed FAIR_GROUP_SCHED runtime fail (Vincent)」。
- **Vincent Guittot**（sched/fair 维护者，v1 期间）：独立复现 panic 并报「Some of my platforms didn't crash until I added +cpu in cgroup.sub_controller」，为 v2 的修复提供了触发条件。
- 当日无新回帖。v2 把此前「clobber se/cfs_rq」的根因从机制上消解（back-link 移入宏），但 v2 的实机验证尚未见（Vincent 的 runtime fail 修复声明待实测确认）。

## 合入评估

*likelihood=high*。补丁出自 sched 核心维护者本人，v2 已把 v1 的 panic 根因从机制上重做并声称修复两类失败，方向与实现此前已收敛。*blocking_issues*：v2 的 `FAIR_GROUP_SCHED` 运行期修复尚未见 Vincent 重新实测确认；1/4–3/4 前置清理（尤其 3/4 的 `for_each_sched_entity_bl()` 宏）在 v2 语境下需重新审阅。*next_action*：等 Vincent 对 v2 重新测试确认无 panic，及系列其余补丁的 review 后，由 Peter 收进 sched/core。

## 效果评估

无 benchmark 数字；效果证据来自 v1 期间的正确性（Chen Yu 192 核 GPF、Vincent 独立复现 → v2 声称修复）。层级负载计算本身与负载均衡质量收益未见量化。

## 我可以参与的点

- `testing`：在 192 核物理机 + autogroup + `+cpu` 场景下验证 v2 不再启动 panic（尤其是 `FAIR_GROUP_SCHED=n` 与 `=y` 两种配置）。
- `review`：审计 v2 的 `for_each_sched_entity_bl()`（3/4）与 4/4 的 rework，确认 back-link 在新机制下无 clobber 残留、`h_load` 更新频率绑定 PELT 衰减后线程安全。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
- lore（v2 4/4）: https://lore.kernel.org/all/20260929085320.337703476@infradead.org/
- v1 线程根: https://lore.kernel.org/all/20260828074059.232353141@infradead.org/
