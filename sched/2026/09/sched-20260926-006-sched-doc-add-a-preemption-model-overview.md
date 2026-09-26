# sched/doc: add a preemption model overview

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260920-003：Quchaosheng 提交文档补丁 1/2——新增 `Documentation/scheduler/sched-preemption.rst`，系统介绍内核四种抢占模型（none/voluntary/full/lazy）及运行时选择方式，并澄清最易误解的 PREEMPT_LAZY。
- sched-20260922-016：v2——按 Sebastian Siewior 意见重写为「围绕调度请求」的鸟瞰视角，删错误测量段与 yield 措辞。
- sched-20260923-010：v3/v4——把「such a call」明确写为 `cond_resched()`、保留 Sebastian 的 Reviewed-by。
- sched-20260926-006（今天）：Jonathan Corbet 应用了两枚补丁，并请作者补发一个带合适 SPDX 行的 followup（给新建的 `sched-preemption.rst`）。

## 背景与问题

（承接 sched-20260920-003）现有调度文档只讲各调度类和调优旋钮，没有一处系统描述「抢占模型」本身；唯一提及 `preempt=` 的位置只解释启动参数、不解释其选中的模型。系列补上这块空缺。今天背景无新增。

## 技术方案

（承接 sched-20260922-016）新增 `Documentation/scheduler/sched-preemption.rst`，以「wakeup → 决定谁让出 CPU → 置 TIF_NEED_RESCHED[LAZY] → 抢占模型决定在哪兑现」为主线。今天方案无变化，仅进入合入与 SPDX 收尾。

## 版本演进与当前进展

- v1 → v2 → v3 → v4（09-23，diff 无变化的二次发送）。
- 09-26：Jonathan Corbet（`<87v77s2f02.fsf@trenco.lwn.net>`）回复 "I have applied these two patches. However: can you please send a followup with a suitable SPDX line for your new sched-preemption.rst file?"

## Maintainer 意见与讨论焦点

- **Jonathan Corbet**（docs 维护者）：直接应用两枚补丁，唯一遗留动作是请作者为新建 rst 补 SPDX 行（GPL/CC-BY 等许可标识）。无 NAK。
- 延续前文：Sebastian Siewior 此前给出 Reviewed-by 并建议合入。

## 合入评估

已应用进 Jonathan Corbet 的 docs 树（*likelihood=merged*），commit hash 未在邮件中给出。*blocking_issues*：仅剩 SPDX 行 followup（不影响已应用状态，属规范化收尾）。*next_action*：作者补发带 SPDX 行的 followup。

## 效果评估

文档类补丁，无运行时/benchmark 数据；效果体现在调度文档对抢占模型的覆盖完整性上。

## 我可以参与的点

- `new_patch`：代作者补发带 SPDX 行（如 `SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later`，或按内核文档惯例的 GPL-2.0）的 followup 补丁——这是 Corbet 明确提出的、且作者尚未回应的最小收尾动作。

## 参考链接

- Corbet 应用回帖: https://lore.kernel.org/all/87v77s2f02.fsf@trenco.lwn.net/
- 系列（v2 1/2）: https://lore.kernel.org/all/20260922083101.99685-1-quchaosheng000406@163.com/

---
id: sched-20260926-006
date: 2026-09-26
subject: "sched/doc: add a preemption model overview"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<87v77s2f02.fsf@trenco.lwn.net>"
lore_url: "https://lore.kernel.org/all/87v77s2f02.fsf@trenco.lwn.net/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v4
generated_at: "2026-09-27T01:20:00"
authors:
  - "Quchaosheng"
maintainers_involved:
  - "Jonathan Corbet"
patch_series:
  - version: v4
    msgid: "<20260922083101.99685-1-quchaosheng000406@163.com>"
    date: 2026-09-22
    summary: "sched-preemption.rst 抢占模型概述；已按 Sebastian 意见收敛"
    review_outcome: "09-26 Jonathan Corbet 应用，仅请作者补 SPDX 行 followup"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "作者补发带 SPDX 行的 followup"
contribution_opportunities:
  - kind: new_patch
    description: "补发带 SPDX 行的 followup 补丁（Corbet 明确要求的收尾动作）"
source_email_count: 1
related_articles:
  - "sched-20260923-010"
  - "sched-20260922-016"
  - "sched-20260920-003"
tags:
  - preempt
---