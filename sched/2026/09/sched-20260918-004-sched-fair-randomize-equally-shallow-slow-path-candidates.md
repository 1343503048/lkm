# sched/fair: Randomize equally shallow slow-path candidates

## TL;DR
增量更新：Christian Loehle 的慢路径 idle CPU 随机化系列（v2）本日收尾——Vincent Guittot 对 2/2 补上 Reviewed-by，Peter Zijlstra 表示"Thanks, let me go queue this"，系列即将进入 tip。上一日遗留的 !idle 处理与候选计数复位分歧，作者 v2 已按 U64_MAX reservoir 落实。

## 背景与问题
背景见 sched-20260917-007 与 sched-20260916-015：并发慢路径选择器会收敛到同一 idle CPU，且 idle-recency tie-break 可能选中唤醒成本最高的 CPU。v2 拆为 1/2（删除 idle-recency tie-break）与 2/2（reservoir sampling 随机化等 exit-latency 候选）。

## 技术方案
沿用 v2 方案：1/2 删除 idle_stamp tie-break；2/2 用 per-CPU PRNG + `reciprocal_scale()` 对等 exit-latency 候选做 reservoir sampling，U64_MAX 表示未发布状态。

## 版本演进与当前进展
- v2（09-17，`<20260917153915.1563875-1-christian.loehle@arm.com>`）：1/2 已获 Reviewed-by，2/2 本日补获 Reviewed-by 并被 Peter 表示将排队合入。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**：对 2/2 给出 Reviewed-by（补足本日）。
- **Peter Zijlstra**：回复 "Thanks, let me go queue this"，表示准备将系列合入 tip。
- 无剩余未解决分歧；上日关于 !idle 语义的讨论已随 v2 的 U64_MAX reservoir 收敛。

## 合入评估
*likelihood=high*。1/2、2/2 均已获 Reviewed-by，Peter 明确表示将排队合入，接近合入。*blocking_issues*：无明显阻塞（等待 Peter 实际合入）。*next_action*：等待 Peter 将系列收进 tip/sched/core；作者无需进一步动作，除非合入时出现冲突。

## 效果评估
本日无新增 benchmark；v1 数据（160 核 Altra stress-ng fork 中位数吞吐最高 +4.13%、stale-pick 率近乎减半）见 sched-20260916-015。

## 我可以参与的点
- kind=testing：系列合入 tip 后，在 8~32 核小系统回归慢路径 idle CPU 选择行为，确认无 !idle 相关的反直觉收敛。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/

---
id: sched-20260918-004
date: '2026-09-18'
subject: 'sched/fair: Randomize equally shallow slow-path candidates'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260917153915.1563875-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved:
  - 'Vincent Guittot'
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260916100116.701206-1-christian.loehle@arm.com>'
    date: '2026-09-16'
    summary: '删除 idle-recency tie-break + reservoir sampling'
    review_outcome: 'Kayra/Sashiko 关切小核数与随机性'
  - version: v2
    msgid: '<20260917153915.1563875-1-christian.loehle@arm.com>'
    date: '2026-09-17'
    summary: '拆 1/2（drop idle recency）+ 2/2（U64_MAX reservoir）'
    review_outcome: 'Vincent 双 Reviewed-by；Peter 表示将排队合入'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待 Peter 将系列合入 tip/sched/core'
contribution_opportunities:
  - kind: testing
    description: '合入后在 8~32 核小系统回归慢路径 idle CPU 选择'
generated_at: '2026-09-19T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260917-007
  - sched-20260916-015
tags:
  - cfs
  - idle
---
