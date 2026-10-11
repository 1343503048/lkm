---
id: sched-20261011-001
date: '2026-10-11'
subject: 'sched/psi: Remove the RCU wait from trigger destruction'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010191500.3895736-1-shakeel.butt@linux.dev>
lore_url: https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/
authors:
- Shakeel Butt
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261010191500.3895736-1-shakeel.butt@linux.dev>
  date: '2026-10-11'
  summary: psi_trigger_destroy() 移除 synchronize_rcu()，worker NULL 检查改用 rcu_access_pointer()，kthread_stop()
    保持在 trigger mutex 之外
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无 psi 维护者 review（刚发出）
  next_action: 等 psi 维护者 review 并确认无遗漏的并发访问路径
contribution_opportunities:
- kind: review
  description: 核对 rcu_access_pointer() 后 rtpoll_task 读取在迟到 timer 场景下的可见性
- kind: testing
  description: 在更大规模/不同 RCU 配置下复测 trigger churn 与 cgroup removal
generated_at: '2026-10-12T01:00:00'
source_email_count: 1
related_articles: []
tags:
- psi
- cgroup
title: 'sched/psi: Remove the RCU wait from trigger destruction'
layout: article
---

## TL;DR

Shakeel Butt 移除 PSI trigger 销毁路径上的 `synchronize_rcu()`——Meta 生产环境发现该 RCU 等待在持有 kernfs `node_mutex` 时阻塞其他用户（文件关闭、cgroup 移除、禁用 cgroup.pressure 等）。补丁逐 commit 论证该等待已因历次重构失去必要性，改用 `rcu_access_pointer()` 做 `rtpoll_task` 的 NULL 检查，并把 `kthread_stop()` 保持在 trigger 互斥锁之外。刚发出，暂无 review。

## 背景与问题

在 Meta fleet 中，PSI trigger 销毁时会在持有 kernfs `node_mutex` 的情况下等待一次 RCU grace period，从而阻塞其他用户 [1]。文件 close 与 node drain 在调用 release 回调时持有该 mutex；cgroup 移除与禁用 `cgroup.pressure` 也在 drain 期间持有 `cgroup_mutex`。该等待最初由 commit `0e94682b73bf`（"psi: introduce psi monitor"）引入，用于保护 worker 与 trigger 的查找；但随后的一系列重构使其保护的对象已不复存在（见技术方案），等待不再必要，却仍在持锁路径上造成阻塞。

## 技术方案

补丁论证 `synchronize_rcu()` 已无必要（逐 commit 梳理）：

- `461daba06bdc`（"psi: eliminate kthread_worker from psi trigger scheduling mechanism"）用 group timer 取代 kthread worker 队列；调度器现在只检查 `rtpoll_task` 是否为 NULL，既不用 task 也不用 trigger。
- `a06247c6804f`（"psi: Fix uaf issue when psi trigger is destroyed while being polled"）移除了 trigger 替换与 polling 的 RCU 查找。
- trigger 链表由互斥锁保护；proc poll/select 条目在其文件引用被 drop 前移除；`eventpoll_release()` 在文件 release 回调之前移除 epoll 条目；`aff037078eca`（"sched/psi: use kernfs polling functions for PSI trigger polling"）把 cgroup polling 移到 kernfs waitqueue，其生命周期跟随文件。
- 迟到的 timer 触发只会唤醒 group waitqueue；系统 group 是静态的，`5457025fa8ca`（"sched/psi: Shut down rtpoll_timer in psi_cgroup_free()"）在释放 group 前关闭 cgroup timer；cgroup 回收本身已等待调度器读者。

改动：`psi_trigger_destroy()` 删除 `synchronize_rcu()`，worker NULL 检查改用 `rcu_access_pointer()`，`kthread_stop()` 保持在 trigger mutex 之外。`kernel/sched/psi.c` 1 文件，+5/−20。

## 版本演进与当前进展

v1 刚发出（2026-10-11），暂无 review 意见。

## Maintainer 意见与讨论焦点

无。作者 Shakeel Butt 本人是内核维护者（cgroup/memcg 方向，此前多笔 PSI 提交），但本补丁尚未见 psi 维护者（Johannes Weiner 等）表态。

## 合入评估

*likelihood=medium*。改动小、动机来自真实生产规模触发、论证逐 commit 详实且自带 KASAN/lockdep 测试；但刚发出、psi 维护者尚未 review。*blocking_issues*：无维护者 review（刚发出）。*next_action*：等 psi 维护者 review 并确认 `synchronize_rcu()` 移除后无遗漏的并发访问路径后收取。

## 效果评估

无 benchmark 数字。作者在 8-CPU VM（KASAN、lockdep、full 与 lazy preemption）上测试了 trigger churn、notification 与 cgroup removal，无告警——用于证明移除 RCU 等待后未引入 UAF/竞态回归，而非性能提升数据。

## 我可以参与的点

- `review`：核对改用 `rcu_access_pointer()` 之后 `rtpoll_task` 的读取在「迟到 timer 触发」等场景下是否仍满足可见性/生命周期要求。
- `testing`：在更大规模 cgroup 数量或不同内核配置（如 RCU 配置差异）下复测 trigger churn 与 cgroup removal，回帖补数据。

## 参考链接

- lore（本补丁）: https://lore.kernel.org/all/20261010191500.3895736-1-shakeel.butt@linux.dev/
- 正文引用 [1]: https://github.com/bpftrace/user-tools/tree/master/runnablelockmonitor
