# [GIT PULL] scheduler fixes

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261108-008：Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-11-08`），含六枚此前已过 review 的修复（dying deadline 任务 this_bw 缺账、I/O 等待独立记账、离开 fair 清 throttle、PELT 周期计数 u32 截断、cluster static-key 不平衡、alb_break_llc 忽略非 fair current）。当日缓存未见 Linus 合并回帖。
- sched-20261109-009（今天）：**pr-tracker-bot 确认该 pull 已合入 torvalds/linux.git**（commit `2ebb9de23bbd942b1a2431384e4a62908c31bb2a`）。同日 tip-bot 还推送了 5 枚 sched/urgent 修复与一批 sched/core 补丁进 tip 树。

## 背景与问题

（承接 sched-20261108-008）合入窗口期 Ingo 发 sched/urgent 修复 pull，收集六枚已在各自补丁系列过 review 的修复。今日结论：Linus 已收取该 pull（2026-11-08 10:14:16 +0100 发出 → 已 merge）。

## 技术方案

本轮无新代码，为合入确认。pr-tracker-bot 回帖正文：pull request 已并入 torvalds/linux.git，merge commit `2ebb9de23bbd942b1a2431384e4a62908c31bb2a`。此外当日 tip-bot2 邮件显示 tip/sched/urgent 又被 Ingo 推送 5 枚修复（deadline -EPERM、uclamp 拒绝超量 clamp、cpuset_mutex 二次解锁、cache fits_capacity、SMT siblings 未 join core），并推送了一批 sched/core 补丁（Aaron Tomlin 的 rq->rd __rcu/debug 加固、Peter 的 for_each_sched_entity 重构与 task_h_load 修复、steal_governor、idle_task_exit 清理、PREFERRED_CPU 解耦等）——这些是下一轮 sched/urgent 或 sched/core 的候选。

## 版本演进与当前进展

*current_version: null（GIT PULL 合入确认，无版本化补丁）*。当日进展：六修复 pull 被 Linus 合并（commit `2ebb9de23bbd`），status 从「已进 tip/sched/urgent」变为「已入 mainline」。

## Maintainer 意见与讨论焦点

无争议。Ingo 作为发起人汇总，六修复均已过 review；Linus 直接收取。无 NAK。

## 合入评估

*likelihood=merged*。六枚修复已合入 mainline（torvalds/linux.git commit `2ebb9de23bbd`）。*blocking_issues*：无。*next_action*：关注六修复各自的 stable 回合（视各补丁的 Cc/stable 标记）。

## 效果评估

无量化数据，属正确性修复集（this_bw/throttle/IO-wait 记账一致性、PELT 截断、cluster static-key、alb_break_llc 逻辑）。

## 我可以参与的点

- **review**：核对 OLK-6.6 等旧分支回合这六修复时对应代码路径是否同构（尤其 delayed dequeue 与 alb_break_llc 相关）。
- **testing**：在 v7.4 或 stable 上回归 PELT 周期计数、cluster 感知调度与 delayed dequeue 的 I/O 等待记账。

## 参考链接

- pr-tracker-bot 合并确认: https://lore.kernel.org/all/179416718186.1685596.17704035444438293464.pr-tracker-bot@kernel.org/
- 合入 commit: https://git.kernel.org/torvalds/c/2ebb9de23bbd942b1a2431384e4a62908c31bb2a

---
id: sched-20261109-009
date: '2026-11-09'
subject: "[GIT PULL] scheduler fixes"
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: "<179416718186.1685596.17704035444438293464.pr-tracker-bot@kernel.org>"
lore_url: "https://lore.kernel.org/all/179416718186.1685596.17704035444438293464.pr-tracker-bot@kernel.org/"
authors: [Ingo Molnar]
maintainers_involved: [Ingo Molnar]
current_version: null
patch_series: []
upstream_commit: "2ebb9de23bbd942b1a2431384e4a62908c31bb2a"
fixes_commit: null
merged_branch: "torvalds/linux.git"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "关注六修复各自的 stable 回合"
contribution_opportunities:
  - kind: review
    description: "核对 OLK-6.6 等旧分支回合六修复时代码路径是否同构"
  - kind: testing
    description: "在 v7.4/stable 上回归 PELT 计数、cluster 感知调度与 delayed dequeue 记账"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261108-008]
tags: [cfs, deadline, topology, load_balance]
---