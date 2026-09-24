---
id: sched-20260916-004
date: '2026-09-16'
subject: 'sched_ext: Unlink pending local reenqueues before freeing scheduler'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <20260916145807.3250167-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260916145807.3250167-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260916145807.3250167-1-arighi@nvidia.com>
  date: '2026-09-16'
  summary: 释放 sch->pcpu 前取 rq 锁解除挂起的 deferred local reenqueue 请求，避免 UAF
  review_outcome: 暂无回复
upstream_commit: null
fixes_commit: 0d8c551dd5de
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 待 Tejun 收入 sched_ext/for-7.3-fixes 并回合 stable
contribution_opportunities:
- kind: review
  description: 核对 rq 锁与 deferred_reenq_lock 双重保护顺序与 run_deferred() 是否对称、无死锁
- kind: testing
  description: 在高核数 arm64 上反复 attach/detach 验证无残留节点告警
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- crash
title: 'sched_ext: Unlink pending local reenqueues before freeing scheduler'
layout: article
---

## TL;DR
Andrea Righi 的 sched_ext 修复：调度器 teardown 时若仍有一个已链接但未消费的 deferred local reenqueue 请求挂在 rq 列表上，`scx_sched_free_rcu_work()` 只告警一声就释放 `sch->pcpu`，后续 `run_deferred()` 会顺着悬空节点解引用已释放内存，造成 use-after-free 与系统级 oops。修复在释放前取 rq 锁并解除该请求。带 `Fixes:` 与 `Cc: stable # v7.1+`，属 7.3-fixes，严重度高。

## 背景与问题
deferred local DSQ reenqueue 把链表节点嵌入 `struct scx_sched_pcpu` 并链接进 `rq->scx.deferred_reenq_locals`。调度器 teardown 在 RCU grace period 之前进入 bypass，能阻止新请求，但**不保证**一个已链接的请求已经被消费——RCU grace period 只等待活跃读者，不 flush 挂起的 rq deferred 请求。`scx_sched_free_rcu_work()` 假设每个节点已移除，只对残留节点告警后便释放 `sch->pcpu`，于是 rq 列表保留了一个指向已释放 per-CPU 存储的指针。

## 技术方案
在释放 `sch->pcpu` 之前取消任何挂起的 local reenqueue：先取 rq 锁，等待任何 in-flight 的 `run_deferred()` 并阻止新的开始，再在 `deferred_reenq_lock` 下用 `list_del_init()` 解除请求（teardown 时该请求已过时）。改动集中在 `kernel/sched/ext/ext.c` 的 `scx_sched_free_rcu_work()`（12 insertions / 5 deletions）。

## 版本演进与当前进展
- **v1**（本日 107541，`<20260916145807.3250167-1-arighi@nvidia.com>`）：单枚补丁，带 `Fixes: 0d8c551dd5de ("sched_ext: Make scx_bpf_reenqueue_local() sub-sched aware")` 与 `Cc: stable # v7.1+`。

## Maintainer 意见与讨论焦点
本日暂无维护者回复（Andy 刚发出）。补丁正文给出了完整的复现路径与崩溃签名，属自包含的明确修复。

## 合入评估
*likelihood=high*。明确的 use-after-free 修复，`Fixes:` 与 stable 标签齐全，复现清晰（352-CPU arm64 上反复 attach/detach + hackbench 稳定触发），改动小而聚焦。*blocking_issues*：无。*next_action*：待 Tejun 收入 sched_ext/for-7.3-fixes 并回合 stable v7.1+。

## 效果评估
复现步骤：循环 100 次 `scx_cidland --stats 1` + `hackbench -l 2000 -g 100`。第二次 detach 时 `scx_sched_free_rcu_work()` 报告 pending 节点告警，随后 hackbench 进程命中悬空节点：`Unable to handle kernel paging request at 000000000010b8bf`，调用栈 `run_deferred -> task_woken_scx -> wake_up_new_task -> kernel_clone`；oops 后中断被关闭并伴随持续 RCU stall，「系统不可用」。修复后不再触发。

## 我可以参与的点
- kind=review：核对「取 rq 锁 + `deferred_reenq_lock`」双重保护的顺序是否与 `run_deferred()` 一侧完全对称、无死锁可能。
- kind=testing：在多种拓扑（尤其高核数 arm64）上反复 attach/detach SCX 调度器验证不再有残留节点告警。

## 参考链接
- patch：https://lore.kernel.org/all/20260916145807.3250167-1-arighi@nvidia.com/
