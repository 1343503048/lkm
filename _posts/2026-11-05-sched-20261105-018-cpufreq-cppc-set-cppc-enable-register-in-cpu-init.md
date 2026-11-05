---
id: sched-20261105-018
date: 2026-11-05
subject: 'cpufreq: CPPC: Set CPPC Enable register in cpu_init'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261105123244.3132560-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20261105123244.3132560-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261105123244.3132560-1-sumitg@nvidia.com>
  date: 2026-11-05
  summary: cpu_init 起始处调 cppc_set_enable()，写失败仅记日志。
  review_outcome: Loehle 提失败语义/其它失败路径/resume 重写等开放问题。
upstream_commit: null
fixes_commit: 5477fb3bd1e8
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 写失败的 fatal 语义未定
  - 失败路径与 resume 的 set_enable 处理待澄清
  next_action: 作者回应 Loehle 生命周期问题并可能补 set_enable(false)/resume
contribution_opportunities:
- kind: testing
  description: 在 AArch64 平台验证 CPPC 变频与 hotplug/resume 后仍生效
- kind: review
  description: 核对失败语义与 resume 重写的必要性
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- cpufreq
title: 'cpufreq: CPPC: Set CPPC Enable register in cpu_init'
layout: article
---

## TL;DR

Sumit Gupta 从「autonomous mode boot 参数」系列里拆出的独立 bugfix：cppc_cpufreq 驱动从不写 ACPI CPPC Enable 寄存器，导致像 NVIDIA GB10 这类平台不写该寄存器就不会启用 CPPC、CPU 永远停在最低频率。补丁在 `cppc_cpufreq_cpu_init()` 开头调 `cppc_set_enable()`，`Fixes: 5477fb3bd1e8` 且 `Cc: stable`。Christian Loehle 提出「失败是否该 fatal、其它失败路径是否需 set_enable(false)、resume 是否需重写」等开放问题。

## 背景与问题

按 ACPI 6.x 规范（s8.4.6.1.4 CPPC Enable register），「若平台支持，OSPM 应向该寄存器写 1 以启用本处理器上的 CPPC；若未实现，OSPM 假定平台始终启用 CPPC」。但 cppc_cpufreq 驱动从不写该寄存器。在 NVIDIA GB10 上，不写该寄存器就不会启用 CPPC，导致 CPU 一直停在最低频率。Jiri Benc 因此建议把这部分从 autonomous mode 系列拆出、单独发。

## 技术方案

在 `cppc_cpufreq_cpu_init()` 起始处调用 `cppc_set_enable()`；写失败仅记日志、不视为致命（该寄存器本就可选）。改动 `drivers/cpufreq/cppc_cpufreq.c` 8 行量级。

## 版本演进与当前进展

*current_version: v1（独立补丁，2026-11-05）*。原为 v5 autonomous-mode 系列（20260623080652）的 patch 1/2，今日拆出单发。

## Maintainer 意见与讨论焦点

无 cpufreq 维护者直接表态。Jiri Benc（Red Hat）推动拆分并说明 GB10 的实际影响。Christian Loehle（ARM）提出四点：amd-pstate 已这么写所以方向 OK；是否应让失败变成 fatal；其它失败路径是否要 `set_enable(false)`；resume 时是否需重新写 enable。这些尚未有作者回应。

## 合入评估

*likelihood=medium*。带 Fixes 与 stable 标注、有明确平台需求，但 Loehle 的失败处理/生命周期问题需作者澄清。*blocking_issues*：① 写失败的语义（fatal vs 非 fatal）；② 失败路径与 resume 的 set_enable 处理。*next_action*：作者回应 Loehle 的生命周期问题并可能补 set_enable(false)/resume 重写。

## 效果评估

Jiri Benc 描述实际影响：GB10 不写寄存器则 CPPC 未启用、CPU 保持最低频率（功能/性能缺失）。未附量化数字。

## 我可以参与的点

- testing：在有 CPPC Enable 寄存器的 AArch64 平台验证补丁后 CPU 能正确变频、且 hotplug/resume 后仍生效。
- review：核对失败语义与 resume 重写的必要性（Loehle 提出的开放点）。

## 参考链接

- lore thread（独立补丁）: https://lore.kernel.org/all/20261105123244.3132560-1-sumitg@nvidia.com/
- v5 系列出处: https://lore.kernel.org/lkml/20260623080652.3353386-1-sumitg@nvidia.com/
