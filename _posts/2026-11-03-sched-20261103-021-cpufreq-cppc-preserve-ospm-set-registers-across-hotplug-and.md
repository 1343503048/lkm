---
id: sched-20261103-021
date: 2026-11-03
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261030092416.1993889-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20261030092416.1993889-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved:
- Christian Loehle
current_version: v7
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 确认 v5 时期评审点已解决，等 Rafael 收取。
contribution_opportunities:
- kind: testing
  description: x86 非 ACPI-CPPC 或其它平台复验 hotplug/unload 寄存器保留。
- kind: review
  description: 核对 v5→v7 是否已回应 Pierre 的评审点。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20260928-011
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Sumit Gupta 的 CPPC 系列——在 CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值，避免离线-上线周期后电源管理配置失效。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>：系列经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260917-006</a>：v5 获 K Prateek Nayak 的 x86 实测 Tested-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-009-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260926-009</a>：Rafael Wysocki 催评审输入。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-011-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260928-011</a>：Pierre Gondois 对 v5 给出实质评审（save/restore 表结构、suspend 最低频率、逻辑移入 `cppc_set_perf()`）。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-021-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20261103-021</a>（今天）：系列已到 v7，Christian Loehle（Arm）对 2/5 给 Reviewed-by、对 0/5 给 Tested-by（Orion O6、AmpereOne、Blackview Ryzen 5 7430U，native/emulated CPPC hotplug、S3/s2idle、amd-pstate 三模式）——评审与测试支持进一步充实。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-011-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260928-011</a>）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值，导致离线-上线周期后电源管理配置失效。今日无背景新增，症结仍是评审与测试的收敛。

## 技术方案

（承接）把 OSPM 设置的寄存器（如 `auto_select`、`energy_performance_preference_val`）纳入 save/restore 表，跨 hotplug 与 unload 保留。v7 中的 2/5（"Keep the policy across CPU hotplug"）今日获 Reviewed-by，无新代码。

## 版本演进与当前进展

*current_version: v7*（cover msgid 20261030092416.1993889-1-sumitg@nvidia.com，2026-10-30 发出）。今日 Christian Loehle 给出 Reviewed-by（2/5）与 Tested-by（0/5）。

## Maintainer 意见与讨论焦点

Christian Loehle（Arm）Tested：Orion O6、AmpereOne、Blackview Ryzen 5 7430U（仅 ACPI-CPPC）上，native 与 emulated CPPC hotplug、Blackview S3 与 AmpereOne s2idle、amd-pstate active/passive/guided 三模式下，「未观察到 restore 顺序违例」。无 NAK；较 v5 时期（Rafael 催评审）已进入有测试背书阶段。

## 合入评估

*likelihood=high*。v7 有维护者侧 Reviewer（Christian）的 Tested-by/Reviewed-by，方向无异议；距合入只差 Rafael 的最终收取与前序评审点是否已解决。*next_action*：确认 v5 时期 Pierre 的评审点（save/restore 表结构、suspend 最低频率）已在 v6/v7 解决后，等 Rafael 收取。

## 效果评估

Christian 实测覆盖多平台/多模式 hotplug 与休眠，报告「未观察到 restore 顺序违例」；无量化性能数据。

## 我可以参与的点

- testing：在 x86 非 ACPI-CPPC 或其它 ACPI 平台上复验 hotplug/unload 的寄存器保留。
- review：核对 v5→v7 是否已回应 Pierre 的 save/restore 表结构与 suspend 语义意见。

## 参考链接

- lore thread（v7 cover）: https://lore.kernel.org/all/20261030092416.1993889-1-sumitg@nvidia.com/
