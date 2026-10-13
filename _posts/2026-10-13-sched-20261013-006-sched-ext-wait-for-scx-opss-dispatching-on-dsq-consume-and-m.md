---
id: sched-20261013-006
subject: 'sched_ext: Wait for SCX_OPSS_DISPATCHING on DSQ consume and move paths'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261012210749.2955291-1-jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/20261012210749.2955291-1-jpiecuch@google.com/
authors:
- Kuba Piecuch
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261012210749.2955291-1-jpiecuch@google.com>
  date: 2026-10-12
  summary: 在 DSQ consume/move 路径补 scx_wait_dispatching()，修 SCX_OPSS_DISPATCHING 并发竞态
  review_outcome: Andrea Righi 对两补丁均 Reviewed-by，无回归
upstream_commit: null
fixes_commit: ebf1ccff79c4
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Tejun Heo 收入 sched_ext/for-7.3-fixes，并按 cover 处理 for-7.4 冲突
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Wait for SCX_OPSS_DISPATCHING on DSQ consume and move paths'
layout: article
---

> **subject**：sched_ext: Wait for SCX_OPSS_DISPATCHING on DSQ consume and move paths

## TL;DR
Kuba Piecuch 发 2 补丁修复（挂 `sched_ext/for-7.3-fixes`）：任务可在「调度它的 CPU 仍在跑 `ops.dequeue()`、尚未清 `SCX_OPSS_DISPATCHING`」时就被发现在非本机 DSQ 上，而 DSQ 的 consume 与 move 路径不等 dispatch 完成、会与 dispatcher 并发操作同一任务。系列在 consume/move 关键路径补 `scx_wait_dispatching()`，Andrea Righi 已对两个补丁都给 `Reviewed-by`，`Cc: stable # v7.1+`。

## 背景与问题
dispatch 落到非本机 DSQ 时，`scx_dispatch_enqueue()` 会把任务链入 DSQ、更新 custody、放 DSQ 锁，然后（对 global/bypass DSQ）在**不持任务 rq 锁**的情况下调 `ops.dequeue()`，之后才写 `SCX_OPSS_NONE`。commit `ebf1ccff79c4`（"sched_ext: Fix ops.dequeue() semantics"）把最终 store 挪到 DSQ 解锁之后，`cb86607ada73`（"Don't run ops.dequeue() with a DSQ lock held"）又把 global/bypass 的 `ops.dequeue()` 挪出 DSQ 锁——于是任务可以在仍处 `SCX_OPSS_DISPATCHING` 时就被发现在 DSQ 上。`dequeue_task_scx()`/`set_next_task_scx()` 与 reenqueue 路径（`7de9a6fb44ea`）已加等待，但 DSQ consume 与 move 路径仍缺：

- `scx_consume_dispatch_q() -> scx_move_local_task_to_local_dsq()`（当消费 CPU 就是 `task_rq(p)`）：影响 global/bypass/user DSQ（`scx_bpf_dsq_move_to_local()`）；user DSQ 下消费者把任务拿出 custody 并自行调 `ops.dequeue()`，而 dispatcher 尚未完成。
- `move_task_between_dsqs()`（`scx_bpf_dsq_move[_vtime]()`）：把任务搬到另一个 local 或非本机 DSQ。

两条路径里消费者改 `p->scx`（dsq/dsq_list/flags，及 `scx_resolve_local_dsq()` 改道 rescue/reject DSQ 时的 reenqueue reason），甚至调 `ops.dequeue()`，而 dispatcher 仍可能在无 rq 锁下对同一任务跑 `ops.dequeue()`。

`Fixes: ebf1ccff79c4 / cb86607ada73`，`Cc: stable@vger.kernel.org # v7.1+`。

## 技术方案
两补丁（`kernel/sched/ext/ext.c` + `internal.h` + `sub.c`）：

- **Patch 1（renameme）**：`scx_reenq_wait_dispatching()` → `scx_wait_dispatching()`（等 `SCX_OPSS_DISPATCHING` 清空并不限于 reenqueue，任何把任务从 DSQ 取下的路径都可能命中在途 dispatch），同步更新注释。无功能变化。
- **Patch 2（加等待）**：`scx_move_local_task_to_local_dsq()`（在 `scx_resolve_local_dsq()` 之前，因为它会更新 `p->scx.flags`）、`unlink_dsq_and_switch_rq_lock()`、`move_task_between_dsqs()` 三处操作任务前先 `scx_wait_dispatching(p)`。远端 consume 路径 `unlink_dsq_and_switch_rq_lock()` → `move_remote_task_to_local_dsq()` 原本靠 `deactivate_task() -> ops_dequeue()` 里的等待覆盖，本系列把等待也加到 `unlink_dsq_and_switch_rq_lock()`，使那些在 deactivate 前或不 deactivate 就操作任务的调用方同样受保护。

作者说明：合入 for-7.4 有两处冲突（`cea8b60e4aee` 把 reject DSQ drain 移入 ext.c 需同步改名；`13ae184e4b82` 重构了 `unlink_dsq_and_switch_rq_lock()`），已在 cover 里给出冲突处理指引。

## 版本演进与当前进展
v1（cover `<20261012210749.2955291-1-jpiecuch@google.com>`，昨日收到）。当日 Andrea Righi 对两个补丁均给 `Reviewed-by`，并明确「The race is real, and the new waits cover the affected consume and move paths. I don't see any regressions from this series.」。尚未见 Tejun 的 Applied 回帖。

## Maintainer 意见与讨论焦点
- **Andrea Righi**（sched_ext 核心 reviewer）：认可竞态真实、覆盖到位、无回归，对两补丁都给 `Reviewed-by`。
- 无异议/NAK；待 Tejun Heo 收取。

## 合入评估
*likelihood=high*。竞态有可复现 WARN、修复有 reviewer 背书（Review-by）、挂 `stable # v7.1+` 说明属可回头合的修复。*blocking_issues*：待 Tejun 应用（且合入 for-7.4 有既定冲突需处理）。*next_action*：Tejun 收入 `sched_ext/for-7.3-fixes` 并按 cover 指引处理 for-7.4 冲突。

## 效果评估
作者用 `dequeue_remote` 自测 + 在 `scx_move_local_task_to_local_dsq()`/`move_task_between_dsqs()` 加 `WARN_ON_ONCE(... != SCX_OPSS_NONE)` 的调试补丁，在 vng guest 里数秒即触发 WARN；打上本系列后不再触发，且 `dequeue`/`dequeue_iter`/`dequeue_remote` 三个自测通过、dmesg 干净。

## 我可以参与的点
当前阶段暂无明显参与空间（review 已完成、方向明确）；可持续观察是否被 `for-7.3-fixes` 收取及是否进入 7.3 的 stable backport。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261012210749.2955291-1-jpiecuch@google.com/
