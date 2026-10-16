# sched/psi: Remove the RCU wait from trigger destruction

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261011-001：Shakeel Butt 移除 PSI trigger 销毁路径上的 `synchronize_rcu()`——Meta 生产环境发现该 RCU 等待在持有 kernfs `node_mutex` 时阻塞其他用户；补丁逐 commit 论证该等待已因历次重构失去必要性，改用 `rcu_access_pointer()` 做 `rtpoll_task` 的 NULL 检查。
- sched-20261015-019：Tejun Heo 回 `Acked-by`。
- sched-20261016-006（今天）：**Peter Zijlstra 合入 tip sched/core（commit 6f88f6cbb047）**。

## 背景与问题
（承接 20261011-001）Meta fleet 中 PSI trigger 销毁时在持有 kernfs `node_mutex` 的情况下等待一次 RCU grace period，阻塞文件 close、cgroup 移除、禁用 `cgroup.pressure` 等持同一 mutex 的用户。该等待由 commit `0e94682b73bf` 引入，后经 `461daba06bdc`、`a06247c6804f`、`aff037078eca`、`5457025fa8ca` 等重构已不再保护任何存在对象。

## 技术方案
（承接 20261011-001）移除 `synchronize_rcu()`，改用 `rcu_access_pointer()` 做 `rtpoll_task` 的 NULL 判断，`kthread_stop()` 保持在 trigger 互斥锁之外。今日无代码变更，仅合入。

## 版本演进与当前进展
- v1（2026-10-10，<20261010191500.3895736-1-shakeel.butt@linux.dev>）→ Tejun Acked-by → 今天 Peter 合入 tip sched/core（`6f88f6cbb047`）。

## Maintainer 意见与讨论焦点
Tejun Heo 明确 Ack；Peter Zijlstra 收取合入。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/core（commit `6f88f6cbb047`）。*blocking_issues*：无。*next_action*：无（已合入）。

## 效果评估
Meta 生产环境的症状（RCU 等待阻塞持 node_mutex 的用户）是动机来源；合入 commit 注明作者在 8-CPU VM 上用 KASAN/lockdep、full 与 lazy preemption 测过 trigger churn、通知与 cgroup 移除，无告警。

## 我可以参与的点
当前阶段已合入，无明显参与空间。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213767937.2666988.13837414149970977922.tip-bot2@tip-bot2/
- 原始补丁：https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/

---
id: sched-20261016-006
date: 2026-10-16
subject: "sched/psi: Remove the RCU wait from trigger destruction"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261010191500.3895736-1-shakeel.butt@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/"
authors: ["Shakeel Butt"]
maintainers_involved: ["Tejun Heo", "Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261010191500.3895736-1-shakeel.butt@linux.dev>"
    date: 2026-10-10
    summary: "移除 trigger 销毁路径 synchronize_rcu()，改 rcu_access_pointer"
    review_outcome: "Tejun Acked-by；Peter 合入 tip sched/core"
upstream_commit: "6f88f6cbb047"
fixes_commit: null
merged_branch: "sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无（已合入）"
contribution_opportunities: []
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: ["sched-20261011-001", "sched-20261015-019"]
tags: [psi]
---
