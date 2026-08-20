---
subject: 'sched/idle: Sysbench threads regression after f4c31b07b136'
id: sched-20260730-003
date: 2026-07-30
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20260729022930.318742-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/lkml/20260729022930.318742-1-zhanxusheng1024@gmail.com
authors:
- Zhan Xusheng
maintainers_involved:
- Christian Loehle
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <20260729022930.318742-1-zhanxusheng1024@gmail.com>
  date: 2026-07-29
  summary: Reports sysbench threads regression after f4c31b07b136 (sched/idle tick
    stop change)
  review_outcome: Christian and Rafael discuss possible vCPU scheduling interaction,
    need more data
upstream_commit: null
fixes_commit: f4c31b07b136
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Root cause unclear - may be hypervisor vCPU scheduling interaction
  - Need more diagnostic data
  next_action: Gather more data on tick wakeup frequency and vCPU behavior
contribution_opportunities:
- kind: testing
  description: Provide data on tick wakeup counts in 'leave tick enabled' case to
    distinguish hypervisor behavior
generated_at: '2026-07-31T00:10:00'
source_email_count: 3
related_articles: []
tags:
- idle
- regression
- perf
title: 'sched/idle: Sysbench threads regression after f4c31b07b136'
layout: article
---

## TL;DR

Zhan Xusheng 报告 commit `f4c31b07b136`（sched/idle tick stop 相关）导致 sysbench threads 性能回退。Christian Loehle 和 Rafael J. Wysocki 讨论认为可能与 hypervisor 的 vCPU 调度交互有关，但目前信息不足以确定 root cause。Rafael 明确表示不会在完全理解问题之前应用任何修改。

## 背景与问题

commit `f4c31b07b136` 修改了 idle tick stop 的行为。报告者在 sysbench threads 测试中观察到性能回退。

问题可能涉及虚拟化环境：
- x86 guest 的 `arch_cpu_idle()` 调用 `native_safe_halt()`，trap 到 host
- host 可能根据 guest tick 状态做出不同的 vCPU 调度决策
- tick 保持开启意味着 vtimer 更早触发，可能影响 host 对 vCPU 的调度

## 技术方案

Christian Loehle 分析两个可能原因：
1. Hypervisor 根据 vCPU 的 vtimer 触发时间改变行为（tick 保持开启 = 更早触发）
2. tick 唤醒本身导致观察到的行为差异

建议区分方法：统计 "leave tick enabled" 情况下有多少唤醒是 tick 唤醒。

Rafael J. Wysocki 表示：
> "I'm not going to apply any changes related to this without a clear understanding of what is really going on and there is too little information for that ATM."

## 版本演进与当前进展

- 2026-07-29: Zhan Xusheng 报告回归
- 2026-07-30: Christian Loehle 分析可能原因，建议收集更多数据
- 2026-07-30: Rafael J. Wysocki 回复，认为 host 可能在利用 guest tick stop 行为做 vCPU 调度决策

## Maintainer 意见与讨论焦点

- Christian Loehle: 认为稍微延迟的 idle entry 不足以解释大差异，更可能是 hypervisor 行为变化
- Rafael J. Wysocki: 需要完全理解问题才能应用修改，当前信息不足

## 合入评估

- **likelihood**: unknown
- 回归已确认但 root cause 不明
- 可能涉及虚拟化环境的复杂交互
- 需要更多诊断数据

## 效果评估

- sysbench threads: 性能回退（具体幅度未在邮件中明确）
- 暂无量化数据

## 我可以参与的点

- **提供诊断数据**：如果有类似虚拟化环境，可以测试并统计 tick 唤醒频率，帮助区分两种可能原因
- 如果有裸金属环境的对比数据，可以帮助确认是否为虚拟化特定问题

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260729022930.318742-1-zhanxusheng1024@gmail.com
- tip-bot commit: 未获取到
- stable backport: 未获取到
