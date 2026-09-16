# sched_ext: Idle claim recovery and online cid mask

## TL;DR
本日为增量更新：Tejun Heo 宣布该 patchset 的 1-2 已合入 `sched_ext/for-7.3-fixes`，并补上了 Andrea Righi 的 Reviewed-by。这是一个面向 v7.3 修复窗口的补丁集（idle claim 回收 + 在线 cid mask），现已进入收合流程。

## 背景与问题
完整的背景与方案见 related_articles 中的 sched-20260915-001。要点：sched_ext 的 qmap 示例调度器在 dispatch 路径上会丢失已分配的 idle claim，需要回收；此外，自带 CPU ID 映射的调度器此前无法获知哪些 CPU ID 在线，需要内核维护一个 online mask。

## 技术方案
系列含两枚补丁（idle claim recovery 与 online cid mask 维护），技术细节不变，见 sched-20260915-001。

## 版本演进与当前进展
- v2（2026-09-14 发出，`<20260914234259.3585373-1-tj@kernel.org>`）：本日 Tejun 宣布「Applied 1-2 to sched_ext/for-7.3-fixes with Andrea's Reviewed-by added.」

## Maintainer 意见与讨论焦点
- **Tejun Heo**（作者兼维护者）：亲自把 1-2 收入 for-7.3-fixes。
- **Andrea Righi**：给出 Reviewed-by，无异议。

## 合入评估
likelihood=merged，status=merged_tip。已进入 `sched_ext/for-7.3-fixes` 分支，后续将随 v7.3-rc3 的 GIT PULL 进入 mainline（见 sched-20260916-009）。blocking_issues：无。next_action：等随 pull 请求进入 Linus 主线。

## 效果评估
无性能量化数据；属修复窗口内的正确性补丁。

## 我可以参与的点
当前阶段已合入分支，暂无明显参与空间，可关注其随 v7.3-rc3 pull 进入 mainline 后的 stable 回合情况。

## 参考链接
- Applied 邮件：https://lore.kernel.org/all/17cdcfca5509c320dd1344c66fff4289@kernel.org/
- v2 cover：https://lore.kernel.org/all/20260914234259.3585373-1-tj@kernel.org/

---
id: sched-20260916-008
date: '2026-09-16'
subject: 'sched_ext: Idle claim recovery and online cid mask'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260914234259.3585373-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20260914234259.3585373-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260914234259.3585373-1-tj@kernel.org>'
    date: '2026-09-14'
    summary: 'idle claim recovery + 在线 cid mask'
    review_outcome: 'Tejun 收入 sched_ext/for-7.3-fixes，Andrea Righi Reviewed-by'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '随 v7.3-rc3 pull 进入 mainline'
contribution_opportunities: []
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260915-001
tags:
  - sched_ext
---