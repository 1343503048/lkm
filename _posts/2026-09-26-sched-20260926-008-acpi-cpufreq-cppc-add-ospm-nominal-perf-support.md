---
id: sched-20260926-008
date: 2026-09-26
subject: 'ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <CAJZ5v0hhQCGmC8CGKdK_dZT6mUMZv29rgt=GbAp2aC06mH2x2Q@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CAJZ5v0hhQCGmC8CGKdK_dZT6mUMZv29rgt=GbAp2aC06mH2x2Q@mail.gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v7
generated_at: '2026-09-27T01:20:00'
authors:
- Sumit Gupta
maintainers_involved:
- Rafael Wysocki
patch_series:
- version: v7
  msgid: <20260807214837.863209-1-sumitg@nvidia.com>
  date: 2026-08-07
  summary: OSPM nominal perf 支持：ACPI 寄存器 + cpufreq ospm_nominal_freq sysfs + policy
    反映
  review_outcome: 近 7 周无评审；09-26 Rafael 催稿
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无任何 reviewer 意见
  - Rafael 未亲自 Ack
  next_action: CPPC cpufreq reviewer 评审或给 Tested-by
contribution_opportunities:
- kind: review
  description: 审阅三片（ACPI nominal 寄存器 + ospm_nominal_freq sysfs + policy 反映逻辑）
- kind: testing
  description: 在 arm64 PCC 或 x86 共享内存 CPPC 平台验证 nominal 写入后 boost/limits 一致性
source_email_count: 1
related_articles:
- sched-20260808-004
tags:
- cpufreq
title: 'ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260808-004：Sumit Gupta 的 v7 三片 CPPC 系列——新增 OSPM nominal perf（操作系统电源管理设定的标称性能）支持，把标称性能如实反映到 cpufreq 的 boost 与频率上限。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-008-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260926-008</a>（今天）：cpufreq 维护者 Rafael Wysocki 主动催稿——"Dear CPPC cpufreq driver reviewers, please let me know what you think. This is not going to go in without any comments from anyone, as far as I'm concerned."，系列自 08-07 发出后已近 7 周无人评审。

## 背景与问题

（承接 sched-20260808-004）CPPC 允许 OS 直接写性能寄存器设定目标。本系列新增对 OSPM nominal perf 寄存器的支持，使 OS 设定的标称性能能被如实反映到 cpufreq policy 的 boost 与频率上限，避免两者脱节。今天背景无新增，症结从技术转向「缺人评审」。

## 技术方案

（承接 sched-20260808-004）三片：patch 1（ACPI）加 `ospm_nominal_perf` 寄存器支持（含 `cpc_reg_writable()` 可写判定）；patch 2（cpufreq）新增 `ospm_nominal_freq` sysfs 属性（kHz，write-only，软件侧跟踪）；patch 3（cpufreq）把 OSPM nominal 反映到 policy 的 boost 与 limits。方案无变化，卡在无人给意见。

## 版本演进与当前进展

- v7（2026-08-07，`<20260807214837.863209-1-sumitg@nvidia.com>`）：当前版本，拆 ACPI/cpufreq patch、寄存器 write-only 化、`*_reflect_nominal()` 改名 `*_update_nominal_limits()` 等。
- 08-08 起无评审进展。
- 09-26：Rafael Wysocki（`<CAJZ5v0hhQCGmC8CGKdK_dZT6mUMZv29rgt=GbAp2aC06mH2x2Q@mail.gmail.com>`）催评审。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（cpufreq/ACPI 维护者）：明确表态「没有评论就不会合入」，等于把这个系列的门槛压到「任何一位 CPPC cpufreq 驱动的 reviewer 给意见」上。他本人尚未给 Ack，属于维护者催社区先审。无 NAK，分歧不在技术而在参与度。

## 合入评估

*likelihood=low*。近 7 周零评审，维护者已明示无人评论则不合入。*blocking_issues*：无任何 reviewer 意见；Rafael 未亲自 Ack。*next_action*：CPPC cpufreq 相关 reviewer（尤其是 arm64 PCC / 共享内存 CPPC 平台 owner）站出来评审或给出 Tested-by。

## 效果评估

无性能数据；属电源管理寄存器语义一致性改进，正确性验证缺失（正是卡点之一）。

## 我可以参与的点

- `review`：审阅三片（ACPI nominal 寄存器 + cpufreq `ospm_nominal_freq` sysfs + policy 反映逻辑），这是当前最被需要、也最直接能推动系列的动作。
- `testing`：在 arm64 PCC 或 x86 共享内存 CPPC 平台上验证 OSPM nominal 写入后 boost/limits 的一致性。

## 参考链接

- Rafael 催稿: https://lore.kernel.org/all/CAJZ5v0hhQCGmC8CGKdK_dZT6mUMZv29rgt=GbAp2aC06mH2x2Q@mail.gmail.com/
- v7 封面: https://lore.kernel.org/all/20260807214837.863209-1-sumitg@nvidia.com/
