# sched/idle: Stop the tick when no cpuidle driver is available

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20260729-003 / sched-20261106-018：Christian Loehle 的单行修复恢复「无 cpuidle driver 时无条件停 tick」，修 `f4c31b07b136`（"sched: idle: Consolidate the handling of two special cases"）的回归——此前 Oracle 报告 OCI 小规格 VM 上 sysbench 回退最多 -29%，Broadcom 的 Florian Fainelli 也确认该回归经 stable backport 扩散到 ARM 32 位裸金属平台，并补上 Tested-by。
- sched-20261111-023（今天）：**Thorsten Leemhuis（回归跟踪）补一行线索**——「顺带一提，针对上述 commit 的修复最近进了 mainline，不知是否会改变现状：`96a494c9cfd8f4`（"sched/cputime: Don't account idle time twice after dyntick-idle"）[v7.4-rc1]」，提示一个刚合入的 cputime 修复可能与仍在追踪的问题相关。

## 背景与问题

（承接 sched-20260729-003 / 20261106-018）`f4c31b07b136` 把「无 cpuidle driver」特殊路径并进 tick 唤醒启发式，导致此类系统每个 idle episode 开头都留着周期 tick。Christian Loehle 的单行修复恢复无条件停 tick，已有 Oracle/Broadcom 两家确认影响面。今日 Thorsten 引入新线索：`96a494c9cfd8f4`（修「dyntick-idle 后 idle time 被重复记账」的 cputime 问题）刚进 v7.4-rc1，可能与线程中仍在讨论的现象相关。

## 技术方案

（承接，无变化）Christian Loehle 的单行修复：在无 cpuidle driver 的路径恢复无条件停 tick。今日无新补丁，仅 Thorsten 补充一条「可能相关的已合入修复」线索。

## 版本演进与当前进展

*current_version: v1（Christian Loehle 单行修复）*。今日回归跟踪方补充线索，无新版本。

## Maintainer 意见与讨论焦点

- **Thorsten Leemhuis（回归跟踪维护者）**：提示 `96a494c9cfd8f4`（cputime 重复记账修复，v7.4-rc1）可能与线程仍在讨论的现象相关，询问是否会改变现状。
- 无 NAK。原「stop tick」修复本身方向无异议、Tested-by 已累积。

## 合入评估

*likelihood=high*（针对原「stop tick」单行修复）。修复方向无异议、Tested-by 已累积、且已进 stable 相关跟踪队列。*blocking_issues*：无实质阻塞；`96a494c9cfd8f4` 是否与残余现象相关待确认。*next_action*：确认 `96a494c9cfd8f4` 合入后原现象是否彻底消除；原单行修复按既有路径继续推进。

## 效果评估

（承接）Oracle 曾报告 sysbench 回退最多 -29%，修复后恢复；Florian 在 ARM 32 位 WFI-only 平台的网络吞吐测试亦确认影响。今日无新增数据。

## 我可以参与的点

- **testing**：在无 cpuidle driver 的平台（含 v7.4-rc1 已合 `96a494c9cfd8f4`）复测，确认 tick 不再残留且 cputime 记账不重复。

## 参考链接

- lore thread: https://lore.kernel.org/all/096b42fa-107f-450d-b3b1-03bcad3f1e04@oracle.com/
- Thorsten 的线索: https://lore.kernel.org/all/c92bf044-3a04-4fd7-b1a3-e7ea89cf1e4c@leemhuis.info/

---
id: sched-20261111-023
date: '2026-11-11'
subject: "sched/idle: Stop the tick when no cpuidle driver is available"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<096b42fa-107f-450d-b3b1-03bcad3f1e04@oracle.com>"
lore_url: "https://lore.kernel.org/all/096b42fa-107f-450d-b3b1-03bcad3f1e04@oracle.com/"
authors: [Christian Loehle]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<096b42fa-107f-450d-b3b1-03bcad3f1e04@oracle.com>"
    date: '2026-07-29'
    summary: "无 cpuidle driver 时恢复无条件停 tick"
    review_outcome: "Thorsten 补充 96a494c9cfd8f4 线索，需确认残余现象是否消除"
upstream_commit: null
fixes_commit: "f4c31b07b136"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "确认 96a494c9cfd8f4 合入后残余现象是否消除；单行修复继续推进"
contribution_opportunities:
  - kind: testing
    description: "在无 cpuidle driver 平台（含已合 96a494c9cfd8f4 的内核）复测 tick 与 cputime 记账"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20260729-003, sched-20261106-018]
tags: [idle, nohz]
---