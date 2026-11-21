# sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261112-001：Tao Cui 两补丁修复 sched_ext 在 core.c 里的进入路径契约；patch 1 即本系列——在 fork 路径 `wake_up_new_task()` 给初始入队补 `ENQUEUE_RQ_SELECTED`，与唤醒路径对齐（仅 sched_ext 消费该标志）。当时 Peter 只对 patch 2 表态 NAK，patch 1 未获单独确认。
- sched-20261115-002：Tejun Heo 对 patch 1 给 Acked-by，并问 Peter 该补丁走 sched/core 还是 sched_ext 路由。
- sched-20261121-015（今天）：**Peter Zijlstra 回复「Yeah, take it through sched_ext; I don't think I've got any conflicts around there.」**——路由定案：经 sched_ext 收取。

## 背景与问题

sched_ext 在 core.c 里有「进入路径契约」：`ops.enqueue()` 需知道 `ops.select_cpu()` 是否已跑过。唤醒路径 `ttwu_do_activate()` 把 `select_task_rq()` 置的 `WF_RQ_SELECTED` 映射成 `ENQUEUE_RQ_SELECTED`；fork 路径 `wake_up_new_task()` 同样调 `select_task_rq()` 却不带该标志激活新任务——fork 侧 `ops.enqueue()` 看不到 `SCX_ENQ_CPU_SELECTED`，依赖该标志的调度器还会对已放好的任务重复跑 `select_cpu_dfl()`。

## 技术方案

在 `wake_up_new_task()` 里新增 `en_flags = ENQUEUE_NOCLOCK | ENQUEUE_INITIAL`，若 `select_task_rq()` 后 `wake_flags & WF_RQ_SELECTED` 则追加 `ENQUEUE_RQ_SELECTED`，传给 `activate_task()`，与唤醒路径对齐（`Fixes: 9b671793c7d9`）。改动限 core.c，仅 sched_ext 消费该标志。

## 版本演进与当前进展

*current_version: v1（2026-11-12，`<20261112144935.583937-2-cui.tao@linux.dev>`）*。当日无新版本；进展为路由定案（经 sched_ext）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：本日「take it through sched_ext; I don't think I've got any conflicts around there.」——同意经 sched_ext 路由、无冲突顾虑。
- **Tejun Heo**（前情）：Acked-by，愿意经 sched_ext 收取。
- 无 NAK；此前对 patch 2 的 NAK 与本 patch 1 无关。

## 合入评估

*likelihood=high*。patch 1 独立、已获 Tejun Ack，且 Peter 已确认路由（sched_ext）、无冲突。*blocking_issues*：无实质阻塞；作者需确认在 sched_ext 树基线可干净应用。*next_action*：Tejun 经 sched_ext 树收取。

## 效果评估

属正确性修复，无性能数据。前情作者在 qemu 上 A/B：40k fork 中打 patch 1 后 fork 与唤醒两条路径均 1:1 计数 fallback 事件（patch 前 fork 侧为 0）。

## 我可以参与的点

- **review**：核对 `ENQUEUE_RQ_SELECTED` 在初始入队路径语义与唤醒路径完全一致，以及 sched_ext 之外是否还有遗留消费方或边界路径（如 kernel_clone 其它调用点）。

## 参考链接

- lore thread（patch 1/2）: https://lore.kernel.org/all/20261112144935.583937-2-cui.tao@linux.dev/
- Peter 路由定案: https://lore.kernel.org/all/20261120162123.GS2668804@noisy.programming.kicks-ass.net/

---
id: sched-20261121-015
date: '2026-11-21'
subject: "sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261112144935.583937-2-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261120162123.GS2668804@noisy.programming.kicks-ass.net/"
authors: [Tao Cui]
maintainers_involved: [Tejun Heo, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112144935.583937-2-cui.tao@linux.dev>"
    date: '2026-11-12'
    summary: "fork 路径 wake_up_new_task() 补 ENQUEUE_RQ_SELECTED，与唤醒路径对齐"
    review_outcome: "Tejun Acked-by；Peter 同意经 sched_ext 路由、无冲突"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Tejun 经 sched_ext 树收取"
contribution_opportunities:
  - kind: review
    description: "核对初始入队语义与唤醒路径一致、无其它遗留消费方或边界路径"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: [sched-20261112-001, sched-20261115-002]
tags: [sched_ext]
---