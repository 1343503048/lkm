# sched: Add task enqueue/dequeue trace points

> **subject**：`sched: Add task enqueue/dequeue trace points`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260831-010：Gabriele Monaco（Red Hat）此前发出 20 补丁 RFC，第 1 篇在通用入队/出队路径 `enqueue_task()`/`dequeue_task()`/`__block_task()` 上加一对新 tracepoint `sched_enqueue`/`sched_dequeue` 并 GPL 导出，方向由 Peter Zijlstra 建议、已获 K Prateek Nayak Reviewed-by。
- sched-20260929-013（今天）：该 tracepoint 补丁作为 `[PATCH 00/10] rv: Add remaining deadline monitors` 系列的第 05/10 重发，署名 `From: Nam Cao`、`Co-developed-by: Gabriele Monaco`，其余内容与 v1 基本一致，目标是为 RV 的新 deadline monitor 补齐可观测点。

## 背景与问题

（承接 sched-20260831-010）现有 sched tracepoint 覆盖事件语义（`sched_wakeup`/`sched_switch`/`sched_migrate_*`），缺一对「任务被放进/拿出 runqueue」的通用观察点；想看调度类无关层面的 runqueue 实际增删（含 `__block_task()` 这类不走 `dequeue_task()` 的路径）只能靠 kprobe 或改代码。本补丁把它做成正式 tracepoint，放在通用 `enqueue_task()`/`dequeue_task()` 层。今天的新背景是：它现在是 RV「remaining deadline monitors」系列（10 补丁）的一部分，为 deadline monitor 记录任务入队/出队事件。

## 技术方案

（承接 sched-20260831-010，内容与 v1 基本一致）在 `include/trace/events/sched.h` 用 `DECLARE_TRACE` 声明 `sched_enqueue`/`sched_dequeue`（原型 `(struct task_struct *tsk, int cpu)`），`EXPORT_TRACEPOINT_SYMBOL_GPL` 导出给模块/BPF。要点：`enqueue_task()` 只在 `!(flags & ENQUEUE_DELAYED)` 时打点、`dequeue_task()` 只在 `!(flags & DEQUEUE_SLEEP)` 时打点（先存 `p->sched_class->dequeue_task()` 返回值再打点）；`__block_task()` 开头补一次 `trace_sched_dequeue_tp()`；两处均先 `trace_*_enabled()` 判断控制开销（未启用时仅一次 static key 检查）。

今天唯一可观察到的文本变化是署名 trailer（`From: Nam Cao`、`Co-developed-by: Gabriele Monaco`、`Suggested-by: Peter Zijlstra`、`Reviewed-by: K Prateek Nayak`），补丁功能面与 v1 相同。

## 版本演进与当前进展

- v1（8/31）：作为 20 补丁 RFC 的第 01/20 首发（对应 sched-20260831-010）。
- 9/29：作为「rv: Add remaining deadline monitors」10 补丁系列的 05/10 重发（patch msgid `<20260929124908.177676-6-gmonaco@redhat.com>`，cover `<20260929124908.177676-1-gmonaco@redhat.com>`）。当日无新回帖。

## Maintainer 意见与讨论焦点

当日线程内无新意见；已有信号仍写在 trailer 上：`Suggested-by: Peter Zijlstra`（方向由他提出）、`Reviewed-by: K Prateek Nayak`（首篇已过一轮 review）。v1 时期识别出的潜在争议（`DECLARE_TRACE` 不带格式化字段、只带 tsk/cpu 是否够用、`__block_task()` 计入 dequeue 与 `DEQUEUE_SLEEP` 过滤的语义自洽）当日仍无人重提。

## 合入评估

*likelihood=medium*。补丁本身干净、有建议者与 AMD reviewer 的 Reviewed-by，作为独立观测点补齐可合入性不低；但它现在挂在 RV「remaining deadline monitors」系列（10 补丁）里，实际推进依赖整个 RV 系列的用途与 RV maintainer 的收取。*blocking_issues*：RV 系列目标（cover 与其余 9 篇补丁）不在本次分析窗口内，无法判断整体进展。*next_action*：跟踪 RV 系列（尤其 cover）的 review 与本片是否随系列整体合入。

## 效果评估

暂无效果数据（trace 开销对比、启用/未启用性能数字均无）。

## 我可以参与的点

- `review`：确认 `sched_enqueue`/`sched_dequeue` 的字段（仅 tsk/cpu）是否满足 RV deadline monitor 的观测需求，或是否需要带 flags/调度类字段。
- `testing`：把这对 tracepoint 摘到本地分支跑负载均衡/带宽限流排查，反馈开销与可用性（作为 RV 系列之外的独立使用反馈）。

## 参考链接

- lore（系列 cover）: https://lore.kernel.org/all/20260929124908.177676-1-gmonaco@redhat.com/
- lore（05/10）: https://lore.kernel.org/all/20260929124908.177676-6-gmonaco@redhat.com/

---
id: sched-20260929-013
date: '2026-09-29'
subject: "sched: Add task enqueue/dequeue trace points"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260929124908.177676-1-gmonaco@redhat.com>"
lore_url: "https://lore.kernel.org/all/20260929124908.177676-6-gmonaco@redhat.com/"
authors: ["Gabriele Monaco", "Nam Cao"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260929124908.177676-6-gmonaco@redhat.com>"
    date: 2026-09-29
    summary: "作为 rv: Add remaining deadline monitors 系列 05/10 重发：enqueue_task()/dequeue_task()/__block_task() 加 sched_enqueue/sched_dequeue tracepoint 并 GPL 导出"
    review_outcome: "带 Reviewed-by: K Prateek Nayak 与 Suggested-by: Peter Zijlstra；当日无新意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "RV 系列目标（cover 与其余补丁）不在本次分析窗口内，无法判断整体进展"
  next_action: "跟踪 RV 系列 review 与本片是否随系列整体合入"
contribution_opportunities:
  - kind: review
    description: "确认 sched_enqueue/sched_dequeue 字段是否满足 RV deadline monitor 观测需求"
  - kind: testing
    description: "摘到本地分支跑负载均衡/带宽限流排查，反馈开销与可用性"
generated_at: "2026-09-30T01:15:00"
source_email_count: 1
related_articles:
  - sched-20260831-010
tags:
  - sched_debug
---