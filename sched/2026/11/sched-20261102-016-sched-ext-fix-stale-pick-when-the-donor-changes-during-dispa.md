# sched_ext: Fix stale pick when the donor changes during dispatch

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261101-002：修 sched_ext dispatch 中 `rq->donor` 被并发改写仍用旧 `@prev` 的 stale pick；v4 已获 Andrea Righi Reviewed-by（for-7.4-fixes，Cc stable v6.12+）。
- sched-20261102（今天）：Tejun Heo 宣布**已收取**进 `sched_ext/for-7.4-fixes`，并补 `Reviewed-by: Andrea Righi`；同时宣告 `ops.cpu_acquire()`/`ops.cpu_release()` 彻底废弃（「never worked completely and won't」），要求 scx repo 里的调度器移除其用法。

## 背景与问题

（承接）dispatch drop lock 期间其它 CPU 经 `proxy_needs_return()`/`sched_proxy_block_task()` 重置 donor，导致本 CPU 运行一个已排队到别处 rq 的任务。

## 技术方案

（承接）`scx_dsp_prev_stale()` 检测 + `dispatch_one()`/`scx_dispatch_sched()` 重启 pick。今日无代码变化，仅维护者收取 + 邻接 API 废弃宣告。

## 版本演进与当前进展

v4 已合入 sched_ext/for-7.4-fixes；`ops.cpu_acquire/cpu_release` 同步标记废弃。

## Maintainer 意见与讨论焦点

Tejun（维护者）：apply + 补 RB；明确 cpu_acquire/cpu_release 废弃——这是除了本补丁之外的社区行动项（scx 用户空间调度器需删用法）。

## 合入评估

likelihood=merged（已进 sched_ext/for-7.4-fixes，随后续 pull 进主线）。

## 效果评估

（承接）正确性修复，无独立性能数据。

## 我可以参与的点

- new_patch：清理 scx repo 里调度器对 `ops.cpu_acquire/cpu_release` 的用法（已废弃）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261031162803.541236-1-tj@kernel.org/

---
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261031162803.541236-1-tj@kernel.org>
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v4
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched_ext for-7.4-fixes 后续 pull 进主线
contribution_opportunities:
- kind: new_patch
  description: 清理 scx repo 调度器对已废弃 ops.cpu_acquire/cpu_release 的用法
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
source_email_count: 1
related_articles:
- sched-20261101-002
tags:
- sched_ext
- proxy_execution
id: sched-20261102-016
subject: 'sched_ext: Fix stale pick when the donor changes during dispatch'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
