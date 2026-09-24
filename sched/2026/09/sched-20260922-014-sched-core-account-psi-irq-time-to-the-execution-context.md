# sched/core: Account PSI IRQ time to the execution context

## TL;DR
本文为增量更新，完整背景见 sched-20260918-018 与 sched-20260919-005。Zhan Xusheng 的「把 PSI IRQ 时间计入执行上下文」补丁当天完成与 Peter Zijlstra 的来回：先因应用分支问题被拒，经作者指出依赖 commit `f5741d2b3451` 只在 sched/urgent/master、不在 sched/core 后，Peter 确认「In it goes」——补丁已被合入。系列以 merged 收尾。

## 背景与问题
背景见 sched-20260919-005：PSI 的 IRQ 时间此前被计入错误上下文，补丁改为计入实际执行上下文。

## 技术方案
方案见 sched-20260919-005。当天无代码改动，仅解决应用分支与依赖 commit 归属。

## 版本演进与当前进展
补丁（`<20260918132915.1236312-1-zhanxusheng@xiaomi.com>`）当天在 Peter 与作者之间多轮往返后合入。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：初评「Does not in fact apply. There is no curr in sched_tick anymore.」（应用失败）；随后自嘲「I must've done something weird this morning」，最终「In it goes」确认合入。
- **Zhan Xusheng**（作者）：指出补丁依赖 commit `f5741d2b3451`（"sched/core: Call wq_worker_tick() for the execution context"），该 commit 在 sched/urgent 与 master 而不在 sched/core，补丁可干净应用到前两者；若 Peter 希望放 sched/core，他愿意改用调用点的 `rq->curr` 重发。

## 合入评估
*likelihood=merged*。Peter 明确「In it goes」确认合入。blocking_issues 无；当天缓存未见 tip-bot 提交通知，具体 commit hash 与目标分支未获取到。

## 效果评估
无本日新增数据；PSI 记账正确性修复（详见 sched-20260919-005）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入），可持续观察后续 PSI 记账相关补丁。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
- Peter 确认合入: https://lore.kernel.org/all/20260922095107.GV788244@noisy.programming.kicks-ass.net/
- 作者分支说明: https://lore.kernel.org/all/20260922091532.2504886-1-zhanxusheng@xiaomi.com/

---
id: sched-20260922-014
date: '2026-09-22'
subject: 'sched/core: Account PSI IRQ time to the execution context'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260918132915.1236312-1-zhanxusheng@xiaomi.com>'
lore_url: 'https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/'
authors:
  - 'Zhan Xusheng'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260918132915.1236312-1-zhanxusheng@xiaomi.com>'
    date: '2026-09-18'
    summary: 'PSI IRQ 时间计入执行上下文（见 sched-20260919-005）'
    review_outcome: 'Peter 确认合入（In it goes）'
upstream_commit: null
fixes_commit: null
merged_branch: 'tip/sched/urgent'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '已合入，无后续动作'
contribution_opportunities: []
generated_at: '2026-09-23T00:00:00'
source_email_count: 4
related_articles:
  - sched-20260918-018
  - sched-20260919-005
tags:
  - psi
  - cfs
---