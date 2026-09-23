---
id: sched-20260923-004
subject: 'cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()'
date: '2026-09-23'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <12975163.O9o76ZdvQC@rafael.j.wysocki>
lore_url: https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/
authors:
- Rafael J. Wysocki
maintainers_involved:
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <12975163.O9o76ZdvQC@rafael.j.wysocki>
  date: '2026-09-22'
  summary: 新增 .scale_freq_ref() 回调修正 pressure 回落条件
  review_outcome: Ricardo Neri Tested-by；Rafael 宣布将作为 7.3 fix 排队
upstream_commit: null
fixes_commit: d2d5c129d07e
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Rafael 合入 cpufreq 树并流向 7.3
contribution_opportunities:
- kind: testing
  description: 在非 Intel hybrid 平台复验 .scale_freq_ref() 路径的 pressure 信号
- kind: review
  description: 确认其它 driver 在 arch_scale_freq_ref()==0 时的回落行为不受影响
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
- sched-20260922-009
tags:
- cpufreq
- load_balance
title: 'cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 sched-20260922-009（v1）。Rafael Wysocki 的这个修复今日收获 Ricardo Neri 的 Tested-by（第 25/26 代 Intel 混合架构实测无压力时任务正常散开、施压后迁移、撤压后回流），Rafael 表态：若无异议将作为 7.3 的 fix 收下。合入概率从 high 逼近 merged。

## 背景与问题
背景见 sched-20260922-009：commit `d2d5c129d07e` 让 `cpufreq_update_pressure()` 在 `arch_scale_freq_ref()` 返回 0 时无条件回落到 `policy->cpuinfo.max_freq`，违反「只有容量参考频率已知时才设 cpufreq pressure」的假设，向调度器负载均衡误报压力信号。`Fixes: d2d5c129d07e`，`Reported-by/Tested-by: Jianyong Wu`。

## 技术方案
方案不变（见 sched-20260922-009）：新增 cpufreq driver 回调 `.scale_freq_ref()`，intel_pstate 仅在 scale-invariant capacity 已显式设置时才返回 `cpuinfo.max_freq`，否则返回 0，避免误报压力。

## 版本演进与当前进展
- v1（09-22）当日无 review，今日（09-23）进入验证与收取阶段：Ricardo Neri 给出 Tested-by，Rafael 表态准备作为 7.3 fix 排队。

## Maintainer 意见与讨论焦点
- **Ricardo Neri**（Intel）：在多颗开启非对称容量的 Intel 处理器上实测「本补丁未破坏任何东西」——无压力时任务按预期散开，对部分 CPU 施压后任务正确迁出，撤压后回流。给出 `Tested-by: Ricardo Neri # Intel hybrid parts`。
- **Rafael J. Wysocki**（作者、cpufreq 维护者）：谢谢后明确「In the absence of objections or concerns, I'll queue up this patch as a fix for 7.3.」。无争议、无反对。

## 合入评估
likelihood=high。作者即 cpufreq 维护者，带 Fixes、Reported/Tested-by 与新增的 Intel hybrid 实测 Tested-by，且维护者本人已宣布将作为 7.3 fix 排队。blocking_issues：无（仅待正式合入动作）。next_action：Rafael 合入 tip（cpufreq 树）并流向 7.3。

## 效果评估
无新增 benchmark 数字；Ricardo 的验证为行为正确性验证（任务按压力散开/迁出/回流符合预期），非量化性能数据。

## 我可以参与的点
- kind=testing：在同代 Intel hybrid 之外（如 acpi-cpufreq、amd-pstate）复验 `.scale_freq_ref()` 回调路径下 pressure 信号是否仍正确。
- kind=review：确认 `.scale_freq_ref()` 回调只被 intel_pstate 实现时，其它 driver 的 `arch_scale_freq_ref()==0` 回落行为不受影响。

## 参考链接
- lore（v1 补丁/线程根）: https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/
- Ricardo Neri 回复: https://lore.kernel.org/all/20260923145111.GA24137@ranerica-svr.sc.intel.com/
- Rafael 收取表态: https://lore.kernel.org/all/CAJZ5v0hYU1Ky6L8Oa5ALWw3Z9gbM82oxZGv4cpXmPYwW-DM+6Q@mail.gmail.com/
