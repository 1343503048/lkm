# cpufreq: stats: Fix potential out-of-bounds access in deferred reset

## TL;DR
Zhongqiu Han（Qualcomm）修 `cpufreq_stats` 的潜在越界访问：当 `policy->cur` 不在频率表里时 `stats->last_index` 停在 -1，而 deferred reset（`cpufreq_stats_reset_table()`）末尾无条件 `cpufreq_stats_update()`，写 `time_in_state[-1]`。补丁让 reset_table 在 `last_index == -1` 时同样提前返回。Rafael 当日 `Applied as 7.4 material`。

## 背景与问题
`cpufreq_stats_create_table()` 在 `policy->cur` 不在频率表时把 `stats->last_index` 置 -1。commit `40c3bd4cfa6f` 把 stats reset 推迟到 `cpufreq_stats_record_transition()` 开头（在该处 `old_index == -1` 的提前返回检查**之前**），并让 `cpufreq_stats_reset_table()` 末尾无条件 `cpufreq_stats_update()`。于是写 `reset` 属性时若 `last_index == -1`，下次频率变迁就访问 `time_in_state[-1]`。

## 技术方案
单补丁：在 `cpufreq_stats_reset_table()` 里也对 `last_index == -1` 提前返回。`Fixes: 40c3bd4cfa6f`。

## 版本演进与当前进展
*current_version: v1*（`<20261027133332.377546-1-zhongqiu.han@oss.qualcomm.com>`），当日新发并直接合入。

## Maintainer 意见与讨论焦点
Rafael J. Wysocki（PM 维护者）`Applied as 7.4 material, thanks!`。无分歧。

## 合入评估
*likelihood=merged*。已作为 7.4 材料合入。

## 效果评估
正确性修复，越界访问（`time_in_state[-1]`）规避，无性能数据。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间。

## 参考链接
- patch: https://lore.kernel.org/all/20261027133332.377546-1-zhongqiu.han@oss.qualcomm.com/

---
id: sched-20261027-016
date: 2026-10-27
subject: 'cpufreq: stats: Fix potential out-of-bounds access in deferred reset'
subsystem: sched
type: bug
status: merged_tip
severity: medium
thread_root_msgid: '<20261027133332.377546-1-zhongqiu.han@oss.qualcomm.com>'
lore_url: 'https://lore.kernel.org/all/20261027133332.377546-1-zhongqiu.han@oss.qualcomm.com/'
authors:
  - 'Zhongqiu Han'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261027133332.377546-1-zhongqiu.han@oss.qualcomm.com>'
    date: 2026-10-27
    summary: 'reset_table 里对 last_index == -1 提前返回'
    review_outcome: 'Applied as 7.4 material'
upstream_commit: null
fixes_commit: '40c3bd4cfa6f'
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '已作为 7.4 材料合入'
contribution_opportunities: []
generated_at: '2026-10-28T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - cpufreq
---