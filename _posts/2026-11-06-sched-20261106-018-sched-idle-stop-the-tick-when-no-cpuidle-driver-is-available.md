---
id: sched-20261106-018
date: 2026-11-06
subject: 'sched/idle: Stop the tick when no cpuidle driver is available'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <097f4855-eca1-414a-932c-107d9eee5088@broadcom.com>
lore_url: https://lore.kernel.org/all/097f4855-eca1-414a-932c-107d9eee5088@broadcom.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: null
  date: 2026-07-29
  summary: 无 cpuidle driver 路径恢复无条件停 tick。
  review_outcome: Zhan Xusheng 机理分析、Rafael 参与；今日 Florian 补 Tested-by。
upstream_commit: null
fixes_commit: f4c31b07b136
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者收取并评估 stable 回合策略
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20260729-003
tags:
- idle
- nohz
title: 'sched/idle: Stop the tick when no cpuidle driver is available'
layout: article
---

## TL;DR

Florian Fainelli（Broadcom）为 Christian Loehle 的「无 cpuidle driver 时停止 tick」单行修复补上 Tested-by：该修复被 backport 进 stable（5.15、6.1 等）后，Broadcom 在 ARM 32 位平台（无 ARM_CPUIDLE/ARM_PSCI_CPUIDLE、只有 WFI idle）的网络吞吐测试中撞上了同一问题，确认了影响面——这是继 Oracle 之后第二家报告此回归的厂商，且把范围从虚拟化扩展到了裸金属小平台。此修复（修 f4c31b07b136 的回归）已有 Tested-by 累积，方向无异议。

## 背景与问题

commit `f4c31b07b136`（"sched: idle: Consolidate the handling of two special cases"）把「无 cpuidle driver」的特殊路径并进了 tick 唤醒启发式，导致无 cpuidle driver 的系统每个 idle episode 开头都留着周期 tick。此前 Oracle 的 Joseph Salisbury 报告 OCI 小规格 VM 上 sysbench 回退最多 -29%，Christian Loehle 发出单行修复恢复无条件停 tick。Florian 今天确认：该回归经 stable backport 扩散到了非虚拟化场景——ARM 32 位、仅 WFI 作 idle state 的平台上，网络吞吐测试可见同样问题（平台没开 ARM_CPUIDLE/ARM_PSCI_CPUIDLE，本身只有 WFI）。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/07/29/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.html">sched-20260729-003</a>）Christian Loehle 的单行修复：在无 cpuidle driver 的路径恢复无条件停 tick。Florian 补 Tested-by，未改方案。

## 版本演进与当前进展

*current_version: v1（2026-07-29 首次分析）*。今日 Florian Fainelli 补 Tested-by 并报告 stable backport 后的真实命中，无新代码版本。

## Maintainer 意见与讨论焦点

Florian Fainelli（Broadcom 资深内核贡献者）给出 Tested-by，并指出「不只我们一家受影响」。此前（7 月）Rafael J. Wysocki 参与讨论、Zhan Xusheng 给出机理分析。无 NAK，方向持续获得背书。

## 合入评估

*likelihood=high*。单行修复、机理清楚、多厂商 Tested-by 累积（Oracle 场景 + Broadcom ARM 场景），仅差收取。*blocking_issues*：无显著阻塞。*next_action*：维护者收取该单行修复并评估 stable 回合策略（问题已因 backport 扩散到 stable）。

## 效果评估

7 月 Oracle 报告 sysbench threads 回退最多 -29%、revert 后恢复；今日 Florian 报告 ARM 32 位平台网络吞吐测试同样命中。修复效果为恢复无条件停 tick，未见修复后的正向量化数据（两处均为「撞上问题」的报告）。

## 我可以参与的点

当前阶段暂无明显参与空间：修复成熟、Tested-by 累积，可持续观察其合入与 stable 回合。

## 参考链接

- lore thread（今日回帖）: https://lore.kernel.org/all/097f4855-eca1-414a-932c-107d9eee5088@broadcom.com/
- 历史文章: <a class="article-ref" href="/lkm/2026/07/29/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.html">sched-20260729-003</a>（见 sched/2026/07/ 归档）
