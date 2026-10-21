# sched_ext: Remove the foreign CPU check from the kick_sync wait

## TL;DR
Andrea Righi 发往 sched_ext 的补丁（其 3 补丁系列之 3/3）：在 kick_sync wait 中移除 foreign CPU 检查。当日 Tejun Heo 已将其收取到 `sched_ext/for-7.5`。

## 背景与问题
在 series 2/3 将 deferred actions 改用 `irq_work` 后，kick_sync wait 里原先用于规避平衡回调跨 CPU 问题的 foreign CPU 检查变得不再必要，本补丁将其移除。

## 技术方案
单补丁：从 kick_sync wait 路径移除 foreign CPU 检查（`sched_ext: Remove the foreign CPU check from the kick_sync wait`），享受 2/3 的 irq_work 改造带来的简化。

## 版本演进与当前进展
*current_version: v1*。作为系列 3/3 发出（`<20261020084400.845842-4-arighi@nvidia.com>`），当日即被 Tejun 收取。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）直接收取到 `sched_ext/for-7.5`，无额外意见。

## 合入评估
*likelihood=merged*。已由 Tejun 收取到 `sched_ext/for-7.5`。

## 效果评估
未提供性能基准，属对 2/3 改造的配套简化。

## 我可以参与的点
当前无即时参与点。

## 参考链接
- 补丁 3/3：https://lore.kernel.org/all/20261020084400.845842-4-arighi@nvidia.com/
- Tejun 收取回帖：https://lore.kernel.org/all/1a2249f7b86926dc7c617424853af24c@kernel.org/

---
id: sched-20261021-007
date: 2026-10-21
subject: "sched_ext: Remove the foreign CPU check from the kick_sync wait"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261020084400.845842-4-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261020084400.845842-4-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261020084400.845842-4-arighi@nvidia.com>"
    date: 2026-10-20
    summary: "kick_sync wait 移除 foreign CPU 检查"
    review_outcome: "Tejun 收取到 sched_ext/for-7.5"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.5"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已收取，无需进一步动作"
contribution_opportunities: []
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, proxy_execution]
---