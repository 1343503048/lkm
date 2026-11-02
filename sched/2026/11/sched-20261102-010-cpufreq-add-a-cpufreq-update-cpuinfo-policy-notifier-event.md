# cpufreq: Add a CPUFREQ_UPDATE_CPUINFO policy notifier event

## TL;DR

Hugo Sales 的 RFC（4 patches，v1）：新增 `CPUFREQ_UPDATE_CPUINFO` policy notifier 事件，在 boost 开关等改变 `policy->cpuinfo.max_freq` 的时机通知依赖方（典型是 ACPI processor thermal 的节流步进，它按 `cpuinfo.max_freq` 的固定比例计算）。patch 2/4 让缺 `->set_boost()` 回调的 `intel_pstate` 也在 `__intel_pstate_update_max_freq()` 里发送该事件。本窗口只收到 1/4 与 2/4，暂无回复。

## 背景与问题

开关 boost 会改变 `policy->cpuinfo.max_freq`（amd-pstate、cppc_cpufreq、以及走 `cpufreq_boost_set_sw()` 的驱动都在 `->set_boost()` 里改它）。依赖 `cpuinfo.max_freq` 推导 QoS 请求的订阅者无法得知这一变化——ACPI processor thermal 即一例：其节流步进是 `cpuinfo.max_freq` 的固定比例、仅在写 cooling state 时计算。freq QoS notifier 帮不上忙：它只在 aggregate limit 变化时触发，而 thermal cap 低于两个最大值时，开关 boost 只改 `boost_freq_req` 不改 aggregate。

## 技术方案

新增 `CPUFREQ_UPDATE_CPUINFO` 事件，在 `policy_set_boost()` 于驱动更新 cpuinfo 之后发送；发送 helper 设为全局，使在 `->set_boost()` 之外改 `cpuinfo.max_freq` 的驱动也能发。patch 2/4 在 `intel_pstate` 的 `__intel_pstate_update_max_freq()` 中：当 `no_turbo` 写入或 HWP capability 变化导致 `cpuinfo.max_freq` 改变时，刷新 limits 之前发送该事件。

## 版本演进与当前进展

v1（RFC，2026-11-01），本窗口仅 1/4、2/4，暂无回复。

## Maintainer 意见与讨论焦点

暂无表态（RFC 刚发出）。

## 合入评估

likelihood=unknown。RFC 无人回应，且涉及 cpufreq 通知机制的 AB/BI 变化，需 Viresh 等 cpufreq 维护者定夺。

## 效果评估

无数据；是通知机制新事件，无直接性能测量。

## 我可以参与的点

- review：评估新增全局 notifier 事件对现有 policy notifier 订阅者的冲击（编号/时序）。
- discussion：讨论是否应以更窄的 `->set_boost()` 专用回调替代通用事件。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101185807.112449-1-hugo@hsal.es/

---
type: feature
status: rfc
severity: none
thread_root_msgid: <20261101185807.112449-1-hugo@hsal.es>
authors:
- Hugo Sales
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261101185807.112449-1-hugo@hsal.es>
  date: '2026-11-01'
  summary: 新增 CPUFREQ_UPDATE_CPUINFO notifier 事件，intel_pstate 在 max_freq 变化时发送
  review_outcome: 暂无回复（RFC）
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 无人回应，需 cpufreq 维护者定夺 notifier 机制变更
  next_action: 等 Viresh 等 cpufreq 维护者 review
contribution_opportunities:
- kind: review
  description: 评估新 notifier 事件对现有订阅者的冲击
- kind: discussion
  description: 讨论通用事件 vs set_boost 专用回调的取舍
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 2
related_articles: []
tags:
- cpufreq
- x86
- cppc
id: sched-20261102-010
subject: 'cpufreq: Add a CPUFREQ_UPDATE_CPUINFO policy notifier event'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
