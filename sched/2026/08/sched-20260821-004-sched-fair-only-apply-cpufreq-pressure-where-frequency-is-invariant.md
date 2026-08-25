---
id: sched-20260821-004
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260821073927.455475-1-wujianyong@hygon.cn>"
lore_url: "https://lore.kernel.org/lkml/20260821073927.455475-1-wujianyong@hygon.cn/"
authors: ["Wu Jianyong"]
maintainers_involved: ["Vincent Guittot"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260821073927.455475-1-wujianyong@hygon.cn>"
    date: 2026-08-21
    summary: "仅在频率不变架构上应用 cpufreq pressure"
    review_outcome: "Vincent Guittot 质疑修复必要性"
upstream_commit: null
fixes_commit: "d2d5c129d07e"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "需要回应 Vincent 关于频率不变性与 utilization 关系的质疑"
  next_action: "作者需解释具体触发场景和数据"
contribution_opportunities:
  - kind: testing
    description: "在非频率不变架构上测试 cpufreq pressure 对调度的影响"
generated_at: "2026-08-21T10:00:00"
source_email_count: 2
related_articles: []
tags: ["sched/fair", "cpufreq", "frequency_invariance"]
---

## TL;DR

cpufreq pressure 在非频率不变架构上会错误地降低 CPU capacity，导致利用率计算失衡。Wu Jianyong 的修复仅在 `arch_scale_freq_invariant()` 为真时应用 pressure，但 Vincent Guittot 质疑修复的必要性。

## 背景与问题

`cpufreq_get_pressure()` 通过 `cpuinfo.max_freq` 与当前频率之比降低 CPU capacity。在频率不变架构上，utilization 也按同样比例缩放，两边对等。但在非频率不变架构上，utilization 不随频率缩放，只降 capacity 不降 utilization，导致满载 CPU 报告的 utilization 超过被降低后的 capacity。

Commit `d2d5c129d07e` 让 `cpufreq_update_pressure()` 回退到 `cpuinfo.max_freq`，使这个问题变得可达。

## 技术方案

在 `get_actual_cpu_capacity()` 中增加 `arch_scale_freq_invariant()` 检查：
- 频率不变：正常应用 `max(hw_load, cpufreq_pressure)`
- 非频率不变：忽略 cpufreq pressure，仅使用 `hw_load`

```c
if (arch_scale_freq_invariant())
    pressure = max(pressure, cpufreq_get_pressure(cpu));
return capacity - pressure;
```

## 版本演进与当前进展

v1 刚发出。Vincent Guittot 质疑："Even with frequency invariance, utilization can exceed capacity, only the time to reach it will change. What issue do you try to fix?"

## Maintainer 意见与讨论焦点

Vincent Guittot 对修复的必要性提出质疑，认为即使有频率不变性，utilization 也可能超过 capacity。这暗示可能需要更深入的讨论或不同的修复方案。

## 合入评估

- **likelihood**: medium
- **blocking_issues**: 需要回应 Vincent 的质疑，说明具体触发场景
- **next_action**: 作者需要解释在非频率不变系统上观察到的具体问题

## 效果评估

暂无 benchmark 数据。修复的是理论上的计算不一致，实际影响取决于具体硬件和负载。

## 我可以参与的点

- 在非频率不变架构（如某些 ARM 平台）上测试 cpufreq pressure 对调度决策的影响
- 提供具体场景下 utilization > capacity 的数据

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821073927.455475-1-wujianyong@hygon.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到
