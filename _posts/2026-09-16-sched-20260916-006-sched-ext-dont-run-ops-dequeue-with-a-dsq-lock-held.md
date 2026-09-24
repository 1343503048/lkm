---
id: sched-20260916-006
date: '2026-09-16'
subject: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260916070753.3343113-1-fangqiurong@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260916070753.3343113-1-fangqiurong@kylinos.cn/
authors:
- Qiurong Fang
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v3
patch_series:
- version: v3
  msgid: <20260916070753.3343113-1-fangqiurong@kylinos.cn>
  date: '2026-09-16'
  summary: 收紧死锁描述并 open-code 掉 call_task_dequeue()，unlink 后立即解锁 src_dsq
  review_outcome: 完整落实 Tejun 评审，patch 1 带 Andrea Righi Acked-by
upstream_commit: null
fixes_commit: ebf1ccff79c4
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 待 Tejun 收入 sched_ext 修复分支并回合 stable
contribution_opportunities:
- kind: testing
  description: 修复前后分别跑 dequeue_iter selftest，验证死锁复现与修复
- kind: review
  description: 核对 unlink 后解锁窗口内 SCX_TASK_IN_CUSTODY 清除的并发正确性
generated_at: '2026-09-17T09:00:00'
source_email_count: 5
related_articles:
- sched-20260915-003
tags:
- sched_ext
- hang
title: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
layout: article
---

## TL;DR
Qiurong Fang 的 v3：`ops.dequeue()` 在 consume/move 路径上仍带着源 user DSQ 锁被调用，任何从 `ops.dequeue()` 回锁同一 DSQ 的 BPF 调度器会自死锁。v3 按 Tejun Heo 的全套评审意见重写：收紧死锁描述到两条 user DSQ 路径、open-code 掉 `call_task_dequeue()`、放弃拆分直接「unlink 后立即解锁 @src_dsq」、selftest 补齐 select_cpu/UEI/SCX_EXIT_UNREG。带稳定标签，合入概率高。

## 背景与问题
`ebf1ccff79c4 ("sched_ext: Fix ops.dequeue() semantics")` 之后，`ops.dequeue()` 在 consume（`scx_consume_dispatch_q()`）与 move（`move_task_between_dsqs()`）两条路径上仍持源 user DSQ 锁被调用。若 BPF 调度器在 `ops.dequeue()` 里锁同一 DSQ——典型如用 `bpf_iter_scx_dsq` 迭代（每步拿 DSQ 锁）——即与本身路径自死锁，CPU 带 IRQ 关闭地死锁，watchdog 无法恢复。另有一条只影响 lockdep 的路径：所有 DSQ 锁共享一个 lockdep class，在任何 user DSQ 上迭代都会触发递归检查。

## 技术方案
v3 把三条路径上的 `ops.dequeue()` 调用统一移到 DSQ 解锁之后：`SCX_TASK_IN_CUSTODY` 仍在锁内清除以保证回调恰好执行一次（`task_leave_custody()`），回调本身在无 DSQ 锁状态下执行（`ops.dequeue()` 只允许调用 "any" kfuncs，不能锁 builtin DSQ，因此 global/bypass 路径天然不会死锁，只是 shared lockdep class 会触发递归检查）。consumer/move 路径改为「`scx_task_unlink_from_dsq()` 后立即 `raw_spin_unlock(&src_dsq->lock)`，再调用 `scx_move_local_task_to_local_dsq()`」。

## 版本演进与当前进展
- **v3**（本日 106297，`<20260916070753.3343113-1-fangqiurong@kylinos.cn>`）：按 Tejun 上轮评审逐条落实——死锁描述收窄到两条 user DSQ 路径、删掉 ordering 句与文档改动（待 DISPATCHING reenq 洞修复后再加）、open-code 并删除 `call_task_dequeue()`、放弃 `__scx_move_local_task_to_local_dsq()` 拆分、selftest 加 select_cpu/UEI/SCX_EXIT_UNREG、`ops.timeout_ms` 改为 1000U、加 `Cc: stable # v7.1+`。
- v2 回顾：补了迭代源 DSQ 的 selftest，删掉被 Andrea 纠正的回调时序说法。

## Maintainer 意见与讨论焦点
- **Tejun Heo（v2→v3 评审）**：逐条给出可执行意见——自死锁只存在于两条 user DSQ 路径；要求把「任务在 `ops.dequeue()` 完成前不能开始运行或被 reenqueue」的不变量说清楚（或删掉）；指出该不变量当前有个洞（DISPATCHING reenq，见 sched-20260916-005）会本补丁放大、由其单独修；要求 open-code 掉只剩两个调用点的 `call_task_dequeue()`；否定拆分方案、改为 unlink 后立即解锁。v3 全部落实。
- 无 NAK 与遗留争议。

## 合入评估
*likelihood=high*。清晰的自死锁缺陷，带 `Fixes:` 与 stable 标签，patch 1 带 Andrea Righi Acked-by，v3 完整落实 Tejun 评审且 selftest 规范，无阻塞项。*blocking_issues*：无。*next_action*：待 Tejun 收入 sched_ext 修复分支并回合 stable v7.1+。

## 效果评估
selftest（patch 2）描述：未修复内核上首个被消费的任务在 `ops.dequeue()` 迭代源 DSQ 时自死锁、watchdog 无法恢复（「wedges the system」）；修复内核上调度器干净运行、测试以 SCX_EXIT_UNREG 通过。属正确性验证，无性能量化数据。

## 我可以参与的点
- kind=testing：在修复前后内核分别跑 `dequeue_iter` selftest，确认未修复触发 UEI/死锁、修复后通过。
- kind=review：核对「unlink 后立即解锁」与 `SCX_TASK_IN_CUSTODY` 清除的并发正确性，确认没有任务在解锁窗口内被并发消费。

## 参考链接
- v3 cover：https://lore.kernel.org/all/20260916070753.3343113-1-fangqiurong@kylinos.cn/
- Tejun v2 评审：https://lore.kernel.org/all/e69a808d40739510ffa7d2c7f053a9e8@kernel.org/
