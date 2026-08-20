---
id: sched-20260805-010
date: '2026-08-05'
title: 'cpufreq: intel_pstate: Avoid using DESIRED_PERF when DEC is enabled'
series: 'schedutil: Fix rate limit overflow when clamping frequency'
type: fix
status: under_review
severity: high
merge_likelihood: high
tags:
- cpufreq
- preempt
authors:
- Rafael J. Wysocki <rafael.j.wysocki@intel.com>
- Viresh Kumar <viresh.kumar@linaro.org>
reviewers:
- Viresh Kumar <viresh.kumar@linaro.org>
related_articles: []
emails:
- uid-22691@qq-imap
layout: article
---

# cpufreq: schedutil 修复频率限幅时的 rate_limit 溢出

## 摘要

schedutil 调频器在计算「下一次允许更新频率的时间」（基于 `rate_limit_us`）时，若目标频率被 `policy->min` / `policy->max` 限幅（clamp），限幅后的频率对应的 `transition_delay` 计算会发生**无符号整数溢出/回绕**，导致 `sg_policy->last_freq_update_time` 被设成一个错误的（可能远小于当前时间）值，进而使后续的频率更新被过早或过晚允许，表现为调频抖动甚至短暂「卡在错误频率」。

本日要点（22691）：
- Rafael 给出修复：在做限幅之前先用未限幅的目标频率计算 `next_freq_update_time`，限幅只影响最终写入 `policy->cur` 的频率值，不影响时间窗计算；或者对 `rate_limit` 的累加使用 64 位（`ktime_t`/`u64`）避免回绕。
- Viresh（维护者）确认这是真实 bug，并建议把「限幅不影响时间窗」作为 invariant 在注释里写明，同时加一个最小复现说明（如 `rate_limit_us` 较大 + 频繁触顶 `policy->max` 的突发负载）。

## 技术细节

问题代码（示意）：
```
next_freq = clamp(target_freq, policy->min, policy->max);   // 限幅
sg_policy->last_freq_update_time =
    ktime_get() + rate_limit_for_freq(next_freq);            // 用限幅后频率算延迟
```
当 `next_freq` 因限幅偏离 `target_freq` 较大时，`rate_limit_for_freq()` 的乘除（基于频率比例）可能溢出 `unsigned int` 或算出异常小的延迟。

修复：
```
raw_target = target_freq;
sg_policy->last_freq_update_time =
    ktime_get() + rate_limit_for_freq(raw_target);   // 用原始目标算时间窗
policy->cur = clamp(raw_target, policy->min, policy->max);  // 限幅只作用于写入值
```

## 影响与风险

- 影响面：所有使用 schedutil 的平台（绝大多数 arm64 / x86 默认调频器），影响调频时机正确性；极端情况下表现为性能抖动或能效下降。
- 风险：高（作为 bug 的严重度），但修复局部、易验证；建议尽快合入。
- 触发条件：较大 `rate_limit_us` + 负载频繁触顶/触底 `policy->max`/`min`。

## 评价

明确的真实 bug，维护者（Viresh）已确认，修复方向清晰。合入可能性高，属于应当优先进入 tip/sched 或 cpufreq 的 fix。建议补一个复现/验证说明后提交。
