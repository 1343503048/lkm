# sched: Set TIF_NEED_RESCHED before calling __trace_set_need_resched()

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260912-007：Andrea Righi 发现 `sched_set_need_resched_tp` 在 `TIF_NEED_RESCHED` 置位前触发、可被 BPF 程序递归重入直至内核栈溢出；Gabriele Monaco 指出这与 Sechang 六月的系列是同一修复，Andrea 确认逐行相同并主动撤回。
- sched-20260913-004：kernel-patches CI 的 AI 审查 bot 提出新顺序在远程 CPU 分支可能破坏 RV nrp monitor 状态机，作者未回应，合入前景未定。
- sched-20260929-005：Andrea 复现出该顺序竞态导致 RV nrp monitor 状态机违规（300 次 `perf bench sched messaging` 下报 `schedule_entry_preempt on state any_thread_running`），提出把 `trace_sched_entry_tp()` 移到 `rq_lock()` 之后的 fold-in；Gabriele 担心移动打点破坏 sts monitor，建议先放宽竞态。
- sched-20261002-018（今天）：**Sechang Lim 的修复已被 Peter Zijlstra 合入 tip/sched/core**（commit `53bc5c556b82a3ca32b62ba349c4511f91526b9f`，CommitterDate 2026-10-01，tip-bot 于 10-02 回帖公告）。合入版本带 Andrea `Reviewed-by` 与 Gabriele `Acked-by`——此前 09-29 的打点位置分歧未阻塞本修复的收取（该分歧针对的是另一 tracepoint `sched_entry_tp` 的位置，而非本补丁的 `sched_set_need_resched_tp` 顺序）。

## 背景与问题

（承接 sched-20260913-004）`set_tsk_need_resched()` 先测试 `TIF_NEED_RESCHED`、标志清零时调 `__trace_set_need_resched()`，**之后**才经 `set_tsk_thread_flag()` 置位。挂到 `sched_set_need_resched` 上的 BPF raw_tp 程序在 `__bpf_trace_run()` 内同步执行；返回时 `rcu_read_unlock_migrate()` 在「关抢占或关 BH」路径上调用 `set_need_resched_current() -> set_tsk_need_resched()` 重入。由于 `set_tsk_thread_flag()` 在 tracepoint 之后，每个重入帧都看到 `TIF_NEED_RESCHED` 清零、再次发出 tracepoint，形成无限递归。合入 commit message 附带真实 Oops（KASAN 栈保护页命中）：

```
BUG: TASK stack guard page was hit at ffffc9001224ff98
Oops: stack guard page: 0000 [#1] SMP KASAN PTI
RIP: 0010:__bpf_trace_sched_set_need_resched_tp+0x1c/0x190
Call Trace:
 trace_sched_set_need_resched_tp+0x110/0x130
 set_tsk_need_resched include/linux/sched.h:2076
 set_need_resched_current include/linux/sched.h:2094
 rcu_read_unlock_special+0x43a/0x440
 ...
 __bpf_trace_sched_set_need_resched_tp+0x13a/0x190
```

`__resched_curr()` 有同样的顺序问题（先发 tracepoint 再置标志），随本补丁一并修复。触发面：BPF 程序挂载 `sched_set_need_resched_tp`（RV 任务模型监控是典型用户）；`Fixes: adcc3bfa8806`（"sched: Adapt sched tracepoints for RV task model"）。

## 技术方案

（承接，合入版即 v3 思路落地）两处修改，共 `include/linux/sched.h` +2/−3、`kernel/sched/core.c` +5/−2：

- `set_tsk_need_resched()`：把 `test_tsk_thread_flag()` + `set_tsk_thread_flag()` 拆分对替换为 `test_and_set_tsk_thread_flag()` 原子对——仅当标志原先清零时才发 `__trace_set_need_resched()`，重入帧看到已置位标志后不再递归。
- `__resched_curr()`：本地路径先 `set_ti_thread_flag()`/`set_preempt_need_resched()` 再发 tracepoint；远程路径先取 `need_ipi = set_nr_and_not_polling()` 并置标志、发 tracepoint，再按 `need_ipi` 决定是否发 IPI——tracing 仍先于 IPI 投递且观察到已更新的标志。

## 版本演进与当前进展

- v3（06-30，`<20260630084750.2792851-1-rhkrqnwk98@gmail.com>`）：上述两处修改，长时间无维护者表态。
- 09-12：Andrea 独立发现同一问题并发等价补丁，经 Gabriele 提示后撤回，让位于 Sechang 的版本。
- 09-29：Andrea 复现 RV nrp 竞态并提出 `sched_entry_tp` 移位 fold-in（另一问题域，未随本 commit 合入）。
- 10-01 合入 tip/sched/core（commit `53bc5c556b82a3ca32b62ba349c4511f91526b9f`），10-02 tip-bot 公告；合入版带 `Reviewed-by: Andrea Righi`、`Acked-by: Gabriele Monaco`。

## Maintainer 意见与讨论焦点

- 无 NAK。Andrea Righi（撤回自己的等价补丁、复现 RV 竞态后）给出 `Reviewed-by`；Gabriele Monaco 给出 `Acked-by`。
- 09-29 讨论中 Gabriele 对「移动 `sched_entry_tp` 打点位置」的顾虑与本补丁无关（本补丁只动 `sched_set_need_resched_tp` 的顺序），未构成本次合入的阻塞。
- Peter Zijlstra 直接收取，未提额外意见。

## 合入评估

*likelihood=merged*。已合入 `tip/sched/core`（commit `53bc5c556b82a3ca32b62ba349c4511f91526b9f`）。带 `Fixes:` 标签，属 bug 修复，进主线后大概率随 -rc 周期回合 stable。*blocking_issues*：无。*next_action*：关注 `sched_entry_tp` 位置问题（Andrea 09-29 fold-in / Gabriele 的放宽方案）是否有后续补丁——那是本线程暴露出的相邻问题。

## 效果评估

合入 commit message 附带递归 Oops 栈（如上），修复后重入被 `test_and_set` 原子语义截断。Andrea 09-29 的 300 次 `perf bench sched messaging -g 20 -l 100` RV nrp 复现（修复前违规、修复思路通过）是本问题域的量化佐证；本补丁自身无新 benchmark 数据。

## 我可以参与的点

- `new_patch`：跟进 09-29 讨论暴露的 `sched_entry_tp` 位置问题（Andrea fold-in vs Gabriele 放宽竞态方案），两者均未落地，可发后续补丁收敛。
- `testing`：在挂 BPF raw_tp + RV monitor 的负载下验证合入版无递归且 nrp/sts monitor 均不再违规。

## 参考链接

- lore（v3 补丁）: https://lore.kernel.org/all/20260630084750.2792851-1-rhkrqnwk98@gmail.com/
- tip commit: https://git.kernel.org/tip/53bc5c556b82a3ca32b62ba349c4511f91526b9f

---
id: sched-20261002-018
date: '2026-10-02'
subject: 'sched: Set TIF_NEED_RESCHED before calling __trace_set_need_resched()'
subsystem: sched
type: bug
status: merged_tip
severity: high
thread_root_msgid: '<20260630084750.2792851-1-rhkrqnwk98@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260630084750.2792851-1-rhkrqnwk98@gmail.com/'
authors:
  - 'Sechang Lim'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Andrea Righi'
  - 'Gabriele Monaco'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260630084750.2792851-1-rhkrqnwk98@gmail.com>'
    date: '2026-06-30'
    summary: 'test_and_set_tsk_thread_flag 原子化 + __resched_curr tracepoint 后移'
    review_outcome: 'Andrea 撤回等价补丁让位；10-01 合入 tip/sched/core，带 R-b/A-b'
upstream_commit: '53bc5c556b82a3ca32b62ba349c4511f91526b9f'
fixes_commit: 'adcc3bfa8806'
merged_branch: 'tip/sched/core'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '进主线后关注 stable 回合；跟进 sched_entry_tp 位置的相邻问题'
contribution_opportunities:
  - kind: new_patch
    description: '跟进 sched_entry_tp 位置问题（Andrea fold-in vs Gabriele 放宽方案）发后续补丁'
  - kind: testing
    description: 'BPF raw_tp + RV monitor 负载下验证合入版无递归且 nrp/sts monitor 不再违规'
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260912-007
  - sched-20260913-004
  - sched-20260929-005
tags:
  - tracepoints
  - bpf
  - rv
---
