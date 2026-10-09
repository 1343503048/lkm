# sched_ext: Keep proxy donors with slice left on the local DSQ

> **subject**：`sched_ext: Keep proxy donors with slice left on the local DSQ`

## TL;DR

Andrea Righi（NVIDIA，sched_ext 维护者）直接发往 `sched_ext/for-7.4` 分支的单补丁修复：commit ee172227d0dc（"Delegate proxy donor admission to BPF schedulers"）让 `put_prev_task_scx()` 把保留的 proxy donor 以 `SCX_ENQ_BLOCKED` 传回 `ops.enqueue()`，但其中一些 put 只是 proxy 记账（`proxy_resched_idle()` 找到远端 mutex owner、`proxy_migrate_task()` 迁移前摘除 donor、`proxy_deactivate()` 阻塞 owner 无法运行的 donor）——这些场景下 BPF 被迫对同一个 donor 反复做无意义的 dispatch/撤回。补丁改为：仍有 slice 剩余的 donor 放本地 DSQ 头部，下一次 pick 可继续解析其 owner、或 deactivation 直接摘除；用新 `SCX_RQ_PROXY_PICK_PENDING` rq 标志区分「proxy 记账性 put」与「真实 IMMED 抢占」，IMMED donor 本地保留时携带 `SCX_ENQ_IMMED` 使能力检查走 `SCX_CAP_ENQ_IMMED`。带 `Fixes: ee172227d0dc`。当日无回帖。

## 背景与问题

sched_ext 的 proxy execution 里，blocked 在 mutex 上的任务可作为 donor 留在 runqueue（`SCX_OPS_ENQ_BLOCKED` 下由 BPF 准入）。ee172227d0dc 之后，`put_prev_task_scx()` 对 is_blocked 的保留 donor 走 `scx_do_enqueue_task()` 交还 BPF。但三类 put 本质只是 proxy 内部记账：

1. `find_proxy_task()` 在 donor 切出前找到远端 mutex owner，`proxy_resched_idle()` 切 idle 前丢掉 rq 的 donor 引用——BPF 可能已为该 donor 选好位置（有 slice 剩余），交还再 dispatch 一轮纯属浪费，且拖延 proxy 解析继续；
2. `proxy_migrate_task()` 迁移前摘除 donor；
3. `proxy_deactivate()` 阻塞 owner 无法运行的 donor——caller 在 `ops.enqueue()` 后立刻 deactivate，BPF 的放置被立即撤销。

IMMED donor 另有坑：带 slice 剩余的 put 会报告 IMMED 抢占并交还 BPF；而 proxy 解析可能只是把已选中的 donor put 到 idle 以丢引用——当成抢占处理会重复同样的 BPF 放置。

## 技术方案

单补丁（`kernel/sched/ext/ext.c` +53/−17、`internal.h`、`sched.h`）：

- **本地 DSQ 头部保留**：`set_next_task_scx()` 里对 `sched_proxy_exec() && p->is_blocked && (type == SNT_PICK || SNT_REPICK)` 置 `SCX_RQ_PROXY_PICK_PENDING`；`put_prev_task_scx()` 检测到 `p->is_blocked && next == rq->idle && PICK_PENDING` 即视为 proxy put——不走 `scx_do_enqueue_task()` 交还 BPF，而是（有 slice 剩余时）放本地 DSQ 头部。真正的 IMMED 抢占仍交还 BPF（`REENQ_PREEMPTED`）。
- **IMMED 语义保留**：IMMED donor 本地保留时在插入 flags 上携带 `SCX_ENQ_IMMED`，使后续 sub-scheduler 能力检查用 `SCX_CAP_ENQ_IMMED` 而非 `SCX_CAP_ENQ`；延迟本地检查（CPU 不可用时的回交）不受影响。
- **delegation 顺位后移**：原「is_blocked 即交还 BPF」的分支移到 slice/救援判断之后——slice 用尽、被抢占或必须移动时才交还，`SCX_ENQ_BLOCKED` 语义不变。
- **文档**：`internal.h` 里 `SCX_ENQ_BLOCKED` 的注释改写，明确 donor 的完整生命周期（本地 DSQ 头部保留 vs 交还 BPF 的四个时机）。
- `scx_proxy_donor_start()`/`do_pick_task_scx()` 里清 `PICK_PENDING`（proxy 解析已接手/重试放弃临时 pick）。

## 版本演进与当前进展

v1 刚发出（`<20261001191216.2391359-1-arighi@nvidia.com>`，`[PATCH sched_ext/for-7.4]` 直发分支）。当日无回帖（Tejun 未表态）。作者即 sched_ext 维护者之一，直发 for-7.4 表明目标是本窗口合入。

## Maintainer 意见与讨论焦点

当日无回帖。作者自述设计立场：「For donors with slice left, this leaves BPF to handle meaningful placement decisions rather than transient proxy-bookkeeping puts」——BPF 只处理有意义的放置决策。无 NAK。潜在评审点（无人提出）：`PICK_PENDING` 与 core scheduling forced-idle pick 的交互（补丁注释说明 core 调度的 forced-idle pick 选 idle、不能标记 proxy put）；`scx_proxy_donor_start()` 清标志的时序。

## 合入评估

*likelihood=medium*。维护者本人直发目标分支、带 `Fixes:`、修复 ee172227d0dc 引入的实际 BPF 冗余交互；但 sched_ext 分支惯例是 Tejun 逐补丁 review（"Applied 1-2 to ..." 式收取），未经其确认不算数。*blocking_issues*：Tejun 的 review/收取未发生。*next_action*：等 Tejun 对 sched_ext/for-7.4 的收取表态。

## 效果评估

无量化数据（无 BPF dispatch 次数对比、无延迟数据）。收益是机制性的：消除三类 proxy 记账 put 的冗余 BPF 往返。作者未附测试说明。

## 我可以参与的点

- `testing`：用支持 `SCX_OPS_ENQ_BLOCKED` 的 BPF 调度器（如 scx_mitosis/scx_rusty 带 blocked donor 场景）跑 proxy-heavy 负载（大量 mutex 争用），统计 `ops.enqueue()` 调用次数前后对比——把机制收益量化，这正是补丁缺失的证据。
- `review`：核对 `PICK_PENDING` 标志在 `do_pick_task_scx()` 重试路径与 core scheduling forced-idle 路径下的清除完整性（补丁注释自认 forced-idle 不能标记 proxy put）。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261001191216.2391359-1-arighi@nvidia.com/

---
id: sched-20261002-008
date: '2026-10-02'
subject: 'sched_ext: Keep proxy donors with slice left on the local DSQ'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261001191216.2391359-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20261001191216.2391359-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261001191216.2391359-1-arighi@nvidia.com>'
    date: '2026-10-02'
    summary: '有 slice 剩余的 proxy donor 留本地 DSQ 头部；PICK_PENDING 区分记账 put 与抢占；IMMED 能力检查保留'
    review_outcome: '当日无回帖，等 Tejun 收取'
upstream_commit: null
fixes_commit: 'ee172227d0dc'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Tejun 对 sched_ext/for-7.4 的 review/收取未发生'
  next_action: '等 Tejun 收取表态'
contribution_opportunities:
  - kind: testing
    description: 'proxy-heavy 负载统计 ops.enqueue() 调用次数前后对比，量化机制收益'
  - kind: review
    description: '核对 PICK_PENDING 在重试与 forced-idle 路径的清除完整性'
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - sched_ext
  - proxy_exec
---
