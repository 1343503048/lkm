---
id: sched-20261015-019
date: 2026-10-15
subject: 'sched/psi: Remove the RCU wait from trigger destruction'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261010191500.3895736-1-shakeel.butt@linux.dev>
lore_url: https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/
authors:
- Shakeel Butt
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261010191500.3895736-1-shakeel.butt@linux.dev>
  date: 2026-10-10
  summary: 移除 trigger 销毁路径 synchronize_rcu()，改 rcu_access_pointer
  review_outcome: Tejun Heo Acked-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 sched/psi 侧收取合入
contribution_opportunities: []
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20261011-001
tags:
- psi
title: 'sched/psi: Remove the RCU wait from trigger destruction'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-001-sched-psi-remove-the-rcu-wait-from-trigger-destruction.html">sched-20261011-001</a>：Shakeel Butt 移除 PSI trigger 销毁路径上的 `synchronize_rcu()`——Meta 生产环境发现该 RCU 等待在持有 kernfs `node_mutex` 时阻塞其他用户；补丁逐 commit 论证该等待已因历次重构失去必要性，改用 `rcu_access_pointer()` 做 `rtpoll_task` 的 NULL 检查。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-019-sched-psi-remove-the-rcu-wait-from-trigger-destruction.html">sched-20261015-019</a>（今天）：Tejun Heo 回 `Acked-by: Tejun Heo <tj@kernel.org>`。

## 背景与问题
（承接 20261011-001）Meta fleet 中 PSI trigger 销毁时会在持有 kernfs `node_mutex` 的情况下等待一次 RCU grace period，阻塞文件 close、cgroup 移除、禁用 `cgroup.pressure` 等其他持同一 mutex 的用户。该等待由 commit `0e94682b73bf` 引入，后经 `461daba06bdc`、`a06247c6804f`、`aff037078eca`、`5457025fa8ca` 等重构已不再保护任何存在对象，却仍在持锁路径上造成阻塞。

## 技术方案
（承接 20261011-001）移除 `synchronize_rcu()`，改用 `rcu_access_pointer()` 做 `rtpoll_task` 的 NULL 判断，`kthread_stop()` 保持在 trigger 互斥锁之外。今日无代码变更，仅新增维护者 Ack。

## 版本演进与当前进展
- v1（2026-10-10，<20261010191500.3895736-1-shakeel.butt@linux.dev>）：见 related 文章。
- 今天：Tejun Heo 给出 Acked-by。

## Maintainer 意见与讨论焦点
Tejun Heo（`sched/psi` 维护者）明确 Ack，无保留意见。

## 合入评估
*likelihood=high*。维护者 Acked-by，方向无争议。*blocking_issues*：无。*next_action*：等 Peter Zijlstra / Andrew Morton 侧收取合入（psi 属 sched/psi.c）。

## 效果评估
Meta 生产环境的症状（RCU 等待阻塞持 node_mutex 的用户）是动机来源，未提供量化数据。

## 我可以参与的点
当前阶段暂无明显参与空间，已获维护者 Ack；可持续观察。

## 参考链接
- Tejun 的 Ack：https://lore.kernel.org/all/as_aB-eIeU16h_JN@slm.duckdns.org/
- 原始补丁：https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/
