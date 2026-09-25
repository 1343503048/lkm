# sched_ext: Update scx_dispatch_dequeue() comments

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 sched-20260924-005。

- sched-20260924-005：Usama Arif 的纯注释修正 v2，`scx_dispatch_dequeue()` 两段过时注释按 Tejun 意见改写并重排 80 列，获 Andrea Righi Reviewed-by。
- sched-20260925-021（今天）：Tejun Heo 把 v2 应用到 sched_ext/for-7.4，并附带 Andrea Righi 的 Reviewed-by。

## 背景与问题

（承接 sched-20260924-005）`scx_dispatch_dequeue()` 里两段注释与实际代码路径脱节：`!dsq` 分支如今也因「远端消费」而带 `holding_cpu`；`dsq` 分支的竞争对方其实是 `unlink_dsq_and_switch_rq_lock()` 而非 `dispatch_to_local_dsq()`。不更新会让读者对竞争关系与 `holding_cpu` 语义误读。

## 技术方案

（承接 sched-20260924-005）纯注释改动（8 insertions / 8 deletions，kernel/sched/ext/ext.c）：`!dsq` 分支改为「`dispatch_to_local_dsq()` 或远端消费把任务移到本地 DSQ 时，任务不关联任何 DSQ 但可能带 `holding_cpu`；清除它是告诉对方它输了这次 dequeue」；`dsq` 分支改为「正与 `unlink_dsq_and_switch_rq_lock()` 竞争」。v1→v2 按 Tejun 意见显式点名函数、补「清除 holding_cpu 让对方知道输了」、重排 80 列。

## 版本演进与当前进展

- v1（无版本号）：初版注释修正。
- v2（2026-09-24，`<20260924130503.853919-1-usama.arif@linux.dev>`）：按 Tejun 意见改写。
- 09-25：Tejun 应用，附 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。

## Maintainer 意见与讨论焦点

Tejun Heo 在 v1 提出意见（显式点名竞争函数、补语义句），v2 落实后直接应用；Andrea Righi 给出 Reviewed-by。无分歧。

## 合入评估

已应用到 sched_ext/for-7.4（*likelihood=merged*），`merged_branch=sched_ext/for-7.4`。纯注释，无阻塞项。

## 效果评估

无运行时数据；纯注释修正，效果体现在代码可读性。

## 我可以参与的点

已应用，当前阶段暂无明显参与空间。

## 参考链接

- Tejun 应用回帖: https://lore.kernel.org/all/9dd9a20323b92268b57c4edd0be094ab@kernel.org/
- v2 补丁: https://lore.kernel.org/all/20260924130503.853919-1-usama.arif@linux.dev/

---
id: sched-20260925-021
date: 2026-09-25
subject: "sched_ext: Update scx_dispatch_dequeue() comments"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20260924130503.853919-1-usama.arif@linux.dev>"
lore_url: "https://lore.kernel.org/all/20260924130503.853919-1-usama.arif@linux.dev/"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
current_version: v2
generated_at: "2026-09-26T01:15:00"
authors:
  - "Usama Arif"
maintainers_involved:
  - "Tejun Heo"
  - "Andrea Righi"
patch_series:
  - version: v2
    msgid: "<20260924130503.853919-1-usama.arif@linux.dev>"
    date: 2026-09-24
    summary: "按 Tejun 意见改写 scx_dispatch_dequeue 两段注释，重排 80 列"
    review_outcome: "09-25 Tejun 应用到 sched_ext/for-7.4，附 Andrea Righi Reviewed-by"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已应用到 sched_ext/for-7.4，随合并窗口进主线"
contribution_opportunities: []
source_email_count: 1
related_articles:
  - "sched-20260924-005"
tags:
  - sched_ext
---