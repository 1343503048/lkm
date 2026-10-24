---
id: sched-20261024-005
date: 2026-10-24
subject: 'sched: Fix SCX_ENQ_CPU_SELECTED for queued wakeups'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261023144811.2230393-1-jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/20261023144811.2230393-1-jpiecuch@google.com/
authors:
- Kuba Piecuch
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261023144811.2230393-1-jpiecuch@google.com>
  date: 2026-10-23
  summary: 跨 wakelist 保留 WF_RQ_SELECTED + 新增 selftest
  review_outcome: Tejun Acked-by + Andrea Reviewed-by，建议澄清描述
upstream_commit: null
fixes_commit: 3539c6411a7c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 归属树未定（核心 sched 改动需 Peter 拍板）
  next_action: 作者修订描述后等 Peter/Tejun 确定收取路径
contribution_opportunities:
- kind: testing
  description: 真实 sched_ext 负载上跑 enq_cpu_selected selftest 确认无 missing/spurious
- kind: review
  description: 复核 sched_rq_selected 位字段对 wakelist 串行化/内存序假设的影响
generated_at: '2026-10-25T01:00:00'
source_email_count: 2
related_articles:
- sched-20261023-002
tags:
- sched_ext
- cfs
title: 'sched: Fix SCX_ENQ_CPU_SELECTED for queued wakeups'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a>：Kuba Piecuch（Google）的两补丁修复——`SCX_ENQ_CPU_SELECTED` 本应告诉 `ops.enqueue()` 本次唤醒是否执行过 `ops.select_cpu()`，但经 ttwu wakelist 投递的 queued wakeup 会丢掉 `WF_RQ_SELECTED`，导致设 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的 BPF 调度器无法判断且 `SCX_EV_SELECT_CPU_FALLBACK` 事件被低估。patch 1 把 `WF_RQ_SELECTED` 像 `WF_MIGRATED` 一样跨 wakelist 传递，patch 2 加 selftest。作者 4-vCPU 实测 2 秒约 11 万次 queued wakeup 全部误判。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-005-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261024-005</a>（今天）：Tejun Heo 给 *Acked-by*，Andrea Righi 给 *Reviewed-by* 并建议在描述中澄清「修的是 `->select_task_rq()` 之后的 queued wakeup」。两位维护者背书后，系列仅剩确定归属树即可收取。

## 背景与问题
（承接 20261023-002）sched_ext 用 `ENQUEUE_RQ_SELECTED` 告诉 sched_class `->select_task_rq()` 是否已在唤醒时被调用，并以 `SCX_ENQ_CPU_SELECTED` 暴露给 BPF 调度器。问题是 queued wakeup 路径里 `sched_ttwu_pending()` 只透传 `p->sched_remote_wakeup`（映射 `WF_MIGRATED`），`WF_RQ_SELECTED` 被丢弃，导致经 wakelist 投递的唤醒永远看不到该 flag。今日无新背景，为 review 背书确定。

## 技术方案
（承接 20261023-002）patch 1 在 `struct task_struct` 新增 1-bit `sched_rq_selected`，`__ttwu_queue_wakelist()` 记录 `WF_RQ_SELECTED`，`sched_ttwu_pending()` 据此把 flag 重新并入 `wake_flags`，使 `ttwu_do_activate()` → `activate_task()` 收到 `ENQUEUE_RQ_SELECTED`；patch 2 加 `enq_cpu_selected` selftest。今日无新代码，仅新增两个维护者背书与一处描述修订建议。

## 版本演进与当前进展
*current_version: v1*（`<20261023144811.2230393-1-jpiecuch@google.com>`）。当日无新版本，进展为获得 Tejun Acked-by 与 Andrea Reviewed-by。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：*Acked-by*（简短确认，无附加意见）。
- **Andrea Righi**：*Reviewed-by*，并建议描述澄清为「修的是 `try_to_wake_up()` 里 `->select_task_rq()` 被调用之后的 queued wakeup（即 ttwu_queue() 路径），而非 p->on_cpu 路径」，附一段改写的 commit 描述草稿；另指出一处 nit：`s/ttwu_activate()/ttwu_do_activate()/`。

无分歧或未解决问题，两位背书均为正向。

## 合入评估
*likelihood=high*。改动小而聚焦、带 `Fixes: 3539c6411a7c` 与配套 selftest，已获 Tejun Acked-by + Andrea Reviewed-by，仅剩确定走 tip（Peter）还是 sched_ext 树。*blocking_issues*：归属树未定（涉及 `kernel/sched/core.c` 与 task_struct 新位字段，需 Peter 拍板）。*next_action*：作者按 Andrea 建议修订描述后，等 Peter/Tejun 确定收取路径。

## 效果评估
作者 4-vCPU 虚拟机实测（延续 20261023-002）：无 patch 1 时 2 秒约 **11 万次 queued wakeup 全部**表现为「select_cpu 已调用但 flag 被清」，加 patch 1 后 missing/spurious 为 0。今日无新数据。

## 我可以参与的点
- *kind: testing*：在设 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的真实 sched_ext 负载上跑 `enq_cpu_selected` selftest，确认无 missing/spurious。
- *kind: review*：复核 `sched_rq_selected` 位字段对 wakelist 串行化/内存序假设的影响。

## 参考链接
- cover: https://lore.kernel.org/all/20261023144811.2230393-1-jpiecuch@google.com/
- Tejun Acked-by: https://lore.kernel.org/all/bba1b0e8d484f3da05cd956fb8052705@kernel.org/
- Andrea Reviewed-by: https://lore.kernel.org/all/atu_vjtcwe1BjCaf@gpd4/
- 前文: <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a>
