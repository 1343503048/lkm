# cpufreq: fix policy max not returning to non-boost freq on boost disable

## TL;DR

本文为增量更新，完整脉络见 related_articles（本系列即 schedutil boost 频率处理系列，本文以其 v3 2/2 补丁标题为跟踪入口）。

- sched-20260921-007：Ananthu C V 的 schedutil boost 频率处理修复（v2）。
- sched-20260922-019：Zhongqiu Han 在 SM8850 上二分定位 `db80ad776cd2` 引入问题。
- sched-20260929-004：v3——drop `max_table_freq`、新增 helper、`policy_set_boost` 判「是否有 boost 频率」。
- sched-20260930-012：Oleg 复测给 Tested-by。
- sched-20261011-005：Zhongqiu 新 review（changelog、2/2 前置、has_boost 标志）。
- sched-20261102（今天）：cpufreq 维护者 Viresh Kumar 回 v3 2/2——「若这是 fix 应单独提交以便独立合入」，且坦言「还看不懂当前问题：从 cover 时序看 scaling_max_freq 没回来，但为何？简单 revert freq_table.c 是否能修？」

## 背景与问题

（承接）v3 2/2 修的是「boost 关闭后 `policy->cpuinfo.max_freq` 未能回到非 boost 频率」的问题。今日 Viresh 要求作者把问题机理讲清楚、并先回答「revert 是否即可」。

## 技术方案

（承接）无新代码；Viresh 并非否定方向，而是要求先厘清根因与最小修复（单独成 patch、排查是否 revert `db80ad776cd2` 即可）。

## 版本演进与当前进展

v3；今日为维护者的根因追问。

## Maintainer 意见与讨论焦点

Viresh（维护者）：把 fix 从系列里拆出单独合入；并直指作者尚未给出「为何不回非 boost」的清晰机理。这是当前推进的卡点。

## 合入评估

likelihood=medium。维护者在认真评审但要求补根因分析；作者需回应「revert 是否足够」的问题。

## 效果评估

（承接）Oleg Tested-by 数据：boost 关 4032000→开 4723200→再关 4032000。

## 我可以参与的点

- review：分析 `db80ad776cd2` 与「scaling_max_freq 不回退」的因果，判断 revert 是否充分。
- testing：在 SCMI 等驱动上复测 boost 开关后 policy max 的恢复。

## 参考链接

- lore thread: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-2-68de169498c7@oss.qualcomm.com/

---
id: sched-20261102-024
subject: 'cpufreq: fix policy max not returning to non-boost freq on boost disable'
date: '2026-11-02'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260929-schedutil-boost-frequency-handling-v3-2-68de169498c7@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-2-68de169498c7@oss.qualcomm.com/
authors:
- Ananthu C V
maintainers_involved:
- Viresh Kumar
current_version: v3
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 维护者要求拆出 fix 并讲清根因（revert 是否足够）
  next_action: 作者单独提交 fix、回答根因/revert 可行性
contribution_opportunities:
- kind: review
  description: 分析 db80ad776cd2 与 policy max 不回退的因果
- kind: testing
  description: SCMI 等驱动复测 boost 开关后 policy max 恢复
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20260921-007
- sched-20260922-019
- sched-20260929-004
- sched-20260930-012
- sched-20261011-005
tags:
- cpufreq
- dvfs
generated_at: '2026-11-03T01:26:30'
---
