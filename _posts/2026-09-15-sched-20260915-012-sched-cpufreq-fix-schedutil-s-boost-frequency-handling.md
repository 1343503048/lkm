---
id: sched-20260915-012
date: '2026-09-15'
subject: 'sched/cpufreq: fix schedutil''s boost frequency handling'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/2f7f671e-eace-4a6b-8a0b-20151f81d34d@arm.com/
authors:
- Ananthu C V
maintainers_involved:
- Dietmar Eggemann
current_version: v2
patch_series:
- version: v2
  msgid: <20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>
  date: '2026-09-08'
  summary: 见 sched-20260908-006
  review_outcome: Dietmar 认可并给出 ARM64 Juno 实测，仅一处 pressure 口径说明
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 102 vs 79 压力口径差异是否预期待作者确认
  next_action: 作者回应 pressure 口径说明后即可推进
contribution_opportunities:
- kind: discussion
  description: 分析 102 vs 79 的 pressure 口径差异是否符合 cpufreq_pressure 预期语义
- kind: testing
  description: 在其它大小核平台复现 boost 开关下的压力联动，验证补丁通用性
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20260908-006
tags:
- cpufreq
title: 'sched/cpufreq: fix schedutil''s boost frequency handling'
layout: article
---

## TL;DR
本文为增量更新（v2 全貌见 related_articles）。Dietmar Eggemann（Arm，sched 维护者）09-15 回复该 v2：认可方案（"IMHO, this makes sense"）及通过 `cpufreq_pressure`（policy->max）的协调，并在 ARM64 Juno R0 上给出实测数据；唯一小问题——boost 关闭后 cpu0/3-5 的 pressure 从 102 掉到 79（前一个含纯微架构差异、后者含微架构+最大频率差异，max_capacity 从 578 变 446），倾向认为这是预期的压力口径变化而非 bug。合入概率高。

## 背景与问题
承 sched-20260908-006：修 schedutil 打不到 boost 频率、以及 boost 关掉后频率上限回不来这两头问题。Dietmar 本日从「cpufreq 压力（policy->max）与 boost 的协调」这个角度做维护者评审验证。

## 技术方案
本日无新代码。Dietmar 的验证：在 ARM64 Juno R0（大小核，cpu_capacity 446/1024）上，关闭 boost 时 `cpufreq_update_pressure()` 报告的 policy->max 与 pressure（如 policy[0,3-5] max=700000 pressure=102）；开 boost 后两 policy pressure 均归 0；再关 boost 后恢复（pressure 280 / 102→79）。他确认压力随 boost 开关正确联动，仅标注 102 vs 79 的差异为其「唯一小问题」。

## 版本演进与当前进展
v2（09-08，见 related_articles）本日获 Dietmar 评测，无新版本。作者尚未就 102 vs 79 的差异回复。

## Maintainer 意见与讨论焦点
- **Dietmar Eggemann**：认可方案与 cpufreq_pressure 协调方式；实测数据给出压力随 boost 正确联动；指出 102（纯 uarch 差异，max_capacity=578）vs 79（uarch+最大频率差异，max_capacity=446）的压力差异，认为这是口径变化、非缺陷。
- 无 NAK；唯一待澄清点是作者是否认同 102→79 属预期行为。

## 合入评估
likelihood=high。维护者方向性认可、实测数据支持，仅一处压力口径的轻微说明。blocking_issues：102 vs 79 压力差异是否「预期」待作者确认（Dietmar 已倾向预期行为）。next_action：作者回应 pressure 口径说明后即可推进。

## 效果评估
Dietmar 实测（ARM64 Juno R0）：boost=0 时 policy[0,3-5] max=700000/pressure=102、policy[1-2] max=800000/pressure=280；切 boost=1 后两 policy pressure 均 0；再切 boost=0 后恢复 pressure=280 / 79。关键验证点是压力随 boost 开关正确联动（尤其大核从 102 修正为 79 的 uarch+频率差异口径）。这是维护者实测数据，非作者自报。

## 我可以参与的点
- kind=discussion：就「102 vs 79」的 pressure 口径差异（纯 uarch vs uarch+boost 频率）做分析，确认其是否符合 `cpufreq_pressure` 的预期语义。
- kind=testing：在其它大小核平台（如 big.LITTLE/DynamIQ）复现 boost 开关下的压力联动，验证补丁的通用性。

## 参考链接
- Dietmar Eggemann 回帖：https://lore.kernel.org/all/2f7f671e-eace-4a6b-8a0b-20151f81d34d@arm.com/
- v2 cover：https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/
