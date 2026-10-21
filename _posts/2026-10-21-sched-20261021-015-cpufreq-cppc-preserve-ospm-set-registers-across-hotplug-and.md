---
id: sched-20261021-015
date: 2026-10-21
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/cf4e3153-ff80-4d0d-94f7-572a26f369c1@arm.com/
authors:
- Sumit Gupta
maintainers_involved: []
current_version: v6
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺更广泛评审输入（Rafael 要求）
  - sysfs_store 保存建议待采纳
  next_action: 回应 Christian 建议并收集评审输入
contribution_opportunities:
- kind: review
  description: 评审 sysfs_store 保存改动的可行性与边界
generated_at: '2026-10-22T01:30:00'
source_email_count: 1
related_articles:
- sched-20260926-009
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>：Sumit Gupta 的 CPPC 系列（CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值）经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260917-006</a>：v5 获 K Prateek Nayak 的 x86 实测 Tested-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-009-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260926-009</a>：cpufreq 维护者 Rafael Wysocki 催评审——「没有其他输入我不会应用这个系列」。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-015-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261021-015</a>（今天）：Christian Loehle（Arm）补充建议——所有 ospm-set 寄存器可以在 `sysfs_store` 时就保存下来，从而不必处理 offline/suspend 期间可能发生的读错误。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值，导致离线-上线周期后电源管理配置失效。今日 Christian 指出一个实现层面的额外风险：在 offline/suspend 时读这些寄存器**可能失败**，因此建议改到写 sysfs 时即保存，省去「离线期间读寄存器」的隐患。

## 技术方案
（承接前序版本）把 OSPM 设置的寄存器（如 `auto_select`、`energy_performance_preference_val`）纳入 save/restore 表，跨 hotplug/unload 保留。今日新增实现建议：在 `sysfs_store` 时保存 ospm-set 寄存器，避免 offline/suspend 时的读错误。

## 版本演进与当前进展
*current_version: v6*（当日讨论对象为 `[PATCH v6 4/5]`）。

## Maintainer 意见与讨论焦点
Christian Loehle（Arm）：提出「sysfs_store 时保存」的实现建议，属实现细节优化，未质疑方案本身。系列仍缺更广泛的评审输入（Rafael 此前已催）。

## 合入评估
*likelihood=medium*。已有 x86/arm64 两份路径验证与 Tested-by，但 Rafael 明确「没有更广泛输入不应用」，且仍有实现建议待作者回应。*blocking_issues*：缺更广泛的评审输入；`sysfs_store` 保存建议待作者采纳。*next_action*：作者回应 Christian 建议、继续收集评审输入以满足 Rafael 的收取条件。

## 效果评估
无新增 benchmark。此前已验证 arm64 PCC 与 x86 共享内存两条传输路径下寄存器正确保留。

## 我可以参与的点
- `review`：从 CPPC/ACPI 驱动的角度评审 v6「sysfs_store 保存」改动的可行性与边界（是否有平台在离线时才有真实值等）。

## 参考链接
- Christian 的建议：https://lore.kernel.org/all/cf4e3153-ff80-4d0d-94f7-572a26f369c1@arm.com/
- v6 4/5 patch：https://lore.kernel.org/all/20261020121846.691218-5-sumitg@nvidia.com/
