---
id: sched-20260806-007
date: '2026-08-06'
title: 'cpufreq: schedutil: Fix rate limit overflow'
series: 'schedutil: Fix rate limit overflow when clamping frequency'
type: fix
status: under_review
severity: high
merge_likelihood: high
tags:
- cpufreq
- preempt
authors:
- Hui Su <hui.su@linux.dev>
- Rafael J. Wysocki <rafael.j.wysocki@intel.com>
- Viresh Kumar <viresh.kumar@linaro.org>
- Zhongqiu Han <quic_zhonghan@quicinc.com>
reviewers:
- Viresh Kumar <viresh.kumar@linaro.org>
- Rafael J. Wysocki <rafael.j.wysocki@intel.com>
related_articles:
- sched-20260805-010
emails:
- uid-24824@qq-imap
- uid-24803@qq-imap
- uid-24613@qq-imap
- uid-24438@qq-imap
- uid-23848@qq-imap
- uid-23944@qq-imap
layout: article
---

# cpufreq: schedutil 修复频率限幅时的 rate_limit 溢出（v3）

## 摘要

Hui Su 的「schedutil 频率限幅时 rate_limit 计算溢出」修复系列推进到 **v3**，本日可见 v3 0/2（24824）及 Rafael 的 review（24803）。延续 08-05-010（已识别为明确 bug、Viresh 确认）。

问题：在 `get_next_freq()` 里把「限幅后的频率」用于 `rate_limit_for_freq()` 的时间窗计算，限幅偏离原始目标较大时该乘除可能溢出 `unsigned int`，使 `sg_policy->last_freq_update_time` 异常，导致调频抖动或短暂卡在错误频率。

v3 变化（相对 v2）：
- Rafael 要求：把「限幅只影响最终写入频率」与「时间窗用原始目标频率算」做成 invariant，并用独立 helper 表达，便于 review。
- 引入 `READ_ONCE/WRITE_ONCE` 保护 `sg_policy->last_freq_update_time` 的并发读写。
- Zhongqiu 在 23944 等邮件里补了复现说明（较大 `rate_limit_us` + 突发负载频繁触顶 `policy->max`）。

## 技术细节

v3 修复（示意）：
```
raw_target = target_freq;                                  // 未限幅
next_freq = clamp(raw_target, policy->min, policy->max);    // 限幅仅作用于写入
// 时间窗用原始目标，避免限幅后乘除溢出
WRITE_ONCE(sg_policy->last_freq_update_time,
           ktime_get() + rate_limit_for_freq(raw_target));
policy->cur = next_freq;
```

## 影响与风险

- 影响面：所有使用 schedutil 的平台，影响调频时机正确性；极端情况下性能抖动/能效下降。
- 风险：高（bug）。但修复局部、已被 maintainer（Viresh/Rafael）review 并给 R-b/建议，风险可控。
- 触发条件：较大 `rate_limit_us` + 负载频繁触顶/触底 `policy->max`/`min`。

## 评价

明确的真实 bug，维护者已介入并给出改进方向，v3 已吸收 Rafael 的 invariant/helper 建议。合入可能性高，建议作为 cpufreq fix 优先提交（与 08-05-010 同系列，现为 v3）。
