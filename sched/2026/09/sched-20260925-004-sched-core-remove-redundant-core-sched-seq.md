# sched/core: Remove redundant core_sched_seq

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 sched-20260916-020。Hui Su 的「删除冗余 core_sched_seq、用 core_pick 直接作 pending 标记」清理已被 Peter Zijlstra 合入 tip/sched/core（commit fbbc63fed0b09c8c5cf3972db8922ae98406ceec，09-25 12:45:58 +0200）。

## 背景与问题

core scheduling（超线程隔离）中，`core_sched_seq` 记录「一个 rq 是否已经消费了上一轮 core-wide 选择的 pick」。但 `rq->core_pick` 已经承载了同一份 per-rq 状态：core-wide 选择之后，`core_pick` 只对仍需消费 pick 的 sibling 保持非空，当前 CPU 消费、sibling 已在跑选中任务、或通过 fastpath 消费 pending pick 时被清空，CPU offline 路径也会清空。`core_task_seq` 与 `core_pick_seq` 各有其责（前者随任务集变化和每轮 core-wide pick 递增，后者记录做出选择时的任务序列），两者相等即证明 pending 的 core_pick 仍有效。因此 `core_sched_seq` 是对 pending/consumed 状态的重复记录，可删。

## 技术方案

删除 `core_sched_seq`，直接用 `core_pick` 作为 pending 标记；在 `core_pick_seq == core_task_seq` 时，非空 `core_pick` 即表示该 rq 还有 pick 待消费。合入版本涉及 kernel/sched/core.c 等 core scheduling 路径的清理。

## 版本演进与当前进展

- v1（2026-09-15，`<20260915163138.2973969-1-sh_def@163.com>`）：删除 core_sched_seq、用 core_pick 直接作 pending 标记；提交说明附带了 core scheduling 的一致性测试。
- 09-25：Peter 合入 tip/sched/core（Commit-ID fbbc63fed0b09c8c5cf3972db8922ae98406ceec）。

## Maintainer 意见与讨论焦点

Peter Zijlstra 作为 committer 直接收取 v1，本日无新讨论、无分歧、无 NAK。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit fbbc63fed0b09c8c5cf3972db8922ae98406ceec。纯冗余状态删除，语义由 `core_pick`/`core_pick_seq` 等价覆盖，无阻塞项。

## 效果评估

无运行时 benchmark；清理属静态可证的等价变换（状态去重）。暂无效果数据。

## 我可以参与的点

修复已合入，当前阶段暂无明显参与空间。core scheduling 路径在自家分支回合时需确认 `core_pick_seq`/`core_task_seq` 的等价不变量一并成立（*review*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033365058.2819794.4873909017186114311.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/fbbc63fed0b09c8c5cf3972db8922ae98406ceec
- v1 补丁: https://lore.kernel.org/all/20260915163138.2973969-1-sh_def@163.com/

---
id: sched-20260925-004
date: 2026-09-25
subject: "sched/core: Remove redundant core_sched_seq"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<179033365058.2819794.4873909017186114311.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179033365058.2819794.4873909017186114311.tip-bot2@tip-bot2/"
upstream_commit: "fbbc63fed0b09c8c5cf3972db8922ae98406ceec"
fixes_commit: null
merged_branch: "tip/sched/core"
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Hui Su"
maintainers_involved:
  - "Peter Zijlstra"
patch_series:
  - version: v1
    msgid: "<20260915163138.2973969-1-sh_def@163.com>"
    date: 2026-09-15
    summary: "删除冗余的 core_sched_seq，用 core_pick 直接作 pending 标记"
    review_outcome: "09-25 Peter 合入 tip/sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 tip/sched/core，等待进入合并窗口"
contribution_opportunities:
  - kind: review
    description: "自家分支回合时需确认 core_pick_seq/core_task_seq 等价不变量一并成立"
source_email_count: 1
related_articles:
  - "sched-20260916-020"
tags:
  - core_sched
---