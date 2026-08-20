---
date: 2026-08-08
series: cpufreq-cppc-ospm-nominal-perf
version: v7
status: in-review
tags:
- cpufreq
related_articles:
- sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug
submitter: Lifeng Zheng
emails:
- uid: 27762
  subject: '[PATCH v7 0/3] ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
- uid: 27763
  subject: '[PATCH v7 2/3] cpufreq: CPPC: Add ospm_nominal_freq attribute'
- uid: 27765
  subject: '[PATCH v7 3/3] cpufreq: CPPC: Reflect the OSPM nominal in boost and limits'
title: 'cpufreq: CPPC 增加 OSPM nominal perf 支持（v7）'
layout: article
---

## 概述

Lifeng Zheng 提交 v7 的 3 片 CPPC cpufreq 系列，增加 **OSPM nominal perf（操作系统电源管理设定的标称性能）** 支持，与 8/7 的 Sumit Gupta "Preserve OSPM-set registers" 系列衔接（本系列构建于其上）。

## 背景

CPPC 允许 OS 直接写性能寄存器设定目标。本系列新增对 OSPM nominal perf 寄存器的支持，使 OS 设定的标称性能能被如实反映到 cpufreq policy 的 boost 与频率上限，保持一致性。

## 三片内容

- **Patch 1（ACPI）**：`ACPI: CPPC: Add ospm_nominal_perf support` — 新增 nominal perf 寄存器支持（含 `cpc_reg_writable()` 辅助判定可写性）。
- **Patch 2（cpufreq）**：`cpufreq: CPPC: Add ospm_nominal_freq attribute` — 新增 `ospm_nominal_freq` sysfs 属性（kHz），追踪寄存器（因寄存器不可回读，故为 write-only，软件侧跟踪请求值）。
- **Patch 3（cpufreq）**：`cpufreq: CPPC: Reflect the OSPM nominal in boost and limits` — 把 OSPM nominal 反映到 policy，使 boost 与频率限制与该寄存器一致。

## 版本演进（v6 → v7）

- 把 patch 1 拆分为 ACPI patch 与 cpufreq patch。
- Patch 1：去掉 `cppc_get_ospm_nominal_perf()`（寄存器 write-only），新增 `cppc_ospm_nominal_perf_supported()` 复用 `cpc_reg_writable()` 可写判定。
- Patch 2：使 `ospm_nominal_freq` write-only，软件侧跟踪而非回读；把寄存器排在 auto_sel 之前存入 save/restore 表。
- Patch 3：重命名 `*_reflect_nominal()` → `*_update_nominal_limits()`；sysfs 写失败时不再 fail；boost 启用时跳过 limit 更新；`cppc_cpufreq_effective_nominal()` 直接从软件状态取值（不会失败）；`init()` 直接检查 `cppc_ospm_nominal_perf_supported()`。

## 状态

v7，依赖于 Sumit Gupta 的 "Preserve OSPM-set registers across hotplug and unload" 系列（`20260806200857.601152-1-sumitg@nvidia.com`），处于评审阶段。

## 参考链接

- 系列：uid 27762 / 27763 / 27765
- 依赖系列分析：sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug
