---
id: sched-20261023-002
date: 2026-10-23
subject: 'sched: Fix SCX_ENQ_CPU_SELECTED for queued wakeups'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261023144811.2230393-1-jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/20261023144811.2230393-1-jpiecuch@google.com/
authors:
- Kuba Piecuch
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261023144811.2230393-1-jpiecuch@google.com>
  date: 2026-10-23
  summary: 跨 wakelist 保留 WF_RQ_SELECTED + 新增 selftest
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: 3539c6411a7c
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无维护者 review
  - task_struct 新增位字段需确认布局/内存序影响
  next_action: 等 Peter/Tejun 确定归属树并 review
contribution_opportunities:
- kind: testing
  description: 在真实 sched_ext 负载上跑 enq_cpu_selected selftest 确认无 missing/spurious
- kind: review
  description: 复核 sched_rq_selected 位字段对 wakelist 串行化/内存序假设的影响
generated_at: '2026-10-24T09:01:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- bpf
title: 'sched: Fix SCX_ENQ_CPU_SELECTED for queued wakeups'
layout: article
---

## TL;DR
Kuba Piecuch（Google）发往 sched 的两补丁修复：`SCX_ENQ_CPU_SELECTED` 本应告诉 `ops.enqueue()` 本次唤醒是否执行过 `ops.select_cpu()`，但经 ttwu wakelist 投递的 queued wakeup 会丢掉 `WF_RQ_SELECTED`，导致开启了 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的 BPF 调度器无法判断 `ops.select_cpu()` 是否被跳过、`SCX_EV_SELECT_CPU_FALLBACK` 事件被低估。patch 1 把 `WF_RQ_SELECTED` 像 `WF_MIGRATED` 一样跨 wakelist 传递（`Fixes: 3539c6411a7c`），patch 2 加 selftest。作者在 4-vCPU 虚拟机实测：无 patch 1 时 2 秒约 11 万次 queued wakeup 全部「select_cpu 被调用但 flag 被清」，加 patch 1 后为 0。尚无 review。

## 背景与问题
sched_ext 用 `ENQUEUE_RQ_SELECTED` 标志告诉 sched_class `->select_task_rq()` 是否已在唤醒时被调用，并把它以 `SCX_ENQ_CPU_SELECTED` 暴露给 BPF 调度器。问题出在 queued wakeup 路径：`sched_ttwu_pending()` 里只透传了 `p->sched_remote_wakeup`（映射到 `WF_MIGRATED`），`WF_RQ_SELECTED` 被丢弃，所以经 wakelist（任务在 `ops.select_cpu()` 所选 CPU 之外被 enqueue）投递的唤醒永远看不到这个 flag。开启 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的调度器因此无法区分「`ops.select_cpu()` 被跳过」与「正常执行」，同时 `SCX_EV_SELECT_CPU_FALLBACK` 事件被漏计。

## 技术方案
两补丁（`include/linux/sched.h` + `kernel/sched/core.c` + selftest）：

1. **patch 1**（sched/core: Preserve WF_RQ_SELECTED across queued wakeups）：在 `struct task_struct` 里新增 1-bit `sched_rq_selected`（与 `sched_remote_wakeup` 同处「wakelist 不再由 p->on_cpu 串行化」的字段区）；`__ttwu_queue_wakelist()` 里 `p->sched_rq_selected = !!(wake_flags & WF_RQ_SELECTED)`；`sched_ttwu_pending()` 里据此把 `WF_RQ_SELECTED` 重新并入传给 `ttwu_do_activate()` 的 `wake_flags`，从而让 `ttwu_activate()` → `activate_task()` 收到 `ENQUEUE_RQ_SELECTED`。
2. **patch 2**（selftests/sched_ext: Test SCX_ENQ_CPU_SELECTED with queued wakeups）：新增 `enq_cpu_selected` 测试，用 4 对 task 在 pipe 上乒乓产生唤醒，`ops.select_cpu()` 把「已执行 + 所在 CPU」记入 task storage，`ops.enqueue()` 据此对照 `SCX_ENQ_CPU_SELECTED` 统计 missing/spurious，调度器设 `SCX_OPS_ALLOW_QUEUED_WAKEUP`。

作者注明：bug 的发现与系列起草借助了 AI 编码助手；并请 Peter/Tejun 决定走 tip 还是 sched_ext 树。

## 版本演进与当前进展
*current_version: v1*（`<20261023144811.2230393-1-jpiecuch@google.com>`）。当日发出，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者/资深成员回帖。作者在 cover 中主动向 Peter Zijlstra、Tejun Heo 说明「改动落在 `kernel/sched/core.c` 与 `include/linux/sched.h`，但只有 sched_ext 会看到效果」，请二人决定系列走 tip 还是 sched_ext 树合入。

## 合入评估
*likelihood=medium*。改动小而聚焦、带明确 `Fixes:` 标签与配套 selftest，属正确性修复；但涉及核心调度结构体新增位字段，且尚未有维护者 review。*blocking_issues*：无 review；新位字段对 task_struct 布局的影响需确认。*next_action*：等 Peter/Tejun 决定归属树并 review 后收取。

## 效果评估
作者在 4-vCPU 虚拟机给出实测数据：无 patch 1 时，2 秒运行约 **11 万次 queued wakeup 全部**表现为「`ops.select_cpu()` 已调用但 `SCX_ENQ_CPU_SELECTED` 被清」；加 patch 1 后 missing/spurious 计数为 0（无此类 wakeup 时测试会 SKIP）。未给真实生产负载的调度收益数据。

## 我可以参与的点
- *kind: testing*：在真实 sched_ext 负载（尤其设 `SCX_OPS_ALLOW_QUEUED_WAKEUP` 的调度器）上跑 `enq_cpu_selected` selftest，确认无 missing/spurious。
- *kind: review*：复核 `sched_rq_selected` 位字段加入后 task_struct 的 wakelist 串行化注释与内存序假设是否仍成立。

## 参考链接
- cover: https://lore.kernel.org/all/20261023144811.2230393-1-jpiecuch@google.com/
- patch 1: https://lore.kernel.org/all/20261023144811.2230393-2-jpiecuch@google.com/
- patch 2: https://lore.kernel.org/all/20261023144811.2230393-3-jpiecuch@google.com/
