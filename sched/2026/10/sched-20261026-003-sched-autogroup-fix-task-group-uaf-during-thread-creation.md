# sched/autogroup: Fix task_group UAF during thread creation

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261023-004：Daehyeon Ko 发往 sched 的单补丁修复一个 autogroup 的 use-after-free：`sched_cgroup_fork()` 在 CLONE_THREAD 子进程尚未挂上线程链表前就把它指到 `p->signal->autogroup->tg`，而 autogroup 归属是 per-`signal_struct`、CLONE_THREAD 复用旧 `signal_struct` 且**不为子进程取 autogroup 引用**；`ksys_setsid()` 在释放 `tasklist_lock` 后才做 autogroup move，与 `copy_process()` 这段「未发布」窗口不互斥，最后一个 `autogroup_kref_put()` 可能丢掉旧 autogroup 的最后一根引用，两个 RCU 回调随后释放 per-CPU `cfs_rq`/`task_group`，而 `p->sched_task_group`/`p->se.cfs_rq` 仍指向它们。无特权 clone/setsid 竞态在 v7.3 触发 KASAN task_group slab UAF。`Fixes: b1e8206582f9`、`Cc: stable`。
- sched-20261026-003（今天）：Peter Zijlstra 首次表态——「I'm not sure this works; afaict this will result in a NULL deref instead.」质疑现方案会把 UAF 换成 NULL 解引用，并给出替代方向：「能不能让 `ksys_setsid()` 更复杂一点？在 `tasklist_lock` 下**提前创建** autogroup、失败时再销毁」。补丁的修复路径被维护者否定，需作者改弦更张。

## 背景与问题
（承接 sched-20261023-004）竞态时序：`clone(CLONE_THREAD)` 侧 `sched_cgroup_fork()` 把子进程指到 `p->signal->autogroup->tg` 发生在「尚未通过 `list_add_tail_rcu(thread_node)` 发布」的窗口内；`setsid()` 侧 `sched_autogroup_create_attach()` 在拿 `siglock` 后把 `signal->autogroup` 换成新的、`for_each_thread()` 遍历（此时看不到未发布的子进程）、再 `autogroup_kref_put(old)`。两侧并发下，最后一次 `kref_put` 可能丢掉 `signal` 对旧 autogroup 的最后一根引用，RCU 回调随后释放 per-CPU `cfs_rq`/`task_group`，而新线程仍指向它们。

今日无新背景，为维护者首次（且否定性）review。

## 技术方案
（承接 sched-20261023-004）原方案：在 `copy_process()` 最后一个无失败路径点，对 `CLONE_THREAD` 子进程新增 `sched_autogroup_fork_finalize(p, args)`，持有共享 siglock 重新校验调度组并把锁持有到线程链表发布，从而让一次 autogroup move 要么在重校验前完成、要么能看到该子进程；不一致时更新 `p->sched_task_group`、清空 `p->se.cfs_rq` 并 `set_task_rq()` 重建链接。

今日进展：**Peter Zijlstra 否定该修复路径**——「I'm not sure this works; afaict this will result in a NULL deref instead.」即担心把 UAF 换成 NULL 解引用。他给出的替代设计：**把复杂度移到 `ksys_setsid()`**——提前创建 autogroup、在 `tasklist_lock` 下 move、失败（或路径）时再销毁。

## 版本演进与当前进展
*current_version: v1*（`<20261023013631.881730-1-4ncienth@gmail.com>`）。当日无新版本，进展为收到维护者 Peter 的否定性 review。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：对 v1 方案的质疑是实质性的——「I'm not sure this works; afaict this will result in a NULL deref instead.」并提议改在 `ksys_setsid()` 内提前创建 autogroup、持 `tasklist_lock` move、失败时销毁。

发散点：Peter 不认可「在 fork 侧重校验」的方向，而是倾向把竞态关在 `setsid()` 一侧。作者尚未回应。

## 合入评估
*likelihood=medium*。UAF 本身真实且带 `Fixes:`/`Cc: stable`，安全意义明确；但维护者明确质疑现方案的正确性并提出替代方向，v1 的 fork 侧修法大概率不会被原样收取。*blocking_issues*：Peter 认为现方案会导致 NULL deref、需改为 `ksys_setsid()` 侧处理。*next_action*：作者回应 Peter 的 NULL deref 疑虑，评估 `ksys_setsid()` 提前建 autogroup 方案的可行性并重发。

## 效果评估
正确性修复，无性能数据。作者此前用 uid/gid 65534、空 capability 集合的 unprivileged reproducer 在 v7.3 触发 KASAN task_group slab use-after-free；修复后 1024 轮竞态扫描 + 延迟 setsid 压力无 KASAN/lockdep/oops/panic 报告。今日无新数据。

## 我可以参与的点
- *kind: review*：复核 Peter 提出的 NULL deref 疑虑（`sched_autogroup_fork_finalize()` 清空 `p->se.cfs_rq` 后是否有路径直接解引用），并评估 `ksys_setsid()` 提前建 autogroup 方案的加锁/失败路径。
- *kind: testing*：用并发 clone(CLONE_THREAD)+setsid() 压力（LOCKDEP/KASAN）对作者的替代方案做回归验证。

## 参考链接
- patch（v1）: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/
- Peter 今日回帖: https://lore.kernel.org/all/20261026115707.GF2668200@noisy.programming.kicks-ass.net/
- 前文: sched-20261023-004

---
id: sched-20261026-003
date: 2026-10-26
subject: 'sched/autogroup: Fix task_group UAF during thread creation'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: '<20261023013631.881730-1-4ncienth@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/'
authors:
  - 'Daehyeon Ko'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261023013631.881730-1-4ncienth@gmail.com>'
    date: 2026-10-23
    summary: 'copy_process 最后无失败点持 siglock 重校验 autogroup，消除 task_group UAF'
    review_outcome: 'Peter 质疑会变 NULL deref，建议改在 ksys_setsid() 侧提前建 autogroup'
upstream_commit: null
fixes_commit: 'b1e8206582f9'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Peter 认为现方案会引入 NULL deref，需改在 ksys_setsid() 侧处理'
  next_action: '作者回应 NULL deref 疑虑并评估 ksys_setsid() 提前建 autogroup 方案'
contribution_opportunities:
  - kind: review
    description: '复核 fork 侧重校验的 NULL deref 风险与 ksys_setsid 方案的加锁/失败路径'
  - kind: testing
    description: '并发 clone(CLONE_THREAD)+setsid() 压力 + LOCKDEP/KASAN 回归验证替代方案'
generated_at: '2026-10-27T01:00:00'
source_email_count: 1
related_articles:
  - sched-20261023-004
tags:
  - autogroup
  - cgroup
  - crash
---