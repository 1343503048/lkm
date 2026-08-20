---
id: sched-20260806-006
date: '2026-08-06'
title: 'sched/cpufreq: Update schedutil''s DVFS request to reach the boost frequencies'
series: 'sched/cpufreq: Fix schedutil''s boost frequency handling'
type: fix
status: under_review
severity: high
merge_likelihood: medium
tags:
- cpufreq
- preempt
authors:
- Sibi Sankar <quic_sibis@quicinc.com>
- Viresh Kumar <viresh.kumar@linaro.org>
- Christian Loehle <christian.loehle@arm.com>
- Vincent Guittot <vincent.guittot@linaro.org>
- Hongyan Xia <hongyan.xia@arm.com>
- Dmitry Baryshkov <dmitry.baryshkov@oss.qualcomm.com>
- Zhongqiu Han <quic_zhonghan@quicinc.com>
reviewers:
- Viresh Kumar <viresh.kumar@linaro.org>
- Christian Loehle <christian.loehle@arm.com>
- Vincent Guittot <vincent.guittot@linaro.org>
related_articles: []
emails:
- uid-23730@qq-imap
- uid-23731@qq-imap
- uid-24908@qq-imap
- uid-24906@qq-imap
- uid-24155@qq-imap
- uid-24525@qq-imap
- uid-24446@qq-imap
- uid-24325@qq-imap
- uid-24226@qq-imap
layout: article
---

# sched/cpufreq: 修复 schedutil 对 boost 频率的 DVFS 请求处理

## 摘要

Sibi Sankar（Qualcomm）的 2-patch 系列修复 **schedutil 在处理 boost 频率时的 DVFS 请求问题**，涉及 x86 Turbo Boost 与 ARM 平台（含 CXM、scaling_cur_freq 返回 0 的异常）。本日可见 vN 0/2 cover（23730）与 2/2（23731）及多轮 review（Viresh/Christian/Vincent/Hongyan/Dmitry/Zhongqiu）。

- **Patch 1**：`cpufreq: allow cpuinfo max to decrease when boost is disabled` — 禁用 boost 时允许 `policy->cpuinfo.max_freq` 回落（此前被冻结在 boost 上限），避免 schedutil 基于错误的 max 计算频率。
- **Patch 2**：`sched/cpufreq: Update schedutil's DVFS request to reach the boost frequencies` — 让 schedutil 的 DVFS 请求真正能触达 boost 频率区间。

争议点（来自 review）：
- Christian：质疑 patch1 是否会与 `scaling_cur_freq` 的返回逻辑冲突（某些平台 boost 禁用后仍应展示原始 max）。
- Hongyan/Vincent：要求明确 boost 区间在 `schedutil`'s `get_next_freq()` 里如何映射到 `policy->max`，避免「请求 >max」被 silently clamp。
- Dmitry/Zhongqiu：在禁用 boost 路径上需保证 `cpuinfo.max_freq` 的并发读取一致（`READ_ONCE/WRITE_ONCE`）。

## 技术细节

patch2 思路（示意）：
```
// 让 next_freq 在 boost 启用时可超过 policy->min..policy->max
// 而是基于 policy->cpuinfo.max_freq（含 boost 上限）调度
next_freq = map_util_freq(util, cpuinfo.max_freq_with_boost, ...);
if (boost_disabled) next_freq = clamp(next_freq, policy->min, policy->cpuinfo.orig_max);
```

patch1：在 `cpufreq_disable_boost()`/驱动回调里允许 `cpuinfo.max_freq = policy->cpuinfo.orig_max`（不再被 boost 上限锁定）。

## 影响与风险

- 影响面：schedutil 调频器在 x86（Turbo）/ ARM（CXM 等）上的 boost 行为；影响能效与峰值性能。
- 风险：高（作为 bug 严重度）。改动调频核心映射，错误实现可能导致频率卡在 boost 上限（功耗升高）或达不到 boost（性能下降）；需多平台验证 + 并发保护。
- 收益：修复 schedutil 对 boost 频率的 DVFS 请求失真，使能效/性能意图正确落地。

## 评价

方向合理、reviewer 阵容强（Viresh 为 cpufreq 维护者）。当前仍处 review（多轮 nit + 并发保护要求），合入可能性中等—高。建议落实 `READ_ONCE/WRITE_ONCE` 与 boost 映射语义澄清后推进。与 08-05-010（rate_limit 溢出）同属 cpufreq/schedutil 修复簇。
