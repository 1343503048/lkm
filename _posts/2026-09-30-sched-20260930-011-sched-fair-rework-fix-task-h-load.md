---
id: sched-20260930-011
date: '2026-09-30'
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
  review_outcome: Chen Yu/Vincent 双复现 panic
- version: v2
  msgid: <20260929084923.092062266@infradead.org>
  date: '2026-09-29'
  summary: 修复 FAIR_GROUP_SCHED=n 编译失败与运行期失败；back-link 移入 for_each_sched_entity；重做
    h_load 更新
  review_outcome: 09-30 Peter/Prateek/Kayra 澄清设计取舍，无新阻塞；未发现新问题
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 的 FAIR_GROUP_SCHED 运行期修复尚未见 Vincent 实测确认
  - 1/4-3/4 前置清理需在 v2 语境下完整 review
  next_action: 等 Vincent 对 v2 重新测试确认无 panic，其余补丁 review 后由 Peter 收进 sched/core
contribution_opportunities:
- kind: testing
  description: 在 192 核 + autogroup + +cpu 场景验证 v2 不再启动 panic（两种 GROUP_SCHED 配置）
- kind: review
  description: 审计 for_each_sched_entity_bl 与 4/4 rework 在多分支层级下 h_load 陈旧窗口与懒更新线程安全
generated_at: '2026-10-01T01:00:00'
source_email_count: 7
related_articles:
- sched-20260902-007
- sched-20260929-012
tags:
- cfs
title: 'sched/fair: Rework/fix task_h_load()'
layout: article
---

> **subject**：`sched/fair: Rework/fix task_h_load()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>：Peter Zijlstra 的 4 补丁系列中 `4/4` 重做 `task_h_load()`，v1 的 `for_each_sched_entity_bl()` 在 `set_next_task_fair()` 里 clobber `se`/`cfs_rq`，致 192 核机器启动 panic（Chen Yu、Vincent 双独立复现）。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>：Peter 重发 v2（完整 4 补丁）——修复 `FAIR_GROUP_SCHED=n`/`=y` 的编译与运行期失败，back-link 机制移入 `for_each_sched_entity()`，rebase 到当前树。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>（今天）：无新版本，多名 reviewer 澄清 v2 设计语义——Peter 确认删除 `update_cfs_rq_h_load()`（其调用方一般不持 `rq->lock`、更新不串行）是 rework 的初衷；Prateek Nayak 详细解释 `h_load` 的懒传播为何不向上全量更新；Kayra 指出一个 typo（`apprixmate`）并确认 root 更新频率变化是有意为之。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>）`task_h_load()` 计算任务沿 cgroup 调度层级的「层级负载」。旧实现有多个问题：hierarchy 遍历因 back-link 状态易 race 而破碎；jiffies 限速与 HZ 相关而非底层 PELT 衰减；更新绑定在 `task_h_load()` 使用点上导致 `cfs_rq->h_load` 常不新鲜。v2 把 back-link 跟踪移入 `for_each_sched_entity()` 并在持锁位点重算 h_load。今天的增量是几名 reviewer 对 v2 设计取舍（root 更新频率、`h_load` 懒传播、`update_cfs_rq_h_load()` 移除）的澄清式讨论。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>）今天的讨论把 v2 的几个非显然取舍讲清：

- **`update_cfs_rq_h_load()` 被删除是有意的**：该函数的调用方（`task_h_load()` 的使用者）一般并不持有 `rq->lock`，因此其内部更新是「未串行化的、破碎的」——这正是本补丁要修的东西。
- **root 更新变少是有意的**：`for_each_sched_entity()` 只向上更新「从起点往上」的 group（原来是走到顶且若尚未更新则更新 root）；理想的完整子树更新可能昂贵，按 Prateek 的说法后续按需再更新。
- **`h_load` 懒传播**：`__sched_group_set_shares()` 里先 `for_each_sched_entity()` 做 `update_load_avg`/`update_cfs_group` 建立 backlink，再 `for_each_sched_entity_bl()` 沿 root 用 `update_cfs_rq_h_load()` 更新到受影响 cgroup 的 cfs_rq 为止；全量传播昂贵，因此在 pick/enqueue/dequeue 时懒更新。

## 版本演进与当前进展

- v1（8/28，`<20260828074059.232353141@infradead.org>`）：4 补丁，4/4 rework 引入 panic。
- v2（9/29，`<20260929084923.092062266@infradead.org>`）：4 补丁齐全，修复构建/运行期失败、重做 back-link 机制。
- 09-30：Peter、Prateek、Kayra 的讨论式 review（见下），无新代码版本。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（作者/维护者）：明确 `update_cfs_rq_h_load()` 移除正是补丁目的（其使用方不持 `rq->lock`、更新不串行）；并布置 ASCII 图解释 `cfs_rq_of()`/`group_cfs_rq()` 语义，说明只更新「从起点往上」的 group 是有意取舍。
- **K Prateek Nayak**：解释 `__sched_group_set_shares()` 的 `for_each_sched_entity` + `for_each_sched_entity_bl` 两步如何建立 backlink 并沿 root 更新 h_load 到受影响 cgroup；指出多分支层级（如 `A→(B,C)`）下 C/D/E 的 h_load 会陈旧，但全量传播昂贵、故在 pick/enqueue/dequeue 时懒更新。
- **Kayra Cizmeci**：确认「root 更新变少」是有意为之；指出一处 typo `apprixmate`。
- 无 NAK；讨论聚焦于确认「这是有意取舍」而非「是否 bug」，未出现新的阻塞性分歧。V2 的实机验证（Vincent 的 runtime fail 修复）当日仍未见到实测确认。

## 合入评估

*likelihood=high*。补丁出自 sched 核心维护者本人，v2 已把 v1 panic 根因从机制上重做并声称修复两类失败；今日讨论属「确认设计取舍」而非发现新问题（仅一提 typo）。*blocking_issues*：v2 的 `FAIR_GROUP_SCHED` 运行期修复尚未见 Vincent 重新实测确认；1/4–3/4 前置清理（尤其 `for_each_sched_entity_bl()`）仍需完整 review。*next_action*：等 Vincent 对 v2 重新测试确认无 panic，其余补丁 review 后由 Peter 收进 sched/core。

## 效果评估

无 benchmark 数字；效果证据仍来自 v1 期间正确性（GPF/panic 复现）与 v2 的机制重做。当日讨论为语义澄清，无新量化。

## 我可以参与的点

- `testing`：在 192 核物理机 + autogroup + `+cpu` 场景验证 v2 不再启动 panic（`FAIR_GROUP_SCHED=n` 与 `=y` 两种配置），这是当前最缺的实测。
- `review`：审计 v2 的 `for_each_sched_entity_bl()`（3/4）与 4/4 rework 在多分支 cgroup 层级下的 `h_load` 陈旧窗口是否可接受，及懒更新路径的线程安全。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
- Peter 今日解释: https://lore.kernel.org/all/20260930084520.GG88198@noisy.programming.kicks-ass.net/
- Prateek 的 h_load 传播解释: https://lore.kernel.org/all/5a5015bd-ed61-4ef7-a4c9-e759603c4cea@amd.com/
- v1 线程根: https://lore.kernel.org/all/20260828074059.232353141@infradead.org/
