# sched_ext: Wait for SCX_OPSS_DISPATCHING before reenqueueing a task

## TL;DR
Tejun Heo 的 sched_ext 修复：`ebf1ccff79c4` 把 dispatcher 的最终 `ops_state` 写入挪到了 DSQ 解锁之后，于是任务可能还在 `SCX_OPSS_DISPATCHING` 状态就出现在 DSQ 上。dequeue 与 core-sched pick 路径会等该状态清除，但 reenqueue 路径不会，导致 reenqueue 的 `SCX_OPSS_QUEUED` 被 dispatcher 的最终写入覆盖成 `SCX_OPSS_NONE`、后续 dispatch 全部被丢弃。修复在 reenqueue 前等待状态清除。已获 Andrea Righi Reviewed-by，带 stable 标签。

## 背景与问题
`ebf1ccff79c4 ("sched_ext: Fix ops.dequeue() semantics")` 把 `scx_dispatch_enqueue()` 里的最终 `ops_state` store 移到 DSQ 解锁之后，以便 custody 更新与 `ops.dequeue()` 先于它执行。副作用是：任务可以带着 `SCX_OPSS_DISPATCHING` 状态出现在 DSQ 上。`ops_dequeue()` 路径会等待该状态清除，但 reenqueue 路径没有等——在该窗口内 reenqueue 会先执行 `ops.enqueue()` 并置 `SCX_OPSS_QUEUED`，随后 dispatcher 的最终 store 把它覆盖为 `SCX_OPSS_NONE`，`finish_dispatch()` 于是丢弃该任务之后的所有 dispatch。

## 技术方案
新增 `scx_reenq_wait_dispatching()`：若任务的 `ops_state` 仍为 `SCX_OPSS_DISPATCHING`，则用 `wait_ops_state()` 等待其清除，与 `ops_dequeue()` 的做法一致。在三条 reenqueue 路径（`reenq_local()`、`reenq_user()`、`scx_reenq_reject()`）的 dequeue 之前调用。改动集中在 `kernel/sched/ext/ext.c`（13 insertions）加少量头文件声明。

## 版本演进与当前进展
- **v1**（本日 105403，`<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>`）：单枚补丁，`Fixes: ebf1ccff79c4`，`Cc: stable # v7.1+`。这是 Tejun 在 ops.dequeue v2 评审里预告要「单独修」的那个 DISPATCHING reenq 洞（见 sched-20260916-006）。

## Maintainer 意见与讨论焦点
- **Andrea Righi**：`Reviewed-by: Andrea Righi <arighi@nvidia.com>`——「Thanks for fixing this, it makes sense to me.」无异议。

## 合入评估
likelihood=high。作者即 sched_ext 维护者 Tejun Heo，修复路径清晰、逻辑自洽，已获 Andrea Righi Reviewed-by，带 `Fixes:` 与 stable 标签，无争议。blocking_issues：无。next_action：Tejun 自收进 sched_ext/for-7.3-fixes 并回合 stable v7.1+。

## 效果评估
正文未给出量化复现数据，属基于代码时序分析的竞态修复（reenqueue 窗口内的状态覆盖）。

## 我可以参与的点
- kind=review：核对 `scx_reenq_wait_dispatching()` 在三条 reenqueue 路径上的放置是否覆盖所有 reenqueue 入口（含 sub-sched 场景）。
- kind=testing：在触发频繁 reenqueue 的 SCX workload（如 cgroup attach/detach、rescue/reject 路径）下观察是否仍有任务被静默丢弃。

## 参考链接
- patch：https://lore.kernel.org/all/a4304b3f0c89fba23f1e5e92997a8f56@kernel.org/
- Andrea Reviewed-by：https://lore.kernel.org/all/aqmwiJ1StVe1EH4L@gpd4/

---
id: sched-20260916-005
date: '2026-09-16'
subject: 'sched_ext: Wait for SCX_OPSS_DISPATCHING before reenqueueing a task'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>'
lore_url: 'https://lore.kernel.org/all/a4304b3f0c89fba23f1e5e92997a8f56@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>'
    date: '2026-09-15'
    summary: '在三条 reenqueue 路径 dequeue 前等待 SCX_OPSS_DISPATCHING 清除'
    review_outcome: 'Andrea Righi Reviewed-by'
upstream_commit: null
fixes_commit: 'ebf1ccff79c4'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 'Tejun 收入 sched_ext/for-7.3-fixes 并回合 stable'
contribution_opportunities:
  - kind: review
    description: '核对等待逻辑是否覆盖所有 reenqueue 入口含 sub-sched 场景'
  - kind: testing
    description: '在频繁 reenqueue 的 SCX workload 下观察是否仍有任务被静默丢弃'
generated_at: '2026-09-17T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---