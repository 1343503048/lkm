# ACPI / cpufreq: CPPC: Add ospm_nominal_perf support

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是 Sumit Gupta 的 v7 三片 CPPC 系列——新增 OSPM nominal perf 支持，把 OS 电源管理设定的标称性能如实反映到 cpufreq 的 boost 与频率上限。

- sched-20260808-004：v7 三片发出（ACPI 寄存器 + cpufreq `ospm_nominal_freq` sysfs + policy 反映）。
- sched-20260926-008：cpufreq 维护者 Rafael Wysocki 主动催稿——近 7 周无人评审、无人评论则不合入。
- sched-20260928-010（今天）：催稿生效，Pierre Gondois 与 Christian Loehle 分别就 v7 给出评审意见（`ospm_nominal_freq` 接口形态、初值设置时机、rebase 建议等），系列从「零评审」进入「有实质意见」阶段。

## 背景与问题

（承接）CPPC 允许 OS 直接写性能寄存器设定目标。本系列新增对 OSPM nominal perf 寄存器的支持，使 OS 设定的标称性能能被如实反映到 cpufreq policy 的 boost 与频率上限，避免两者脱节。今天背景无新增，症结从「缺人评审」转为「评审意见的收敛」。

## 技术方案

（承接）三片：patch 1（ACPI）加 `ospm_nominal_perf` 寄存器支持；patch 2（cpufreq）新增 `ospm_nominal_freq` sysfs 属性（kHz，write-only，软件侧跟踪）；patch 3（cpufreq）把 OSPM nominal 反映到 policy 的 boost 与 limits。今日无新代码，评审意见指向接口形态与实现细节。

## 版本演进与当前进展

*current_version: v7*（`<20260807214837.863209-1-sumitg@nvidia.com>`）。09-26 Rafael 催稿后，09-28 出现实质评审：Christian Loehle 认为 `ospm_nominal_freq` 做成 write-only 接口别扭（建议返回 `-EOPNOTSUPP`/requested_val/未设置值）；Pierre Gondois 问「是否应在 init 时设一次后不再更新」，并建议 rebase 到 Christian Loehle 的另一系列之上。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（维护者，前一日）：明确无人评论则不合入（催稿门槛）。
- **Christian Loehle（Arm）**：质疑 `ospm_nominal_freq` write-only 接口形态。
- **Pierre Gondois（Arm）**：就初值设置时机、跨系列 rebase 提意见；表示「两个 patchset 都是小意见，不算多」。
- 无 NAK；评审刚起步，方向未定。

## 合入评估

*likelihood=medium*。相较 09-26 的「零评审」，今日已有两位 reviewer 给出意见，blocking_issue 部分解除；但意见尚未收敛、Rafael 仍未亲自 Ack。*blocking_issues*：接口形态（write-only vs 可读）与初值时机未定；需作者按评审改版并 rebase；Rafael 最终 Ack 未给。*next_action*：作者回应 Christian/Pierre 意见、改出 v8（或先澄清接口取舍），并处理 rebase。

## 效果评估

无性能数据；属电源管理寄存器语义一致性改进，正确性验证仍在补齐。

## 我可以参与的点

- `review`：就 `ospm_nominal_freq` 的接口设计（write-only 是否合适、是否应 init 后只读）给出判断，帮助收敛 Christian 与作者的取舍。
- `testing`：在 arm64 PCC 或 x86 共享内存 CPPC 平台上验证 OSPM nominal 写入后 boost/limits 的一致性。

## 参考链接

- Pierre Gondois 总评: https://lore.kernel.org/all/3a3e5dc5-9d1b-4bdf-a0a9-99eaea783f92@arm.com/
- Christian Loehle 接口意见: https://lore.kernel.org/all/e539dce2-1b2a-45cc-9ea8-1ab0e0f11972@arm.com/
- v7 封面: https://lore.kernel.org/all/20260807214837.863209-1-sumitg@nvidia.com/

---
id: sched-20260928-010
date: '2026-09-28'
subject: 'ACPI / cpufreq: CPPC: Add ospm_nominal_perf support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260807214837.863209-1-sumitg@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/3a3e5dc5-9d1b-4bdf-a0a9-99eaea783f92@arm.com/'
authors:
  - 'Sumit Gupta'
maintainers_involved:
  - 'Rafael Wysocki'
current_version: v7
patch_series:
  - version: v7
    msgid: '<20260807214837.863209-1-sumitg@nvidia.com>'
    date: '2026-08-07'
    summary: 'OSPM nominal perf 支持：ACPI 寄存器 + cpufreq ospm_nominal_freq sysfs + policy 反映'
    review_outcome: '09-28 Christian/Pierre 给出接口形态与初值时机评审意见'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '接口形态（write-only vs 可读）与初值时机未定'
    - '需按评审改版并 rebase；Rafael 未 Ack'
  next_action: '作者回应 Christian/Pierre 意见并改出 v8'
contribution_opportunities:
  - kind: review
    description: '就 ospm_nominal_freq 接口设计（write-only 是否合适）给出判断'
  - kind: testing
    description: '在 CPPC 平台验证 OSPM nominal 写入后 boost/limits 一致性'
generated_at: '2026-09-29T01:00:00'
source_email_count: 3
related_articles:
  - sched-20260926-008
  - sched-20260808-004
tags:
  - cpufreq
---