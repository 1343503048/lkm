---
id: sched-20261030-016
date: 2026-10-30
subject: 'cpuidle: idle_miss accounting fixes'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261030083633.1699270-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261030083633.1699270-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 reviewer 反馈
  next_action: 等 cpuidle 维护者/Rafael 等人的 review
contribution_opportunities:
- kind: testing
  description: 在带 timer broadcast 的平台复跑 schbench/tbench/hackbench，验证 cpu_idle_miss
    计数
- kind: review
  description: 核对 entry 快照 latency_req 与 exit disable 检查的组合是否遗漏边界
generated_at: '2026-10-31T09:00:00'
source_email_count: 3
related_articles: []
tags:
- idle
title: 'cpuidle: idle_miss accounting fixes'
layout: article
---

## TL;DR
Christian Loehle（Arm）发 2 补丁修 cpuidle 的 `cpu_idle_miss` 统计：① 把「timer 广播失败导致的浅状态回退」从 above/below miss 记账中排除（广播回退是本该计 miss 的被动行为，会污染观测）；② 在判 below miss 时尊重 entry-time 延迟约束，排除「更深状态存在但违反 latency QoS」造成的假 below miss。`Fixes: 04dab58a39d4`。Orion O6 实测：patch 1 前 8172 次广播回退里记录 6930 次 cpu_idle_miss，之后 7763 次回退里 0 次。除 sysfs above/below 与 tracing 外无功能变化。

## 背景与问题
`/sys/devices/system/cpu/cpuX/cpuidle/state*/above`、`below` 与 `cpu_idle_miss` tracepoint 用于观测 idle 未按要求进入预期深度的频率，是功耗调优的重要信号。两类统计噪声：

1. **timer 广播回退**：`tick_broadcast_enter()` 失败时（无可用广播源），core 会强制进入一个更浅的状态；这是平台约束而非 governor 预测失误，但现有代码仍把它记为 miss，使 above/below 统计与实际调优无关地被抬高。
2. **entry-time 延迟约束**：一个已 enable 的更深状态可能违反 latency QoS 约束，进入它本就不该，却被判为「below miss」。

## 技术方案
- **patch 1**（`cpuidle: Skip miss accounting for timer broadcast fallbacks`）：在 `cpuidle_enter_state()` 里新增 `broadcast_failed` 标志，`tick_broadcast_enter()` 失败并回退浅状态时置位，随后跳过 above/below miss 记账（`goto out`），但仍保留 residency/usage 与 governor 反馈。
- **patch 2**（`cpuidle: Respect latency constraints when accounting below misses`）：entry 时用 `cpuidle_governor_latency_req(dev->cpu)` 存下 governor 延迟上限到 `latency_req`，判 below miss 时跳过 `exit_latency_ns > latency_req` 的状态，避免「更深状态存在但超延迟上限」被记为假 below miss；disable 标志仍在 exit 时检查（其变化预期更少）。

## 版本演进与当前进展
*current_version: v1*（2026-10-30 发出，0/2 + 2 补丁）。当日后无回复。

## Maintainer 意见与讨论焦点
当日无维护者/评审回复（cpuidle 相关维护者尚未表态）。

## 合入评估
*likelihood=unknown*。初版、无 reviewer 反馈；方向（纯统计正确性、Fixes 标签明确、带实测数据）正面，但需过一轮 review。*blocking_issues*：无 reviewer 表态。*next_action*：等 cpuidle 维护者/Rafael 等人的 review。

## 效果评估
Orion O6（menu + TEO governor，schbench/tbench/hackbench）：patch 1 前 8172 次广播回退记录 6930 次 `cpu_idle_miss`，patch 1 后 7763 次回退 0 次 miss，且所有回退均进入 WFI——证明广播回退被正确排除。

## 我可以参与的点
- **testing**：在带 timer broadcast 的平台上复跑 schbench/tbench/hackbench，验证 cpu_idle_miss 计数降至预期。
- **review**：核对 patch 2 中 entry 时快照 `latency_req` 与 exit 时 disable 检查的组合是否遗漏任何边界（如 QoS 动态变化）。

## 参考链接
- lore thread（0/2 封面）: https://lore.kernel.org/all/20261030083633.1699270-1-christian.loehle@arm.com/
