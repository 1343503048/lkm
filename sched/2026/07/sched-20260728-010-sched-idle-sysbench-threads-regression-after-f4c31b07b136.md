# sched idle sysbench threads regression after f4c31b07b136

## TL;DR

Oracle 性能测试发现 commit f4c31b07b136（"sched: idle: Consolidate the handling of two special cases"）导致 MySQL Sysbench threads 在 OCI VM 上出现 10%~29% 的性能回归。讨论持续近一个月，Rafael Wysocki 和 Christian Loehel 参与分析，目前根因指向 tick 停止行为变化，但尚未有正式修复 patch。

## 背景与问题

**复现环境**：
- VM.Standard2.1：x86 OCI VM，1 OCPU / 2 硬件线程，14.5 GB RAM
- VM.Standard.A1.Flex.2：Arm/Ampere A1，2 vCPU 线程，10.9 GB RAM

**回归幅度**：
- VM.Standard2.1：333 → 236（-29.1%）
- VM.Standard.A1.Flex.2：1286 → 1152（-10.4%）

**Bisect 结果**：f4c31b07b136 ("sched: idle: Consolidate the handling of two special cases") 为第一个 bad commit。Revert 后性能恢复。

**关键观察**：两个受影响的 guest 均报告 `cpuidle current_driver = none`，无 `/sys/devices/system/cpu/cpu*/cpuidle` 条目。这属于"无 cpuidle driver"的特殊 idle 路径。

## 技术方案

f4c31b07b136 的改动是合并 idle 循环中两个特殊情况的处理逻辑。改动前：
- 无 cpuidle driver 时：`tick_nohz_idle_stop_tick()` + `default_idle_call()`
- 仅一个 idle state 时：`tick_nohz_idle_retain_tick()` + cpuidle state 0

改动后引入了 previous-wakeup 启发式来决定是否停止 tick，这可能导致原本从不停止 tick 的场景（无 cpuidle driver）开始停止 tick，增加了唤醒延迟。

Rafael Wysocki 确认："I think that this is your case and the tick stops for you sometimes now while it had never stopped before."

## 版本演进与当前进展

- 2026-07-02：Joseph Salisbury（Oracle）首次报告回归
- 2026-07-02：Rafael Wysocki 回复，初步判断是 tick 停止行为变化
- 2026-07-06：Christian Loehel 参与讨论
- 2026-07-24：Joseph 提供 guest 环境详细数据（无 cpuidle driver）
- 2026-07-28：Christian Loehle 最新回复，讨论仍在继续

当前仍处于问题定位阶段，无正式修复 patch。

## Maintainer 意见与讨论焦点

- **Rafael J. Wysocki**（cpuidle/idle maintainer）：确认根因方向是 tick 停止行为变化，但未给出具体修复方案
- **Christian Loehel**（ARM 调度器开发者）：参与分析，关注 previous-wakeup 启发式的合理性
- 核心分歧/未解决问题：
  - guest 环境下 `current_driver = none` 但 `current_governor = menu` 的组合是否正常
  - previous-wakeup 启发式是否应该在无 cpuidle driver 时完全不生效
  - 是应该 revert 还是添加条件判断

## 合入评估

当前无修复 patch 可评估。可能的走向：
1. 直接 revert f4c31b07b136（最简单但会丢失代码整合收益）
2. 在合并后的代码中添加条件：无 cpuidle driver 时不应用 previous-wakeup 启发式
3. 调整启发式阈值使其在少核 VM 环境下不触发 tick 停止

考虑到 Oracle 明确报告了生产环境回归且 bisect 清晰，如果短期内无法达成修复共识，revert 压力会增大。

## 效果评估

回归数据明确：
- x86 2 线程 VM：Sysbench threads -29.1%
- ARM 2 vCPU VM：Sysbench threads -10.4%
- Revert f4c31b07b136 后完全恢复

这是 Oracle 官方性能测试的结果，数据可信度高。

## 我可以参与的点

- 在类似配置（2 核、无 cpuidle driver 的 VM）中复现回归，使用 ftrace 的 `power:cpu_idle` 事件对比 f4c31b07b136 前后的 tick 停止频率和 idle 驻留时间
- 分析 `tick_nohz_idle_stop_tick()` 中 previous-wakeup 启发式的具体判断逻辑，确认在 2 核高负载场景下为何会错误触发
- 如果复现成功，可以提出条件性修复 patch（在无 cpuidle driver 路径中保留原有的 retain_tick 行为）

## 参考链接

- lore thread: 未获取到
- 问题 commit: f4c31b07b136 ("sched: idle: Consolidate the handling of two special cases")
- 报告者: Joseph Salisbury (Oracle)

---
subject: "sched idle sysbench threads regression after f4c31b07b136"
id: sched-20260728-010
date: 2026-07-28
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: null
lore_url: null
authors: [Joseph Salisbury]
maintainers_involved: [Rafael J. Wysocki, Christian Loehel]
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-07-02
    summary: "报告 f4c31b07b136 (sched: idle: Consolidate the handling of two special cases) 引入 Sysbench threads 回归"
    review_outcome: "Rafael 确认可能是 tick 停止行为变化导致；Christian Loehel 参与分析；Oracle 确认 guest 无 cpuidle driver"
upstream_commit: null
fixes_commit: "f4c31b07b136"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["根因尚未完全确认", "guest 环境下 cpuidle 状态不明确"]
  next_action: "需要确认 tick 停止频率变化是否为根因，可能需要 revert 或条件性修复"
contribution_opportunities:
  - kind: testing
    description: "在类似 OCI VM 环境（无 cpuidle driver、少核）中复现回归并收集 ftrace idle 事件数据"
  - kind: discussion
    description: "分析 f4c31b07b136 前后 tick_nohz_idle 行为差异，确认 previous-wakeup 启发式的影响"
generated_at: "2026-07-30T10:00:00"
source_email_count: 1
related_articles: []
tags: [cfs, regression, idle]
---
