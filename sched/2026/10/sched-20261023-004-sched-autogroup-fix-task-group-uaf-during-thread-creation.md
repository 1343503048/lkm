# sched/autogroup: Fix task_group UAF during thread creation

## TL;DR
Daehyeon Ko 发往 sched 的单补丁修复一个 autogroup 的 use-after-free：`sched_cgroup_fork()` 在 CLONE_THREAD 子进程尚未挂上线程链表前就把它指到 `p->signal->autogroup->tg`，而 autogroup 归属是 per-`signal_struct`、CLONE_THREAD 复用旧 `signal_struct` 且**不为子进程取 autogroup 引用**；`ksys_setsid()` 在释放 `tasklist_lock` 后才做 autogroup move，与 `copy_process()` 这段「未发布」窗口不互斥，最后一个 `autogroup_kref_put()` 可能丢掉旧 autogroup 的最后一根引用，两个 RCU 回调随后释放 per-CPU `cfs_rq`/`task_group`，而 `p->sched_task_group`/`p->se.cfs_rq` 仍指向它们。无特权 clone/setsid 竞态在 v7.3 触发 KASAN task_group slab UAF。`Fixes: b1e8206582f9`、`Cc: stable`。尚无 review。

## 背景与问题
竞态时序（两侧并发）：

```
clone(CLONE_THREAD) 调用方      兄弟 setsid() 调用方
---------------------         -------------------------
sched_cgroup_fork()
                              sched_autogroup_create_attach()
                                autogroup_move_group()
                                  lock(siglock)
                                  signal->autogroup = new
                                  for_each_thread()
                                  unlock(siglock)
                                  autogroup_kref_put(old)
lock(siglock)
list_add_tail_rcu(thread_node)
unlock(siglock)
wake_up_new_task()
```

setsid 侧遍历线程时看不到尚未发布的子进程；最后那次 `autogroup_kref_put(old)` 可能因此丢掉 `signal` 对旧 autogroup 的最后一根引用，其后 RCU 回调释放 per-CPU `cfs_rq` 与 `task_group`，而新线程的 `p->sched_task_group`、`p->se.cfs_rq`、`p->se.parent` 仍指向这些已释放对象。

## 技术方案
单补丁（`include/linux/sched/autogroup.h` + `kernel/fork.c` + `kernel/sched/autogroup.c`，+44 行）：

- 在 `copy_process()` 最后一个无失败路径点，对 `CLONE_THREAD` 子进程调用新增 `sched_autogroup_fork_finalize(p, args)`，**持有共享 siglock** 重新校验其调度组，并把锁一路持有到线程链表发布——这样一次 autogroup move 要么在重校验前完成，要么阻塞到发布后、从而能看到该子进程。
- `sched_autogroup_fork_finalize()` 在 `p->pi_lock` 下：若 `autogroup_task_group(p, tg)` 与 `p->sched_task_group` 不一致，则更新 `p->sched_task_group`、将 `p->se.cfs_rq` 清空（防止 `set_task_rq_fair()` 检视已释放的旧 runqueue），并调用 `set_task_rq()` 重建 fair/RT 组链接。`TASK_NEW` 子进程无已挂负载需迁移。

## 版本演进与当前进展
*current_version: v1*（`<20261023013631.881730-1-4ncienth@gmail.com>`）。当日发出，暂无 review。作者注明 AI 编码助手协助识别与验证竞态、构造 reproducer 并起草/测试补丁。

## Maintainer 意见与讨论焦点
暂无维护者/资深成员回帖。补丁带 `Fixes: b1e8206582f9 ("sched: Fix yet more sched_fork() races")` 与 `Cc: stable@vger.kernel.org`，说明作者视其为一处既有 fork 竞态修复的延续。涉及的 siglock/pi_lock 加锁顺序与 `copy_process()` 失败路径需要资深 reviewer 把关。

## 合入评估
*likelihood=medium*。是真实的 UAF（无特权重现）+ 带 Fixes/stable，安全意义明确；但触及 `copy_process()` 与 autogroup 锁序，复杂度高于一般修复，且尚无任何 review。*blocking_issues*：无 review；锁序（siglock/pi_lock）与 `copy_process()` 失败路径的交互需确认。*next_action*：等 Peter/autogroup 相关维护者 review 后收取。

## 效果评估
正确性修复，无性能数据。作者用 uid/gid 65534、全部 capability 集合为空的 unprivileged reproducer 在未改动的 v7.3 内核上触发 `wake_up_new_task()` 中的 KASAN task_group slab use-after-free；分配来自 `sched_create_group()`、释放来自 `sched_free_group_rcu()`。修复后完成 1024 轮「原始竞态扫描 + 延迟 setsid 压力」均无 KASAN/lockdep/oops/panic 报告。

## 我可以参与的点
- *kind: review*：重点核对 `sched_autogroup_fork_finalize()` 的 siglock/pi_lock 顺序、以及「重校验后到线程发布前」窗口内是否仍有遗漏。
- *kind: testing*：用并发 clone(CLONE_THREAD)+setsid() 压力（含 LOCKDEP/KASAN 配置）验证补丁后不再 UAF。

## 参考链接
- patch: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/

---
id: sched-20261023-004
date: 2026-10-23
subject: "sched/autogroup: Fix task_group UAF during thread creation"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<20261023013631.881730-1-4ncienth@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/"
authors: ["Daehyeon Ko"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261023013631.881730-1-4ncienth@gmail.com>"
    date: 2026-10-23
    summary: "在 copy_process 最后无失败点持 siglock 重校验 autogroup，消除 task_group UAF"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "b1e8206582f9"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["无 review", "siglock/pi_lock 锁序与 copy_process 失败路径交互需确认"]
  next_action: "等 Peter/autogroup 维护者 review 后收取"
contribution_opportunities:
  - kind: review
    description: "核对 sched_autogroup_fork_finalize 锁序与重校验窗口是否有遗漏"
  - kind: testing
    description: "并发 clone(CLONE_THREAD)+setsid() 压力 + LOCKDEP/KASAN 验证不再 UAF"
generated_at: "2026-10-24T09:03:00"
source_email_count: 1
related_articles: []
tags: [autogroup, cgroup, crash]
---