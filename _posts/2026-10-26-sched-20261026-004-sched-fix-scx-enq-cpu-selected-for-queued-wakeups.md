---
id: sched-20261026-004
date: 2026-10-26
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
current_version: v2
patch_series:
- version: v1
  msgid: <20261023144811.2230393-1-jpiecuch@google.com>
  date: 2026-10-23
  summary: 跨 wakelist 保留 WF_RQ_SELECTED + 新增 selftest
  review_outcome: Tejun Acked-by + Andrea Reviewed-by，建议澄清描述
- version: v2
  msgid: <20261026114429.209588-1-jpiecuch@google.com>
  date: 2026-10-26
  summary: 澄清 wakelist 前后路径描述、修正 ttwu_do_activate 名称、selftest 亲和性重构，并入 Acked/Reviewed
  review_outcome: 无新 review，待 Peter/Tejun 定归属树
upstream_commit: null
fixes_commit: 3539c6411a7c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 归属树未定（核心 sched 改动需 Peter 拍板）
  next_action: 等 Peter/Tejun 确定 tip 或 sched_ext 树后收取
contribution_opportunities:
- kind: testing
  description: 真实 sched_ext 负载上跑 enq_cpu_selected selftest 确认无 missing/spurious
- kind: review
  description: 复核 sched_rq_selected 位字段对 wakelist 串行化/内存序假设的影响
generated_at: '2026-10-27T01:00:00'
source_email_count: 3
related_articles:
- sched-20261023-002
- sched-20261024-005
tags:
- sched_ext
- cfs
title: 'sched: Fix SCX_ENQ_CPU_SELECTED for queued wakeups'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a>：Kuba Piecuch（Google）的两补丁修复——`SCX_ENQ_CPU_SELECTED` 本应告诉 `ops.enqueue()` 本次唤醒是否执行过 `ops.select_cpu()`，但经 ttwu wakelist 投递的 queued wakeup 会丢掉 `WF_RQ_SELECTED`，导致设 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的 BPF 调度器无法判断且 `SCX_EV_SELECT_CPU_FALLBACK` 事件被低估。patch 1 把 `WF_RQ_SELECTED` 像 `WF_MIGRATED` 一样跨 wakelist 传递，patch 2 加 selftest。作者 4-vCPU 实测 2 秒约 11 万次 queued wakeup 全部误判。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-005-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261024-005</a>：Tejun Heo 给 *Acked-by*，Andrea Righi 给 *Reviewed-by* 并建议澄清「修的是 `->select_task_rq()` 之后的 queued wakeup」；两位维护者背书后仅剩确定归属树。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-004-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261026-004</a>（今天）：作者发 **v2**，采纳 Andrea 的描述澄清与 `ttwu_do_activate()` 名称修正、把 patch 2 selftest 改为「每对 task 各自两个 CPU、dispatch 到 SCX_DSQ_LOCAL，waker/wakee 必跨 CPU」，并并入 Tejun Acked-by + Andrea Reviewed-by。作者仍请 Peter/Tejun 决定系列走 tip 还是 sched_ext 树。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a> / 20261024-005）sched_ext 用 `ENQUEUE_RQ_SELECTED` 标志告诉 sched_class `->select_task_rq()` 是否已在唤醒时被调用，并把它以 `SCX_ENQ_CPU_SELECTED` 暴露给 BPF 调度器。问题出在 queued wakeup 路径：`sched_ttwu_pending()` 里只透传了 `p->sched_remote_wakeup`（映射到 `WF_MIGRATED`），`WF_RQ_SELECTED` 被丢弃，所以经 wakelist 投递的唤醒永远看不到这个 flag。开启 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的调度器因此无法区分「`ops.select_cpu()` 被跳过」与「正常执行」，同时 `SCX_EV_SELECT_CPU_FALLBACK` 事件被漏计。今日无新背景，为 v2 收尾与归属树确认。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a>）patch 1 在 `struct task_struct` 新增 1-bit `sched_rq_selected`，`__ttwu_queue_wakelist()` 记录 `WF_RQ_SELECTED`，`sched_ttwu_pending()` 据此把 flag 重新并入 `wake_flags`，使 `ttwu_do_activate()` → `activate_task()` 收到 `ENQUEUE_RQ_SELECTED`；patch 2 加 `enq_cpu_selected` selftest。

今日 v2 改动（来自 cover letter）：

- patch 1：按 Andrea 意见改写描述，区分「`->select_task_rq()` **之前**的 wakelist 路径（p->on_cpu 路径，flag 本就不该置）」与「**之后**的路径（ttwu_queue() 路径，flag 应置）」，并把 `ttwu_activate()` 修正为 `ttwu_do_activate()`；并入 Tejun Acked-by、Andrea Reviewed-by。
- patch 2：按 Sashiko 意见，给每对 ping-pong 任务各自两个 CPU、dispatch 到 `SCX_DSQ_LOCAL`，使 waker/wakee 恒在不同 CPU，测试不再依赖任务自行铺开；少于 4 CPU 时 SKIP。

作者仍请 Peter/Tejun 决定系列走 tip 还是 sched_ext 树。

## 版本演进与当前进展
*current_version: v2*（cover `<20261026114429.209588-1-jpiecuch@google.com>`）。v1（`<20261023144811.2230393-1-jpiecuch@google.com>`）→ v2：描述澄清 + 名称修正（Andrea）、selftest 亲和性重构（Sashiko）、并入 Acked/Reviewed 标签。当日无新 review 意见。

## Maintainer 意见与讨论焦点
当日无新增意见，延续此前背书：**Tejun Heo** *Acked-by*、**Andrea Righi** *Reviewed-by*（此前还建议描述澄清，v2 已落实）。作者再次请 Peter/Tejun 决定归属树。无分歧、无 NAK。

## 合入评估
*likelihood=high*。改动小而聚焦、带 `Fixes: 3539c6411a7c` 与配套 selftest，已获 Tejun Acked-by + Andrea Reviewed-by，v2 落实了全部 review 意见；仅剩归属树（tip 还是 sched_ext）待 Peter/Tejun 拍板。*blocking_issues*：归属树未定（涉及 `kernel/sched/core.c` 与 task_struct 新位字段，需 Peter 拍板）。*next_action*：等 Peter/Tejun 确定收取路径后合入。

## 效果评估
作者 4-vCPU 虚拟机实测（延续 20261023-002）：无 patch 1 时 2 秒约 **11 万次 queued wakeup 全部**表现为「`ops.select_cpu()` 已调用但 `SCX_ENQ_CPU_SELECTED` 被清」；加 patch 1 后为 0。今日无新数据。

## 我可以参与的点
- *kind: testing*：在设 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的真实 sched_ext 负载上跑 `enq_cpu_selected` selftest，确认无 missing/spurious。
- *kind: review*：复核 `sched_rq_selected` 位字段对 wakelist 串行化/内存序假设的影响。

## 参考链接
- v2 cover: https://lore.kernel.org/all/20261026114429.209588-1-jpiecuch@google.com/
- v2 patch 1: https://lore.kernel.org/all/20261026114429.209588-2-jpiecuch@google.com/
- v1: https://lore.kernel.org/r/20261023144811.2230393-1-jpiecuch@google.com
- 前文: <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-005-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261024-005</a> / <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-002-sched-fix-scx-enq-cpu-selected-for-queued-wakeups.html">sched-20261023-002</a>
