# cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260827-007：Sumit Gupta 的 CPPC 系列（在 CPU 热插拔与驱动卸载时保留 OSPM 设置的寄存器值）经 v1–v5 演进，以 arm64 PCC 为主要验证路径。
- sched-20260917-006：v5 获得 K Prateek Nayak 的 x86 实测 Tested-by（Zen3 共享内存 CPPC，`auto_select` 与 `energy_performance_preference_val` 离线-上线后正确保留）。
- sched-20260926-009（今天）：cpufreq 维护者 Rafael Wysocki 催评审——"I need your input on this series. It is not going to be applied without any input from anyone."

## 背景与问题

（承接 sched-20260827-007）CPPC 驱动在 CPU 热插拔与驱动卸载时丢失 OSPM 设置的寄存器值，导致离线-上线周期后电源管理配置失效。今天背景无新增，症结是「有 Tested-by 但缺更广泛的评审输入」。

## 技术方案

（承接 sched-20260827-007）把 OSPM 设置的寄存器（如 `auto_select`、`energy_performance_preference_val`）纳入 save/restore 表，跨 hotplug 与 unload 保留。已验证 arm64 PCC 与 x86 共享内存两条传输路径。方案无变化。

## 版本演进与当前进展

- v5（2026-09-16，`<20260916103820.1760297-1-sumitg@nvidia.com>`）：当前版本。
- 09-17：K Prateek Nayak 给 x86 Tested-by；作者确认收取。
- 09-26：Rafael Wysocki（`<CAJZ5v0hXcRSj5ufpLTAgTSYtFDCXRQL3bJ5wNLtfRMrvHfo9ow@mail.gmail.com>`）催评审输入。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（cpufreq/ACPI 维护者）：明确「没有他人输入就不合入」，要求 CPPC cpufreq 驱动 reviewers 给出意见。他本人尚未 Ack。
- 延续前文：K Prateek Nayak 已给 x86 实测 Tested-by，无技术分歧。分歧不在方案而在参与度。

## 合入评估

*likelihood=medium*。跨架构（arm64 + x86）实测均已通过、系列成熟，但维护者仍要求更广泛的评审输入，未给 Ack。*blocking_issues*：缺 reviewer 意见、缺 Rafael 最终 Ack。*next_action*：CPPC cpufreq reviewers 补评审意见；作者附上已收取的 Tested-by 后等待维护者拍板。

## 效果评估

无性能数据；K Prateek 的测试为功能正确性验证（`auto_select`、`energy_performance_preference_val` 在 offline-online 后正确保留），非性能收益。

## 我可以参与的点

- `testing`：在其它 CPPC 平台（共享内存 x86 或 arm64 PCC）复测寄存器保留，扩展设备覆盖面。
- `review`：审阅 save/restore 表对 OSPM 寄存器的覆盖是否完整（是否还有其它 OSPM-set 寄存器漏掉）。

## 参考链接

- Rafael 催稿: https://lore.kernel.org/all/CAJZ5v0hXcRSj5ufpLTAgTSYtFDCXRQL3bJ5wNLtfRMrvHfo9ow@mail.gmail.com/
- v5 封面: https://lore.kernel.org/all/20260916103820.1760297-1-sumitg@nvidia.com/

---
id: sched-20260926-009
date: 2026-09-26
subject: "cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<CAJZ5v0hXcRSj5ufpLTAgTSYtFDCXRQL3bJ5wNLtfRMrvHfo9ow@mail.gmail.com>"
lore_url: "https://lore.kernel.org/all/CAJZ5v0hXcRSj5ufpLTAgTSYtFDCXRQL3bJ5wNLtfRMrvHfo9ow@mail.gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v5
generated_at: "2026-09-27T01:20:00"
authors:
  - "Sumit Gupta"
maintainers_involved:
  - "Rafael Wysocki"
patch_series:
  - version: v5
    msgid: "<20260916103820.1760297-1-sumitg@nvidia.com>"
    date: 2026-09-16
    summary: "CPPC 热插拔/卸载保留 OSPM 寄存器；含 x86 实测 Tested-by（K Prateek）"
    review_outcome: "09-26 Rafael 催评审输入，尚未 Ack"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "缺 reviewer 意见、缺 Rafael 最终 Ack"
  next_action: "CPPC cpufreq reviewers 补意见；作者附 Tested-by 后等维护者拍板"
contribution_opportunities:
  - kind: testing
    description: "在其它 CPPC 平台复测寄存器保留，扩展设备覆盖面"
  - kind: review
    description: "审阅 save/restore 表对 OSPM 寄存器的覆盖是否完整"
source_email_count: 1
related_articles:
  - "sched-20260917-006"
  - "sched-20260827-007"
tags:
  - cpufreq
---