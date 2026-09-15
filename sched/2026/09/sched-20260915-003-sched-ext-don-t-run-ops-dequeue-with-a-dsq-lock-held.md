# sched_ext: Don't run ops.dequeue() with a DSQ lock held

## TL;DR
Qiurong Fang v2：`ops.dequeue()` 在 consume、move、terminal insert 三条路径上都是在 DSQ 锁仍被持有的状态下被调用，任何从 `ops.dequeue()` 回锁同一 DSQ 的 BPF 调度器（例如用 `bpf_iter_scx_dsq` 迭代，每步都要拿 DSQ 锁）都会自死锁。修复把这三次调用移到 DSQ 解锁之后。patch 1 带 Andrea Righi 的 Acked-by，v2 新增了 selftest。合入概率高。

## 背景与问题
`ops.dequeue()` 目前在三个路径上带着 DSQ 锁被调用：consume 与 move 路径（`scx_consume_dispatch_q()`、`move_task_between_dsqs()`）持源 user DSQ 锁；terminal insert 路径（`scx_dispatch_enqueue()`）持终端 global/bypass DSQ 锁。若 BPF 调度器在 `ops.dequeue()` 里锁同一个 DSQ——典型如用 `bpf_iter_scx_dsq` 迭代它（每步拿 DSQ 锁）——就会与本身路径自死锁，直到 watchdog 触发。

## 技术方案
在三条路径上把 `ops.dequeue()` 的调用移到 DSQ 解锁之后。`SCX_TASK_IN_CUSTODY` 在锁内清除，保证回调恰好被调用一次；该回调不再与任务消费排序，可能在任务被移动到/从终端 DSQ 消费之后才执行。文档同步说明这一语义（`Documentation/scheduler/sched-ext.rst`）。

## 版本演进与当前进展
- **v1**：提交后经 Andrea Righi 评审。
- **v2**（本日 21:03，`<20260915130334.714388-1-fangqiurong@kylinos.cn>`）：按 Andrea 意见删掉「ops.dequeue() 可能在任务重新进入 custody 后执行」的说法（global/bypass 路径有 `SCX_OPSS_DISPATCHING` 保持、user-DSQ→local 路径有 `@p` 的 rq 锁保持）；新增一个 `ops.dequeue()` 迭代源 user DSQ 的 selftest。patch 1 携带 v1 的 Acked-by。

## Maintainer 意见与讨论焦点
- **Andrea Righi**：对 patch 1 给出 `Acked-by`；v1 时纠正了回调时序的表述（DISPATCHING / rq 锁对 callback 的保持），并要求补 selftest——v2 均已落实。

## 合入评估
likelihood=high。修的是明确的死锁缺陷且带 `Fixes:`（`ebf1ffcc79c4 "sched_ext: Fix ops.dequeue() semantics"`）、已获 sched_ext 维护者 Andrea Righi Acked-by、v2 补了回归 selftest，无遗留争议。blocking_issues：无。next_action：待 Tejun 收入 sched_ext 修复分支。

## 效果评估
patch 2 描述：在未修复内核上跑该 selftest，首个被消费的任务会自死锁该 CPU 直到 watchdog 触发、以 UEI 失败；在修复后内核上调度器干净运行、测试通过。无性能量化数据，属死锁修复的正确性验证。

## 我可以参与的点
- kind=testing：在带/不带该修复的内核上分别跑 `dequeue_iter` selftest，确认未修复内核触发 UEI、修复内核通过，验证死锁复现路径。
- kind=review：核对 `SCX_TASK_IN_CUSTODY` 在锁内清除后「恰好一次调用」的并发正确性是否有遗漏路径。

## 参考链接
- v2 cover：https://lore.kernel.org/all/20260915130334.714388-1-fangqiurong@kylinos.cn/
- v1 评审链接（cover 引用）：https://lore.kernel.org/all/aqkQ1MtqtqnS0wUs@gpd4/

---
id: sched-20260915-003
date: '2026-09-15'
subject: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260915130334.714388-1-fangqiurong@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260915130334.714388-1-fangqiurong@kylinos.cn/'
authors:
  - 'Qiurong Fang'
maintainers_involved:
  - 'Andrea Righi'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260915130334.714388-1-fangqiurong@kylinos.cn>'
    date: '2026-09-15'
    summary: '三条路径把 ops.dequeue() 调用移到 DSQ 解锁之后；新增迭代源 DSQ 的 selftest'
    review_outcome: 'patch 1 带 Andrea Righi Acked-by'
upstream_commit: null
fixes_commit: 'ebf1ffcc79c4'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '待 Tejun 收入 sched_ext 修复分支'
contribution_opportunities:
  - kind: testing
    description: '在带/不带修复的内核分别跑 dequeue_iter selftest，验证死锁复现与修复'
  - kind: review
    description: '核对 SCX_TASK_IN_CUSTODY 锁内清除后回调恰好调用一次的并发正确性'
generated_at: '2026-09-16T01:05:00'
source_email_count: 3
related_articles: []
tags:
  - sched_ext
  - hang
---