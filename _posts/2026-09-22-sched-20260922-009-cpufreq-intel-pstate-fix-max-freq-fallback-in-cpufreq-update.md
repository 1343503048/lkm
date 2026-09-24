---
id: sched-20260922-009
date: '2026-09-22'
subject: 'cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <12975163.O9o76ZdvQC@rafael.j.wysocki>
lore_url: https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/
authors:
- Rafael J. Wysocki
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <12975163.O9o76ZdvQC@rafael.j.wysocki>
  date: '2026-09-22'
  summary: 新增 .scale_freq_ref() 回调，修正 pressure 的 max_freq 回落条件
  review_outcome: 当日无 review 回复
upstream_commit: null
fixes_commit: d2d5c129d07e
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待合入或后续 review
contribution_opportunities:
- kind: testing
  description: 在 intel_pstate 平台验证 scale-invariant capacity 两路径的 pressure 信号
- kind: review
  description: 核查 .scale_freq_ref() 语义与其它 cpufreq driver 的 pressure 假设一致性
generated_at: '2026-09-23T00:00:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
- load_balance
title: 'cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()'
layout: article
---

## TL;DR
Rafael Wysocki 修复 `d2d5c129d07e` 引入的 regrression：`cpufreq_update_pressure()` 在 `arch_scale_freq_ref()` 返回 0 时无条件回落到 `policy->cpuinfo.max_freq`，导致调度器负载均衡中意外出现 cpufreq 压力信号。补丁新增 driver 回调 `.scale_freq_ref()`，让 intel_pstate 仅在容量参考频率已知时才回落，否则保持无压力。这是与 schedutil 压力机制直接相关的 cpufreq 修复。

## 背景与问题
commit `d2d5c129d07e`（"cpufreq: Make cpufreq_update_pressure() fall back to cpuinfo.max_freq"）后，某些此前不出现 cpufreq pressure 的场合，压力信号意外出现在 CPU 负载均衡器中，造成困惑。调度器本假设「只有 CPU 容量参考频率已知时才设置 cpufreq pressure」，该 commit 违反了这个假设。但某些情形下容量参考频率其实已知、只是 `arch_scale_freq_ref()` 返回 0，此时应该能正确设置 pressure。`Fixes: d2d5c129d07e`，`Reported-by/Tested-by: Jianyong Wu <wujianyong@hygon.cn>`。

## 技术方案
引入新的 cpufreq driver 回调 `.scale_freq_ref()` 返回 CPU 容量参考频率；`cpufreq_update_pressure()` 在 `arch_scale_freq_ref()==0` 时改调该回调（若存在），而非无条件回落 `cpuinfo.max_freq`。intel_pstate 实现该回调：仅当该 CPU 的 scale-invariant capacity 已显式设置（`capacity_perf` 非空）时才返回 `cpuinfo.max_freq`，否则返回 0。

## 版本演进与当前进展
v1 当日发出，附 `Fixes:` 与 `Tested-by`。未见当日 review 回复。

## Maintainer 意见与讨论焦点
当日无 review 回复，为作者（cpufreq 维护者本人）自提修复。无争议。

## 合入评估
*likelihood=high*。作者即 cpufreq 子系统维护者，带 Fixes 与 Tested-by，改动小而聚焦；但当日尚未见其他维护者表态或合入通知，故取 high 而非 merged。blocking_issues 无明确项；next_action 等待合入或后续 review。

## 效果评估
无量化 benchmark；本质是正确性修复——避免 cpufreq pressure 信号在容量参考频率未知时误报进负载均衡。

## 我可以参与的点
- **testing**：在 intel_pstate 平台（尤其 scale-invariant capacity 未设置/已设置的两种路径）上验证 pressure 信号行为。
- **review**：核查 `.scale_freq_ref()` 回调语义是否与其它 cpufreq driver 的 pressure 假设一致。

## 参考链接
- lore thread: https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/
