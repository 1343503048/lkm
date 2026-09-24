---
id: sched-20260917-006
date: '2026-09-17'
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260916103820.1760297-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20260916103820.1760297-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved:
- K Prateek Nayak
current_version: v5
patch_series:
- version: v5
  msgid: <20260916103820.1760297-1-sumitg@nvidia.com>
  date: '2026-09-16'
  summary: CPPC 热插拔/卸载保留 OSPM 寄存器；本日补 x86 实测（K Prateek Tested-by）
  review_outcome: K Prateek 实测定通过并给出 Tested-by，作者确认收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺 cpufreq 维护者最终 Ack
  next_action: 作者附上新增标签后等待维护者收取
contribution_opportunities:
- kind: testing
  description: 在其它 CPPC 平台（共享内存 x86 或 arm64 PCC）复测寄存器保留
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
- sched-20260827-007
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR
增量更新：Sumit Gupta 的 CPPC v5 系列（保留 OSPM 设置的寄存器）获得 K Prateek Nayak 的 x86 实测 Tested-by——K Prateek 把 Kconfig 改成可在 x86 上编译驱动后，在 Zen3 共享内存 CPPC 上验证 `auto_select` 与 `energy_performance_preference_val` 在 offline-online 周期后正确保留。Sumit 确认会加 Tested-by 与 patch 2 的 Reviewed-by。

## 背景与问题
背景见 sched-20260827-007：CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值。系列经 v1–v5 演进，此前一直以 arm64 PCC 为主要验证路径。

## 技术方案
无方案变化。本日增量是验证范围的扩展：K Prateek 在 x86 共享内存 CPPC（non-PCC 传输）上又验证了一轮离线-上线周期，补充了此前缺失的跨架构测试覆盖。

## 版本演进与当前进展
- v5（09-16，`<20260916103820.1760297-1-sumitg@nvidia.com>`）：当前版本。
- 09-17：K Prateek Nayak 给出 Tested-by（x86 Zen3）；Sumit 确认将 Tested-by 加入系列、Reviewed-by 加入 patch 2。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak**：实测 x86 下 `auto_select`、`energy_performance_preference_val` 均正确保留，给出 Tested-by。
- **Sumit Gupta**（作者）：感谢并确认收取 Tested-by/Reviewed-by。
- 无分歧；系列进入合入前的标签收尾阶段。

## 合入评估
*likelihood=medium*。跨架构（arm64 + x86）实测均通过，系列已成熟；但当日未见 cpufreq 维护者（Viresh/Rafael）最终 Ack，合入仍待维护者拍板。*blocking_issues*：缺 cpufreq 维护者 Ack。*next_action*：作者附上新增标签后等待维护者收取。

## 效果评估
无性能数据；属电源管理寄存器保留的正确性验证。K Prateek 的测试为功能正确性，非性能收益。

## 我可以参与的点
- kind=testing：在其它共享内存 CPPC x86 平台或 arm64 PCC 平台上复测，扩展设备覆盖面（当前仅 Zen3）。

## 参考链接
- lore（v5 cover）: https://lore.kernel.org/all/20260916103820.1760297-1-sumitg@nvidia.com/
