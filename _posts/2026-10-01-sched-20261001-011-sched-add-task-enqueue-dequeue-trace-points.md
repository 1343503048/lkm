---
id: sched-20261001-011
date: '2026-10-01'
subject: 'sched: Add task enqueue/dequeue trace points'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261001152042.124445-1-gmonaco@redhat.com>
lore_url: https://lore.kernel.org/all/20261001152042.124445-2-gmonaco@redhat.com/
authors:
- Nam Cao
- Gabriele Monaco
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261001152042.124445-2-gmonaco@redhat.com>
  date: '2026-10-01'
  summary: 作为新 15 补丁系列 01/15 再发：enqueue_task()/dequeue_task()/__block_task() 加 sched_enqueue/sched_dequeue
    tracepoint 并 GPL 导出
  review_outcome: Peter 表示未收到其余补丁、changelog 无动机、无法判断为何需要
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 15 补丁系列未完整送达（当日缓存仅见 01/15）
  - 补丁 changelog 无动机说明
  - 宿主系列的整体叙事未建立
  next_action: 补发完整系列并写清 tracepoint 动机
contribution_opportunities:
- kind: review
  description: 帮助补全通用 enqueue/dequeue tracepoint 的动机论述
- kind: testing
  description: 摘到本地分支跑排查负载，反馈开销与可用性
generated_at: '2026-10-09T01:00:00'
source_email_count: 2
related_articles:
- sched-20260831-010
- sched-20260929-013
tags:
- sched_debug
title: 'sched: Add task enqueue/dequeue trace points'
layout: article
---

> **subject**：`sched: Add task enqueue/dequeue trace points`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/31/sched-20260831-010-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260831-010</a>：Gabriele Monaco（Red Hat）在 20 补丁 RFC 中首发该 tracepoint 补丁——在通用 `enqueue_task()`/`dequeue_task()`/`__block_task()` 路径加一对 `sched_enqueue`/`sched_dequeue` tracepoint 并 GPL 导出，方向由 Peter Zijlstra 建议、K Prateek Nayak 已 `Reviewed-by`。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-013-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260929-013</a>：该补丁作为 RV「remaining deadline monitors」系列（10 补丁）的 05/10 重发（`From: Nam Cao`、`Co-developed-by: Gabriele Monaco`）。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-011-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261001-011</a>（今天）：Gabriele 把它作为**新 15 补丁系列**的 01/15 再发 v2（`From: Nam Cao`，trailer 带 `Suggested-by: Peter`、`Reviewed-by: K Prateek Nayak`）；Peter Zijlstra 当晚回帖——他不记得来龙去脉，且作者「忘了把其余补丁发给我」、changelog 也没说明动机，「As is I'm clueless as to why we want this」。补丁本体早获 R-b，但系列叙事与动机说明书仍缺。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-013-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260929-013</a>）现有 sched tracepoint 覆盖事件语义（`sched_wakeup`/`sched_switch`/`sched_migrate_*`），缺一对「任务被放进/拿出 runqueue」的通用观察点；想看调度类无关层面的 runqueue 实际增删（含 `__block_task()` 这类不走 `dequeue_task()` 的路径）只能靠 kprobe 或改代码。该补丁把它做成正式 tracepoint。它已辗转三个系列（20 补丁 RFC → RV 10 补丁 → 今日的 15 补丁），每次宿主系列变化都让评审者难以追索动机——Peter 今天的反应正说明这一点。

## 技术方案

（承接，v2 与此前内容一致）`include/trace/events/sched.h` 用 `DECLARE_TRACE` 声明 `sched_enqueue`/`sched_dequeue`（原型 `(struct task_struct *tsk, int cpu)`），`EXPORT_TRACEPOINT_SYMBOL_GPL` 导出；`enqueue_task()` 只在 `!(flags & ENQUEUE_DELAYED)` 时打点；`dequeue_task()` 存下 `p->sched_class->dequeue_task()` 返回值后、仅 `!(flags & DEQUEUE_SLEEP)` 时打点；`__block_task()` 开头补 `trace_sched_dequeue_tp()`；两处先 `trace_*_enabled()` 判断控制开销。今日 v2 版本 diffstat 3 文件 +21/−1，正文无功能变化（trailer 与系列归属变化）。

## 版本演进与当前进展

- v1（08-31）：20 补丁 RFC 的 01/20（对应 <a class="article-ref" href="/lkm/2026/08/31/sched-20260831-010-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260831-010</a>）。
- 09-29：RV「remaining deadline monitors」10 补丁系列 05/10（对应 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-013-sched-add-task-enqueue-dequeue-trace-points.html">sched-20260929-013</a>）。
- 10-01：新 15 补丁系列 v2 01/15（cover `<20261001152042.124445-1-gmonaco@redhat.com>`，patch `<20261001152042.124445-2-gmonaco@redhat.com>`）；Peter 回帖（`<20261001154934.GT88198@noisy.programming.kicks-ass.net>`）指出没收到其余补丁、changelog 无动机说明。15 补丁系列的其余 14 篇未进入当日缓存。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：「Obviously I don't remember anything at all. But also, you 'forgot' to send me the rest of the patches which might hold a clue. As is I'm clueless as to why we want this, since the Changelog also offers none.」——三重信息：不记得此前的讨论（系列辗转多次的后果）、其余补丁未送达（15/15 里 LKML 收到的只有 01/15？或 Peter 未被抄送其余）、changelog 缺动机。语气是要求补全上下文，不是反对补丁本体。
- 既有 trailer 信号：`Suggested-by: Peter Zijlstra`（方向本就出自他）、`Reviewed-by: K Prateek Nayak`。
- v1 时期识别的潜在争议（字段是否够用、`__block_task()` 计入 dequeue 的语义）无人重提。

## 合入评估

*likelihood=medium*。补丁本体干净、有 R-b、方向由 Peter 本人建议过；但当前挂在第三个宿主系列（15 补丁）之下，且 Peter 明确表示缺其余补丁与动机说明就无法评审——宿主系列的完整性决定本片命运。*blocking_issues*：15 补丁系列未完整送达（当日缓存仅见 01/15）；补丁 changelog 无动机说明；宿主系列（RV 观测/监控用途）的整体叙事未建立。*next_action*：作者补发完整系列（确保 Peter 收到全量）并在 01/15 changelog 写清为什么需要这对 tracepoint。

## 效果评估

暂无效果数据（trace 开销对比、启用/未启用性能数字均无）。

## 我可以参与的点

- `review`：帮助补全「为什么需要通用 enqueue/dequeue tracepoint」的动机论述（如对照现有 `sched_wakeup`/`sched_switch` 的覆盖缺口、RV deadline monitor 的具体需求）——这正是 Peter 索要而缺失的东西。
- `testing`：把这对 tracepoint 摘到本地分支跑负载均衡/带宽限流排查，反馈开销与可用性。

## 参考链接

- v2 01/15: https://lore.kernel.org/all/20261001152042.124445-2-gmonaco@redhat.com/
- Peter 的回复: https://lore.kernel.org/all/20261001154934.GT88198@noisy.programming.kicks-ass.net/
- RV 系列 cover（09-29）: https://lore.kernel.org/all/20260929124908.177676-1-gmonaco@redhat.com/
