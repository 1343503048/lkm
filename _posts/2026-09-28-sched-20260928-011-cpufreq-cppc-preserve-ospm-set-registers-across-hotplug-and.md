---
id: sched-20260928-011
date: '2026-09-28'
subject: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260916103820.1760297-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/e6ef3dd2-c2dc-4156-b5d5-35cad9c524f2@arm.com/
authors:
- Sumit Gupta
maintainers_involved:
- Rafael Wysocki
current_version: v5
patch_series:
- version: v5
  msgid: <20260916103820.1760297-1-sumitg@nvidia.com>
  date: '2026-09-16'
  summary: CPPC 热插拔/卸载保留 OSPM 寄存器；含 x86 实测 Tested-by（K Prateek）
  review_outcome: 09-28 Pierre Gondois 逐枚评审（结构简化/suspend 频率/逻辑归属）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - suspend 最低频率、save/restore 结构、逻辑归属等意见待回应
  - Rafael 未 Ack
  next_action: 作者回应 Pierre 意见、可能改出 v6
contribution_opportunities:
- kind: review
  description: 审阅 save/restore 表覆盖完整性及 suspend/hotplug 边界频率语义
- kind: testing
  description: 在其它 CPPC 平台复测寄存器保留，扩展设备覆盖
generated_at: '2026-09-29T01:00:00'
source_email_count: 3
related_articles:
- sched-20260926-009
- sched-20260917-006
- sched-20260827-007
tags:
- cpufreq
title: 'cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Sumit Gupta 的 CPPC 系列——在 CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值，避免离线-上线周期后电源管理配置失效。

- <a class="article-ref" href="/lkm/2026/08/27/sched-20260827-007-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260827-007</a>：系列经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-006-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260917-006</a>：v5 获 K Prateek Nayak 的 x86 实测 Tested-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-009-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260926-009</a>：Rafael Wysocki 催评审输入（「没有他人输入就不合入」）。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-011-cpufreq-cppc-preserve-ospm-set-registers-across-hotplug-and.html">sched-20260928-011</a>（今天）：Pierre Gondois 对 v5 三片补丁逐枚给出评审意见（save/restore 表结构简化、suspend 时是否请求最低频率、逻辑移入 `cppc_set_perf()` 等），系列从「有 Tested-by 但缺评审」进入「有实质评审」阶段。

## 背景与问题

（承接）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值，导致离线-上线周期后电源管理配置失效。今天背景无新增，症结是评审意见的收敛。

## 技术方案

（承接）把 OSPM 设置的寄存器（如 `auto_select`、`energy_performance_preference_val`）纳入 save/restore 表，跨 hotplug 与 unload 保留。今日无新代码，评审意见指向实现细节与边界语义。

## 版本演进与当前进展

*current_version: v5*（`<20260916103820.1760297-1-sumitg@nvidia.com>`）。09-28 Pierre Gondois 逐枚评审：1/4 建议把寄存器写入顺序相关逻辑移到 `cppc_set_perf()`（驱动不应关心寄存器写入顺序，且 `min_perf` 不变时是否会真的请求最低频率存疑）；3/4 建议用 `regs[CPPC_NR_SAVED_REGS][CPPC_SAVED_MAX]` 二维数组简化 save/restore；4/4 问「suspend 时是否也该请求最低频率」，并转述 sashiko 关于 fie 以 `policy->cpus` 初始化却以 `policy->related_cpus` 退出的疑点。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（维护者，前一日）：无他人输入则不合入（催评审）。
- **Pierre Gondois（Arm）**：就 save/restore 表结构、suspend 最低频率请求、逻辑归属给出多条意见，并引 CPPC spec（「Writes to this register only have meaning when Autonomous Selection is enabled」）讨论该寄存器写是否需被照管。
- 无 NAK；评审刚起步，方向未定。

## 合入评估

*likelihood=medium*。跨架构（arm64 + x86）实测已通过、系列成熟，今日又补上实质评审；但评审意见未收敛、Rafael 仍未 Ack。*blocking_issues*：suspend 最低频率、save/restore 结构、逻辑归属等意见待作者回应；Rafael 最终 Ack 未给。*next_action*：作者逐一回应 Pierre 意见、可能改出 v6，附已有 Tested-by 等维护者拍板。

## 效果评估

无性能数据；K Prateek 的 Tested-by 为功能正确性验证（`auto_select`、`energy_performance_preference_val` 在 offline-online 后正确保留），非性能收益。

## 我可以参与的点

- `review`：审阅 save/restore 表对 OSPM 寄存器的覆盖是否完整（是否还有其它 OSPM-set 寄存器漏掉），以及 suspend/hotplug 边界的频率请求语义。
- `testing`：在其它 CPPC 平台（共享内存 x86 或 arm64 PCC）复测寄存器保留，扩展设备覆盖面。

## 参考链接

- Pierre Gondois 对 1/4: https://lore.kernel.org/all/06075035-5cdd-4e88-ac80-2379f0db4fe9@arm.com/
- Pierre Gondois 对 4/4: https://lore.kernel.org/all/e6ef3dd2-c2dc-4156-b5d5-35cad9c524f2@arm.com/
- v5 封面: https://lore.kernel.org/all/20260916103820.1760297-1-sumitg@nvidia.com/
