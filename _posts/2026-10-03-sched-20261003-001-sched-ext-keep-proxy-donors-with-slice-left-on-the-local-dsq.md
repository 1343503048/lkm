---
id: sched-20261003-001
date: '2026-10-03'
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched_ext
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261002221559.3090900-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261002221559.3090900-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261001191216.2391359-1-arighi@nvidia.com>
  date: '2026-10-02'
  summary: SCX_RQ_PROXY_PICK_PENDING 区分记账 put 与 IMMED 抢占
  review_outcome: Tejun 质疑 IMMED 对 blocked donor 的适用性
- version: v2
  msgid: <20261002221559.3090900-1-arighi@nvidia.com>
  date: '2026-10-03'
  summary: 删 PICK_PENDING；IMMED 全面豁免；折进普通 enqueue 路径
  review_outcome: 全部采纳 Tejun 意见，待其收取
upstream_commit: null
fixes_commit: ee172227d0dc
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 尚无 Tejun 正式收取回帖
  next_action: Tejun review v2 后进 sched_ext/for-7.4
contribution_opportunities:
- kind: testing
  description: proxy execution + ENQ_BLOCKED + IMMED 负载下对比 v1/v2 与基线的 dispatch 次数与尾延迟
generated_at: '2026-10-04T01:00:00'
source_email_count: 3
related_articles:
- sched-20261002-008
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>：Andrea Righi（NVIDIA，sched_ext 维护者）发往 `sched_ext/for-7.4` 的单补丁修复——commit ee172227d0dc 让 `put_prev_task_scx()` 把保留的 proxy donor 以 `SCX_ENQ_BLOCKED` 交还 `ops.enqueue()`，但三类 put 只是 proxy 记账，BPF 被迫反复做无意义 dispatch；补丁改为有 slice 剩余的 donor 放本地 DSQ 头部，并用新 `SCX_RQ_PROXY_PICK_PENDING` rq 标志区分「记账性 put」与「真实 IMMED 抢占」。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261003-001</a>（今天）：Tejun Heo（sched_ext 首席维护者）提出根本性质疑——**IMMED 对 blocked donor 根本不该起作用**：IMMED 的语义是「任务未被任何 CPU 服务时触发 reenqueue」，而 proxy execution 下的 donor 正在被服务（CPU 在替它干活），调度器把它放到别处也不可能让它更快。若成立，有 slice 的 donor 无论 IMMED 与否都留在本地 DSQ，`SCX_RQ_PROXY_PICK_PENDING` 整个不需要；且可把 blocked-donor 回退折进普通 enqueue 路径（`scx_do_enqueue_task()` 已加 `SCX_ENQ_BLOCKED`，`ENQ_LAST` 条件上补 `!p->is_blocked` 测试即可）。Andrea 当场认同：「donor 的进度取决于其 mutex owner，单独 re-enqueue 不可能让它更早运行」，并当天发出 **v2**——全部采纳。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.html">sched-20261002-008</a>）sched_ext 的 proxy execution 里，blocked 在 mutex 上的任务可作为 donor 留在 runqueue（`SCX_OPS_ENQ_BLOCKED` 下由 BPF 准入）。ee172227d0dc 之后 `put_prev_task_scx()` 对 is_blocked 的保留 donor 走 `scx_do_enqueue_task()` 交还 BPF。但三类 put 本质只是 proxy 内部记账：`proxy_resched_idle()` 在 donor 切出前找到远端 mutex owner（BPF 已选好有 slice 剩余的位置，交还再 dispatch 纯属浪费且拖延 proxy 解析）、`proxy_migrate_task()` 迁移前摘除 donor、`proxy_deactivate()` 阻塞 owner 无法运行的 donor（caller 在 `ops.enqueue()` 后立刻 deactivate，BPF 的放置被立即撤销）。

v1 还额外处理了 IMMED donor：带 slice 剩余时视为 IMMED 抢占交还 BPF——这正是 Tejun 今天推翻的部分。

## 技术方案

（承接 v1 框架）v2 单补丁（`kernel/sched/ext/ext.c` +50/−32、`internal.h`）：

- **本地 DSQ 头部保留（不变）**：有 slice 剩余的 blocked donor 放本地 DSQ 头部，下一次 pick 继续解析其 owner、或 deactivation 直接摘除，跳过无意义的 BPF handoff。
- **IMMED 豁免（v2 新，Tejun）**：blocked donor 无论 IMMED 与否都本地保留——IMMED 的设计语义是「未被服务的任务触发 reenqueue」，donor 被 proxy execution 服务中，不满足该前提；`SCX_RQ_PROXY_PICK_PENDING` 标志整体删除。deferred local check 保留同样的豁免（任务保持 `SCX_TASK_IMMED`）。
- **折进普通 enqueue 路径（v2 新，Tejun）**：blocked-donor fallback 折进正常 enqueue 路径，`SCX_ENQ_LAST` 处理限制在未阻塞任务（`scx_do_enqueue_task()` 已加 `SCX_ENQ_BLOCKED`，`ENQ_LAST` 条件补 `!p->is_blocked`）。
- `wakeup_preempt_scx()`：本地 IMMED donor 在 `ttwu_runnable()` 清 `is_blocked` 后仍在其 `wake_cpu` 时重新调度本地检查（`scx_schedule_reenq_local()`）；`dispatch_one()` 注释补充「blocked IMMED donor 可能使扫描成 no-op，跳过不另记账」。
- `Fixes: ee172227d0dc`；base 为 `sched_ext/for-7.4`。

## 版本演进与当前进展

- v1（10-02，`<20261001191216.2391359-1-arighi@nvidia.com>`）：`SCX_RQ_PROXY_PICK_PENDING` 区分记账 put 与 IMMED 抢占。
- v2（10-03，`<20261002221559.3090900-1-arighi@nvidia.com>`）：按 Tejun 意见删 `PICK_PENDING`、IMMED 全面豁免、折进普通 enqueue 路径。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（10-03）：IMMED 语义论证（见 TL;DR）+ 两处具体实现建议（豁免 + fold into ENQ_LAST block）。
- **Andrea Righi**：完全认同并当天落实 v2。无分歧遗留。

## 合入评估

*likelihood=high*。目标分支 `sched_ext/for-7.4` 由 Andrea 自己维护、Tejun 的全部意见已在 v2 采纳且无剩余反对——流程上只待 Tejun 对 v2 的正式收取（或直接 pull 进 for-7.4）。*blocking_issues*：v2 尚无 Tejun 回帖。*next_action*：Tejun review v2 后进 `sched_ext/for-7.4`，随 7.4 合并窗口上行。

## 效果评估

无新增 benchmark。v1/v2 均为正确性/开销修复：消除 proxy 记账 put 的无谓 BPF dispatch 往返（EEVDF slice 剩余的 donor 免于被重复 dispatch 再撤销）；`Fixes:` 指向 ee172227d0dc 的行为回归。

## 我可以参与的点

- `testing`：在 proxy execution + `SCX_OPS_ENQ_BLOCKED` + IMMED 任务的负载（互斥链深的场景）下对比 v1/v2 与基线的 dispatch 次数与尾延迟，补量化数据回帖。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261002221559.3090900-1-arighi@nvidia.com/
- lore（v1）: https://lore.kernel.org/all/20261001191216.2391359-1-arighi@nvidia.com/
- lore（Tejun 意见）: https://lore.kernel.org/all/59be0f173a7bc73a5a7eb6927f635605@kernel.org/
