# cpufreq: amd-pstate: Update Zen6 client EPP tuning values

> **subject**：`cpufreq: amd-pstate: Update Zen6 client EPP tuning values`

## TL;DR

Vishal Badole 的 amd-pstate Zen6 客户端 EPP（Energy Performance Preference）调参补丁：在平台特性刻画基础上进一步调整 per-CPU-type EPP 值（performance 核的 `power` 档 64→115、low-power 核的 `balance_performance` 51→64、`power` 115→64），使每类核用上各自预期的 EPP 设定。Mario Limonciello 当日回复「Applied to superm1/linux.git bleeding-edge. I'll include this in my last PR for 7.4」。

## 背景与问题

这是 Mario Limonciello 早前「cpufreq/amd-pstate: Add EPP tunings for Zen6 client platforms」的后续微调：Zen6 client 平台的 per-CPU-type EPP 值基于平台特性刻画需要进一步 tuning，调整 performance 核与 low-power 核的若干 EPP 档位，使每类核使用其预期（intended）的 EPP 设定。纯调参，无功能性 bug。

## 技术方案

改动仅在 `drivers/cpufreq/amd-pstate.c` 的 `epp_soc_zen6_client` 结构（+3/−3）：performance 核 `power` 64→115；low-power 核 `balance_performance` 51→64、`power` 115→64。基于 Mario 的提交 `114a157e8d30`（"cpufreq/amd-pstate: Add EPP tunings for Zen6 client platforms"）。

## 版本演进与当前进展

v1（09-28 发出，`<20260928203523.1290623-1-Vishal.Badole@amd.com>`）。当日 Mario Limonciello 回复已应用。

## Maintainer 意见与讨论焦点

- **Mario Limonciello**（amd-pstate 维护者）：`Applied to superm1/linux.git bleeding-edge.`，并称将放进他给 7.4 的最后一个 PR。补丁本身已带 `Reviewed-by: Mario Limonciello`。
- 无 NAK，无争议。

## 合入评估

*likelihood=merged*。维护者（Mario）已应用进 amd-pstate 维护树（superm1/linux.git bleeding-edge），并明确纳入 7.4 最后一个 PR。*blocking_issues*：无。*next_action*：跟踪 7.4 合并窗口 amd-pstate/cpufreq PR 是否带上本调参。

## 效果评估

无量化数据；属平台调参（EPP 档位修正），效果体现在 Zen6 client 各类核的能效/性能档位符合预期，邮件未附对比数据。

## 我可以参与的点

- `testing`：在 Zen6 client 平台上验证新 EPP 档位下的功耗/性能表现，回帖佐证调参合理性（邮件未附任何数字）。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260928203523.1290623-1-Vishal.Badole@amd.com/
- Mario 收取回复: https://lore.kernel.org/all/83294b60-a371-43b8-be01-2ff122df2b5f@amd.com/

---
id: sched-20260929-009
date: '2026-09-29'
subject: 'cpufreq: amd-pstate: Update Zen6 client EPP tuning values'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: '<20260928203523.1290623-1-Vishal.Badole@amd.com>'
lore_url: 'https://lore.kernel.org/all/20260928203523.1290623-1-Vishal.Badole@amd.com/'
authors:
  - 'Vishal Badole'
maintainers_involved:
  - 'Mario Limonciello'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260928203523.1290623-1-Vishal.Badole@amd.com>'
    date: '2026-09-28'
    summary: '调整 Zen6 client 的 per-CPU-type EPP 值（performance power 64→115、low-power balance_performance 51→64/power 115→64）'
    review_outcome: 'Mario Limonciello Applied to superm1/linux.git bleeding-edge，将纳入 7.4 PR'
upstream_commit: null
fixes_commit: null
merged_branch: 'superm1/linux.git bleeding-edge'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 7.4 合并窗口 amd-pstate/cpufreq PR 带上本调参'
contribution_opportunities:
  - kind: testing
    description: '在 Zen6 client 平台验证新 EPP 档位的功耗/性能并回帖佐证'
generated_at: '2026-09-30T01:15:00'
source_email_count: 2
related_articles: []
tags:
  - cpufreq
---