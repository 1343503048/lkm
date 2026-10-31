# sched/autogroup: Fix task_group UAF during thread creation

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261023-004：Daehyeon Ko 发单补丁修 autogroup 的 use-after-free：`sched_cgroup_fork()` 在 CLONE_THREAD 子进程尚未挂上线程链表前就把它指到 `p->signal->autogroup->tg`，而 CLONE_THREAD 复用旧 `signal_struct` 且不为子进程取 autogroup 引用；`ksys_setsid()` 在释放 `tasklist_lock` 后才做 autogroup move，与 `copy_process()` 的未发布窗口不互斥，最后一次 `autogroup_kref_put()` 可能丢掉旧 autogroup 的最后一根引用、RCU 回调随后释放 per-CPU cfs_rq/task_group。`Fixes: b1e8206582f9`、`Cc: stable`。
- sched-20261026-003：Peter Zijlstra 质疑现方案「I'm not sure this works; afaict this will result in a NULL deref instead.」并建议把复杂度移到 `ksys_setsid()`。
- sched-20261030-008（今天）：Daehyeon 回应 NULL-deref 疑虑（新 cfs_rq 由 `set_task_rq()` 既有契约兜底），并论证仅把 autogroup move 移到 tasklist_lock 下不足以关窗；Peter 复信「No, I think you're right. Also, its a mess :/」——收回之前的否定，转而建议利用 AUTOGROUP 依赖 CGROUP 的关系，让 `autogroup_move_group()` 也持有 `cgroup_threadgroup_rwsem`，使 autogroup 与 cgroup 逻辑同步。

## 背景与问题
（承接 20261023-004 → 20261026-003）竞态时序不变：`clone(CLONE_THREAD)` 侧 `sched_cgroup_fork()` 把子进程指到旧 `autogroup->tg` 发生在线程链表发布之前；`setsid()` 侧在该窗口内换掉 `signal->autogroup` 并 `autogroup_kref_put(old)`。今日 Daehyeon 补强了对原先「NULL 解引用」质疑的论证，并给出关键时序：`sched_cgroup_fork()` 在 `copy_process()` 拿 `tasklist_lock` **之前**执行，因此仅「把 autogroup move 挪进 tasklist_lock」并不能关窗——setsid 的 move 与「发布子进程」之间仍有交错（作者实测命中该 pre-publication 序列 7 次）。

## 技术方案
（承接 20261026-003 的讨论）今日方向分两路：

- **作者既有设计**：`__sched_fork()` 把 `p->se.cfs_rq` 初始化为 NULL，`sched_cgroup_fork()` 经 `__set_task_cpu()` 走到 `set_task_rq()`；`set_task_rq_fair()` 在 prev 为 NULL 时提前返回（不碰 `cfs_rq_last_update_time(prev)`），随后 `set_task_rq()` 装好新 cfs_rq/parent/depth——因此「prev 为 NULL」由既有契约兜底，不会 NULL 解引用。作者仍坚持用最终的再校验覆盖未发布窗口。
- **Peter 的新提议**：既然 AUTOGROUP **依赖** CGROUP，就让 `autogroup_move_group()` 也使用 `cgroup_threadgroup_rwsem`，使 autogroup 与 cgroup 的逻辑保持同一套串行化；他不愿把 `sched_core_fork()` 挪进 siglock 区（那要复制大半 `sched_cgroup_fork()`，「为一个 autogroup 的事搞这么乱很怪」）。

## 版本演进与当前进展
*current_version: v1*（2026-10-23 首发；今日无新版本，为方向收敛讨论）。维护者由「否定修复路径」转为「认可作者分析 + 提出更干净的串行化方案」，接下来需要作者在「再校验」与「cgroup_threadgroup_rwsem 化 autogroup_move_group」之间取舍并发新版。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（maintainer）**：今日松口认可作者分析，但明确觉得现有 sched 钩子（`free_signal_struct`/`__put_task_struct`/`copy_mm`/`copy_signal`/`copy_process`/`sched_core_fork` 等）太多、是「一个乱摊子」，倾向于复用 `cgroup_threadgroup_rwsem` 而非继续加钩子。
- **Daehyeon Ko（作者）**：进一步论证原方案的正确性，并指出「仅挪 tasklist_lock」的局限性。
- **未解决**：最终落地走哪条路线（作者再校验 vs Peter 的 cgroup_threadgroup_rwsem）未定；`Cc: stable`/`Fixes` 诉求仍在。

## 合入评估
*likelihood=medium*。维护者已不再否定、方向趋于达成共识，但设计尚未收敛到具体补丁（路线仍在讨论），且 Peter 对复杂度敏感。*blocking_issues*：需要在「再校验」与「cgroup_threadgroup_rwsem 化 autogroup_move_group」之间定案并发新版。*next_action*：作者按 Peter 的 cgroup_threadgroup_rwsem 方向（或说服 Peter 维持再校验）发 v2。

## 效果评估
无性能数据；修复为正确性（KASAN slab UAF），作者此前已给出无特权 clone/setsid 竞态的复现基础。

## 我可以参与的点
- **review**：评估 `autogroup_move_group()` 改用 `cgroup_threadgroup_rwsem` 后与现有 `cgroup_threadgroup_rwsem` 使用点（cgroup_fork/cgroup_post_fork）是否有锁序/死锁风险。
- **discussion**：对两条路线（再校验 vs cgroup_threadgroup_rwsem）的锁竞争与复杂度做量化权衡。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/

---
id: sched-20261030-008
date: 2026-10-30
subject: "sched/autogroup: Fix task_group UAF during thread creation"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<20261023013631.881730-1-4ncienth@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261023013631.881730-1-4ncienth@gmail.com/"
authors: [Daehyeon Ko]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "落地路线未定：作者再校验 vs Peter 的 cgroup_threadgroup_rwsem 化 autogroup_move_group"
  next_action: "作者按 cgroup_threadgroup_rwsem 方向发 v2（或说服 Peter 维持再校验）"
contribution_opportunities:
  - kind: review
    description: "评估 autogroup_move_group() 改用 cgroup_threadgroup_rwsem 的锁序与死锁风险"
  - kind: discussion
    description: "对再校验 vs cgroup_threadgroup_rwsem 两条路线的锁竞争与复杂度做权衡"
generated_at: "2026-10-31T09:00:00"
source_email_count: 2
related_articles: [sched-20261023-004, sched-20261026-003]
tags: [autogroup, cgroup]
---