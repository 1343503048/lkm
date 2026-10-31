---
id: sched-20261031-004
date: 2026-10-31
subject: 'ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260807214837.863209-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20260807214837.863209-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved: []
current_version: v8
patch_series:
- version: v7
  msgid: <20260807214837.863209-1-sumitg@nvidia.com>
  date: 2026-08-07
  summary: OSPM nominal perf 支持：ACPI 寄存器 + cpufreq ospm_nominal_freq sysfs + policy
    反映
  review_outcome: 09-26 Rafael 催稿；09-28 Christian/Pierre 给接口形态与初值时机评审
- version: v8
  msgid: <20261030172745.2045743-1-sumitg@nvidia.com>
  date: 2026-10-31
  summary: rebase 到 Christian CPPC fixes；ospm_nominal_freq 改可读；effective_nominal()
    统一 boost 上限
  review_outcome: 回应 Christian/Pierre 全部意见；待新一轮评审与 Rafael Ack
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Rafael 最终 Ack 未给，v8 尚无新一轮评审
  - 跨系列 rebase 依赖 Christian 的 CPPC fixes 先合入
  next_action: Rafael/Christian/Pierre 评审 v8 后合入
contribution_opportunities:
- kind: review
  description: 核对 effective_nominal() 与 boost QoS 请求在多核 policy 下的上限一致性及 cpc_desc_lock
    锁粒度
- kind: testing
  description: 在 CPPC 平台验证写入 ospm_nominal_freq 后 boost/limits 一致性（含 hotplug/suspend-resume）
generated_at: '2026-11-01T09:00:00'
source_email_count: 3
related_articles:
- sched-20260808-004
- sched-20260926-008
- sched-20260928-010
tags:
- cpufreq
- cppc
title: 'ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260808-004：Sumit Gupta 的 v7 三片 CPPC 系列——新增 OSPM nominal perf 支持（ACPI 寄存器 + cpufreq `ospm_nominal_freq` sysfs + policy 反映）。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-008-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260926-008</a>：cpufreq 维护者 Rafael Wysocki 主动催稿——近 7 周无人评审则不合入。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-010-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260928-010</a>：Pierre Gondois 与 Christian Loehle 分别评审 v7（接口形态、初值时机、rebase 建议）。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-004-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20261031-004</a>（今天）：v8 发出，逐条消化评审——rebase 到 Christian 的 CPPC fixes 系列、`ospm_nominal_freq` 由 write-only 改为**可读**、用 `cpc_is_writable()` 替代自写函数、boost 关闭时的上限反映用新的 `cppc_cpufreq_effective_nominal()`。作者标注 `Suggested-by: Pierre Gondois`。

## 背景与问题
（承接）CPPC 允许 OS 直接写性能寄存器设定目标。OSPM Nominal Performance 寄存器（ACPI 6.6 §8.4.6.1.2.6）**可写**，让 OSPM 请求一个低于平台标称的 nominal 值；平台把高于该值的性能视为 boost、低于视为 throttle。本系列把这一语义如实反映到 cpufreq 的 boost 与频率上限。今日背景无新增，症结从「评审意见收敛」转为「v8 落地回应」。

## 技术方案
（承接，三片结构不变）今日 v8 的关键变化：

- **patch 1（ACPI）**：改用 Christian 系列提供的 `cpc_is_writable()`（弃用自写的 `cpc_reg_writable()`）；把该寄存器加入驱动写入的 controls 列表；在 `cppc_ospm_nominal_perf_supported()` 中取 `cpc_desc_lock`，防止检查期间 descriptor 被移除。
- **patch 2（cpufreq）**：`ospm_nominal_freq` 改为**读写**属性——读返回「最后一次写入的值」或未设置时的 `<unset>`（寄存器本身不可回读）。这一改动直接回应 Christian 对 write-only 接口的质疑。
- **patch 3（cpufreq）**：新增 `cppc_cpufreq_effective_nominal()`，boost 关闭时用它做上限；写 `ospm_nominal_freq` 时更新 policy limits（因 cpufreq core 的 boost QoS 请求只在 boost 切换时刷新，需驱动自行更新）；boost 关闭时应用新 nominal，`highest_perf == nominal_perf` 的平台通过 sysfs 调低 nominal 可创建出 boost 区间。

## 版本演进与当前进展
*current_version: v8*（2026-10-31，cover `<20261030172745.2045743-1-sumitg@nvidia.com>`）。v7→v8 全量落地 Christian/Pierre 的评审意见，并 rebase 到 Christian 的 CPPC fixes 系列之上。本系列应用在 v7 的「Preserve OSPM-set registers」之上。

## Maintainer 意见与讨论焦点
今日缓存内无新维护者/评审回帖（v8 刚发出）。此前的关键意见与本版回应：

- **Rafael Wysocki（维护者，前几日）**：无人评论则不合入的催稿门槛。
- **Christian Loehle（Arm）**：`ospm_nominal_freq` write-only 别扭 → v8 改为可读。
- **Pierre Gondois（Arm）**：初值时机与 rebase 建议 → v8 用 `effective_nominal()` 统一处理，并采纳其 `Suggested-by`。
- 无 NAK；Rafael 最终 Ack 仍待给。

## 合入评估
*likelihood=medium*。v8 已把前轮评审逐条落地并 rebase 到维护者推进中的 CPPC fixes 系列，合入概率较 v7 上升；但 Rafael 尚未亲自 Ack、v8 尚无新一轮评审。*blocking_issues*：等 Rafael 最终 Ack 与新一轮评审；跨系列 rebase 依赖 Christian 的 CPPC fixes 先合入。*next_action*：Rafael/Christian/Pierre 评审 v8 后合入。

## 效果评估
无性能数据；属电源管理寄存器语义一致性改进。v8 无新增测试数据。

## 我可以参与的点
- **review**：核对 `cppc_cpufreq_effective_nominal()` 与 boost QoS 请求（`boost_freq_req`）在多核 policy 下的上限一致性，以及 `cpc_desc_lock` 的锁粒度。
- **testing**：在 arm64 PCC 或 x86 共享内存 CPPC 平台上验证写入 `ospm_nominal_freq` 后 boost/limits 的即时一致性（含 hotplug/suspend-resume）。

## 参考链接
- v8 cover: https://lore.kernel.org/all/20261030172745.2045743-1-sumitg@nvidia.com/
- 本系列 v7 起点: https://lore.kernel.org/all/20260807214837.863209-1-sumitg@nvidia.com/
- 前置系列「Preserve OSPM-set registers」v7: https://lore.kernel.org/lkml/20261030092416.1993889-1-sumitg@nvidia.com/
