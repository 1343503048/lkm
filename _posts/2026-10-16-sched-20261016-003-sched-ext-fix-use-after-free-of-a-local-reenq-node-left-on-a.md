---
id: sched-20261016-003
date: 2026-10-16
subject: 'sched_ext: Fix use-after-free of a local reenq node left on an inactive
  cpu'
subsystem: sched
type: bug
status: merged_tip
severity: high
thread_root_msgid: <20261015171628.714661316-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261015171628.714661316-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261015171628.714661316-1-tj@kernel.org>
  date: 2026-10-15
  summary: schedule_dsq_reenq() 忽略 inactive CPU local DSQ 的 reenq
  review_outcome: Andrea Righi Reviewed-by + Tested-by；Tejun 应用于 for-7.3-fixes
upstream_commit: null
fixes_commit: 238eba8c210d
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched_ext fixes 进入 v7.3
contribution_opportunities: []
generated_at: '2026-10-17T01:30:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- crash
title: 'sched_ext: Fix use-after-free of a local reenq node left on an inactive cpu'
layout: article
---

## TL;DR
Tejun Heo 修复 sched_ext 的 use-after-free：一个 local DSQ 的 reenq 节点若被请求时目标 CPU 已经（或即将）下线，节点会一直挂在 rq 链表上，scheduler 释放时带着仍在链表里的节点走 RCU free 路径并告警，CPU 回来后又会被重新遍历。补丁直接忽略对 inactive CPU local DSQ 的 reenq。Andrea Righi 以 AI 生成的 reproducer 在 virtme-ng 里验证通过并给 Reviewed-by + Tested-by，已合入 `sched_ext/for-7.3-fixes`。

## 背景与问题
local DSQ reenq 通过 per-sched 节点挂在 rq 上、由 deferred work 执行。两条路径会留下悬挂节点：

- CPU 下线时，teardown 早期就安装 balance push，此后 `queue_balance_callback()` 拒绝新回调；但 `ops.dispatch()` 在该 CPU 上还要跑到 rq 过完 RCU grace period 才 offline，这窗口里请求的 reenq 可能永不执行。`dispatch_one()` 里的 IMMED 处理也以同样方式请求。
- 从别处对已 offline 的 CPU 请求 reenq 走 `irq_work_queue_on()`，会告警且 work 直到 CPU 回来才执行。

无论哪种，节点都留在 rq 链表上，`scx_sched_free_rcu_work()` 释放 scheduler 时告警并 free 掉仍带节点的 pcpu，CPU 回来后又遍历到该链表。作者认为 inactive CPU 的 local DSQ 只装绑定在它上面、或正被移走的任务，reenq 无意义，故直接忽略。

## 技术方案
单补丁（`kernel/sched/ext/ext.c`，+14/−1）：在 `schedule_dsq_reenq()` 里对 local DSQ 增加 inactive 检查，inactive 时直接忽略 reenq。该检查 lockless：下线的 hotplug 线程先把自己标 inactive、再装 balance push，而 dispatch 跑完才会让该线程在本 CPU 上运行，所以看到 active 的 dispatch 早已把回调入队；grace period 等待任何看到 active 的请求者，保证 irq_work 在 CPU online 时入队。

## 版本演进与当前进展
v1（<20261015171628.714661316-1-tj@kernel.org>）发出后：Andrea Righi 附上一个新的 selftest `reenq_offline`（`tools/testing/selftests/sched_ext/`）并给 `Reviewed-by` + `Tested-by`；Tejun 回「Applied to sched_ext/for-7.3-fixes」。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者）亲自提交并应用；Andrea Righi（sched_ext reviewer）给 Reviewed-by + Tested-by。无分歧。

## 合入评估
*likelihood=merged*。已由 Tejun 应用到 `sched_ext/for-7.3-fixes` 分支。*blocking_issues*：无。*next_action*：随 sched_ext fixes 进入 v7.3。

## 效果评估
Andrea 用 AI 生成的 reproducer 在 virtme-ng 验证通过（并新增 `reenq_offline` selftest 固化回归）。补丁带两处 `Fixes:`（`238eba8c210d`、`76edc2761ab8`）与 `Cc: stable@vger.kernel.org # v7.1+`。

## 我可以参与的点
当前阶段已合入 fixes 分支，无明显参与空间；可持续观察是否进入 v7.3 与后续 stable 回合。

## 参考链接
- patch：https://lore.kernel.org/all/20261015171628.714661316-1-tj@kernel.org/
- Andrea 的 R-B/T-B：https://lore.kernel.org/all/atERmiNFIgyR2ykL@gpd4/
- Tejun 的 applied 回帖：https://lore.kernel.org/all/fe04ef6d5162a7c40e2a7cb1581167f3@kernel.org/
