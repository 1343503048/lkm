# sched/deadline: Fix assorted dl_bw accounting bugs

## TL;DR

Juri Lelli 的 4 补丁系列修复多个 SCHED_DEADLINE 带宽记账 bug（total_bw 泄漏/下溢最终导致新 DL 准入与 CPU offline 报 -EBUSY），当日即由 Ingo Molnar 全数合入 tip/sched/urgent，收到 4 封 tip-bot2 通知。

## 背景与问题

SCHED_DEADLINE 的 dl_bw/total_bw 记账有多个边界缺陷，反复触发会把 total_bw 污染到 admission cap，之后 `sched_setattr(SCHED_DEADLINE)` 与 CPU offline 都报 -EBUSY。系列回应两个独立报告：Weiheng Qiu（cpuset 迁移 stale root domain、zombie 任务）与 Tejun Heo（non-queued 切出泄漏）。

四个问题：1) sleeping 任务在 cpuset 分区间迁移时 `task_rq(p)->rd` 过期，导致带宽转移被错误跳过；2) non-queued 任务切出 SCHED_DEADLINE 时 `switched_from_dl()` 只对 queued 任务走 `task_non_contending()`、对 non-queued 只减 running_bw/rq_bw 从不释放 total_bw；3) `SCHED_FLAG_KEEP_PARAMS` 叠加换类请求自相矛盾，`DEQUEUE_CLASS` 触发虚假 `switched_from_dl()` 导致记账下溢；4) 对已退出（zombie）任务 `setattr(SCHED_DEADLINE)` 能成功收 total_bw 却永不释放。

## 技术方案

逐条修复：patch 1 引入 `dl_task_root_domain_cpu()`，用任务的 `cpus_mask`（调用时仍反映旧源 cpuset）而非过期的 `task_rq(p)->rd` 定位带宽实际记账所在的 root domain；patch 2 在 `switched_from_dl()` 中，当任务 non-queued 且无 pending inactive timer（`dl_non_contending` 未置位）时直接释放 total_bw；patch 3 在 `prev_class != next_class` 且带 `SCHED_FLAG_KEEP_PARAMS` 时提前 `-EINVAL`；patch 4 对 `dl_policy(policy) && p->exit_state` 提前 `-ESRCH`。改动跨 `kernel/sched/deadline.c` 与 `syscalls.c`（+53/−15 行量级）。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103-b4-sched-dl-bw-fixes-v1-0-dd761fe005b4@redhat.com）*。当日即被 Ingo Molnar 收取并入 tip/sched/urgent，4 封 tip-bot2 通知同日发出。

## Maintainer 意见与讨论焦点

无分歧。系列是 Juri Lelli（SCHED_DEADLINE 维护者）本人为回应报告而写；Tejun Heo 测试后回 `Tested-by`（"On 473adf013e43, all three are fixed"），Ingo Molnar 当日收取并合入。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，无阻塞项。4 个 tip commit：`a2b67e904401`（Reject SCHED_DEADLINE on exited tasks）、`8a70415351ba`（Reject KEEP_PARAMS when it would change class）、`41a7968022ca`（total_bw leak when switching away while !queued）、`b4a61fdc19c5`（stale root domain in cpuset bandwidth transfer）。命中多个历史 commit（`Fixes: 209a0cbda7a0`、`a509a7cd7974`），属 urgent 修复，预期后续走 stable 回合。

## 效果评估

无性能数据；纯正确性修复。修复前反复触发会使 total_bw 堆满 admission cap，`sched_setattr` 与 CPU offline 报 -EBUSY；Tejun 实测三 case 均已被修复。

## 我可以参与的点

已合入，暂无直接参与空间；可关注这些 `Fixes:` 引入的记账缺陷在长期维护分支上的 stable backport 情况。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103-b4-sched-dl-bw-fixes-v1-0-dd761fe005b4@redhat.com/
- tip commit（patch 1）: https://git.kernel.org/tip/b4a61fdc19c5c40f295b28ad318a3c4827d7d289

---
id: sched-20261103-001
date: 2026-11-03
subject: "sched/deadline: Fix assorted dl_bw accounting bugs"
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: "<20261103-b4-sched-dl-bw-fixes-v1-0-dd761fe005b4@redhat.com>"
lore_url: "https://lore.kernel.org/all/20261103-b4-sched-dl-bw-fixes-v1-0-dd761fe005b4@redhat.com/"
authors: [Juri Lelli]
maintainers_involved: [Ingo Molnar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103-b4-sched-dl-bw-fixes-v1-0-dd761fe005b4@redhat.com>"
    date: 2026-11-03
    summary: "4 补丁修复 dl_bw/total_bw 记账：stale root domain、!queued 切出泄漏、KEEP_PARAMS 换类、zombie 准入。"
    review_outcome: "Tejun Tested-by；Ingo 当日合入 tip/sched/urgent。"
upstream_commit: null
fixes_commit: "209a0cbda7a0"
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入；关注 stable 回合。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 9
related_articles: []
tags: [deadline, cgroup]
---