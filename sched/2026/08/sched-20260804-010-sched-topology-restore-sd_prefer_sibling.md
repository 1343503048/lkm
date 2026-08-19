# sched/topology: Restore SD_PREFER_SIBLING in domains with asymmetric capacity

# sched/topology: 恢复 SD_PREFER_SIBLING（EAS 路径）

## TL;DR
Chen Yu 在 EAS 路径上恢复 `SD_PREFER_SIBLING` 语义：当兄弟域是 MC 且非 cluster 时，倾向把任务集中到更少 CPU 以留出全 idle sibling 节能。v6 已获 Vincent R-b + Tested-by，合入可能性 high。

## 背景与问题
`SD_PREFER_SIBLING` 让调度域倾向于把任务打包到更少 CPU，从而留出完全 idle 的兄弟 CPU（利于节能/涡轮）。早前在 EAS 重构中被弱化/移除，导致在某些 MC（multi-core，非 cluster）拓扑下失去该打包倾向，节能与单线程突发性能受损。

## 技术方案
在 EAS 相关的兄弟域判定中恢复 `SD_PREFER_SIBLING`：当兄弟域为 MC 且非 cluster 时设置该标志，使 wakeup/balancing 倾向集中于更少 CPU。v6 收敛了与 EAS 的互动逻辑。

## 版本演进与当前进展
当前 v6（2026-08-04）。Vincent Guittot Reviewed-by，并附 Tested-by。

## Maintainer 意见与讨论焦点
Vincent Guittot：R-b，认可方向。焦点在与 EAS 放置的互动是否一致，作者已据此收敛。

## 合入评估
合入可能性 high。v6 已 R-b + Tested-by，无架构反对。

## 效果评估
邮件附 Tested-by（含能效/性能验证），属「有实证」的拓扑优化。具体数字未展开，但有测试覆盖。

## 我可以参与的点
- 可审阅恢复后与 EAS 放置的互动是否影响现有能效基准，回帖补充能量/性能权衡分析。

## 参考链接
- lore thread: 未获取到

---
subject: "sched/topology: Restore SD_PREFER_SIBLING in domains with asymmetric capacity"
id: sched-20260804-010
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Chen Yu]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Valentin Schneider]
current_version: v6
patch_series:
  - version: v6
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "在 EAS（energy-aware scheduling）路径上恢复 SD_PREFER_SIBLING 语义：当兄弟域是 MC（multi-core）且非 cluster 时，倾向于把任务集中到更少 CPU 以留出全 idle 的 sibling 节能。Vincent Guittot Reviewed-by，有人 Tested-by。"
    review_outcome: "Vincent Guittot: Reviewed-by。另有 Tested-by 标签。讨论聚焦与 EAS 的互动。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 PeterZ 最终接收；v6 已 R-b + Tested-by，阻力小。"
contribution_opportunities:
  - kind: review
    description: "可审阅 SD_PREFER_SIBLING 恢复后与非 cluster 的 MC 域互动是否影响现有 EAS 放置，回帖能量/性能权衡分析。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [topology, eas, sched_debug]
---
