# sched_ext: Fix missing ops.dequeue() on remote local DSQ moves

> **subject**：`sched_ext: Fix missing ops.dequeue() on remote local DSQ moves`

## TL;DR

Kuba Piecuch 的 sched_ext 修复：自 ebf1ccff79c4（"sched_ext: Fix ops.dequeue() semantics"）后，任务被迁到**另一 CPU 的 local DSQ**（SCX_DSQ_LOCAL_ON 派发、scx_bpf_dsq_move_to_local() 等）时，`ops.dequeue()` 不会在插入目标 DSQ 时被调用，而是推迟到任务被 pick 时以 `SCX_DEQ_CORE_SCHED_EXEC` 报告——语义被破坏，BPF 调度器可能拿到错误的 dequeue 回调。根因是 b75aaea24c9f 之后 `enqueue_task_scx()` 在插入**之后**才清 `p->scx.sticky_cpu`，导致 `task_leave_custody()` 跳过退出。补丁把 `sticky_cpu` 在读入局部变量后立即清零（等效 revert b75aaea24c9f 的 enqueue 侧）。当天从 v1 一路迭代到 v3（v1 3 补丁 → v2 重排为 fix 优先 + 测试 → v3 加固测试），Andrea Righi 已给 `Reviewed-by`，Tejun Heo 表示「fix looks good」，带 `Fixes:` 与 `Cc: stable # 7.1.x`。合入可能性高。

## 背景与问题

commit ebf1ccff79c4 确立了「每个进入 BPF 调度器 custody 的任务在离开时恰好得到一次 `ops.dequeue()`，派发到 terminal DSQ 时以无 flag 的 `ops.dequeue()` 结束 custody」的语义。但当任务被移到**非其所在 rq 对应 CPU** 的 local DSQ 时，这条语义被打破：`move_remote_task_to_local_dsq()` 设 `p->scx.sticky_cpu` 标记内部迁移，而 `enqueue_task_scx()` 在插入目标 local DSQ 之后才清掉它，`task_leave_custody()` 因此在插入时跳过了 custody 退出。

结果是任务带着 `SCX_TASK_IN_CUSTODY` 仍置位地坐在 local DSQ 上，BPF 调度器只会在两种延迟时刻才被告知：被 pick 时收到 `ops.dequeue(SCX_DEQ_CORE_SCHED_EXEC)`（即便并未发生 core scheduling），或属性变更时收到 `ops.dequeue(SCX_DEQ_SCHED_CHANGE)`（针对已离开 custody 的任务）。现有的 dequeue selftest 未察觉，因为它把迟到的 `SCX_DEQ_CORE_SCHED_EXEC` 当成普通派发 dequeue 处理，且它仍先于 `ops.running()` 到达。

## 技术方案

补丁 2（修复）把 `p->scx.sticky_cpu` 在读入局部变量 `sticky_cpu` 之后立即清为 -1，使 SCX 内部迁移在任务抵达目标 rq 时即告结束；路由决策仍用局部副本，源侧（`deactivate_task()` 期间）不受影响。这样 `ops.dequeue()` 在目标 rq 插入 local DSQ 时即被调用，与 same-rq 派发一致，实质上是 revert 了 b75aaea24c9f 的 enqueue 侧。

配套测试 `dequeue_remote`：把「任务从 BPF 队列用 `SCX_DSQ_LOCAL_ON|cpu` 派发」与「任务在 user DSQ 上被 `scx_bpf_dsq_move_to_local()` 消费」两种跨 CPU 移动路径都做成常见情形，BPF 调度器跟踪每个任务的 custody 状态，在出现迟到 `SCX_DEQ_CORE_SCHED_EXEC`、任务未先经 `ops.dequeue()` 就运行、或 `ops.enqueue()`/`ops.dequeue()` 不配对时触发 `scx_bpf_error()`。因 core scheduling 可以合法地直接从 custody pick 任务，v2 起改为检查 `p->core_cookie` 而非整体跳过。

## 版本演进与当前进展

- **v1**（`<20260929161730.185271-1-jpiecuch@google.com>`）：3 补丁（1/3 测试、2/3 修复、3/3 启用测试）。
- **v2**（`<20260930114725.331370-1-jpiecuch@google.com>`）：按 Tejun/Andrea 意见重排为 fix 优先 + 测试（并入 Makefile 条目）；修复改为「读入后立即清 sticky_cpu」；补 7.1.y 前置依赖 18d62044cda7 说明；测试改为检查 `p->core_cookie`、用 `sched_getaffinity()` 数 CPU、pop 过陈旧队列项、逐场景重置计数、错误路径回收 worker；描述去重。获 Andrea `Reviewed-by`。
- **v3**（`<20260930142412.552765-1-jpiecuch@google.com>`）：按 Andrea 意见加固测试——`ops.dispatch()` 弹尽但队列非空时 kick 该 CPU、`ops.init_task()` 重置 `enqueue_seq`、每场景前清空 exit record。保留 Andrea `Reviewed-by`。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：「The fix looks good to me. It effectively reverts the enqueue_task_scx() half of b75aaea24c9f」，并请 Andrea 确认；同时给出一系列意见——1/3 无法单独构建运行（应 fix 在前）、7.1.y 需注明 18d62044cda7 前置、`scx_resolve_local_dsq()` 可能把任务导向 reject/rescue DSQ（注释里「local DSQ」不准确）、`sched_core_find()` 只返回带 core cookie 的任务（检查 `p->core_cookie` 更精确）、`_SC_NPROCESSORS_ONLN` 忽略 affinity（改用 `sched_getaffinity()`+`CPU_COUNT()`）等。
- **Andrea Righi**（sched_ext 维护者）：确认源侧 sticky_cpu 赋值跨 `deactivate_task()` 保留、修复方向正确；建议「读入局部变量后立即清」以覆盖 `SCX_TASK_QUEUED` 提前退出路径（v2 采纳）；在 v2、v3 均给 `Reviewed-by`。
- 无 NAK；作者对全部意见均逐条落地。

## 合入评估

*likelihood=high*。真实 bug 修复、带 `Fixes: ebf1ccff79c4` 与 `Cc: stable # 7.1.x`，两位维护者已明确认可（Tejun「looks good」、Andrea 两次 `Reviewed-by`），作者当天三轮快速收敛。*blocking_issues*：无实质性未决争议，主要剩 Tejun 收取（for-7.3-fixes / for-next）。*next_action*：由 Tejun 收进 `sched_ext/for-7.3-fixes` 并顺延 for-next（cover 说明 for-next 仅有 selftests Makefile 的 trivial 冲突）。

## 效果评估

测试数据齐全：无修复时 `dequeue_remote` 30/30 全失败、全套 selftest 为 31 通过/1 跳过/1 失败；加修复后 30/30 全通过，每轮约 140k 次 custody enqueue 且约 90k 次任务最终跑到非 enqueue CPU，全套 32 通过/1 跳过/0 失败；runner 与 worker 共享 core cookie 时也 10/10 通过（此时合法 core-sched pick 确实发生）。测试环境为 x86_64 virtme-ng、4 vCPU（2 核×2 线程）、`CONFIG_SCHED_CORE=y`。

## 我可以参与的点

- `testing`：在带 core scheduling cookie 的真实混合负载（尤其同时使用 `scx_bpf_dsq_move*()` 的场景）下验证 v3 无 regressions，回帖补 `Tested-by`。
- `review`：核对 7.1.y 前置依赖 18d62044cda7 是否已进入对应 stable 分支，避免 stable 回合时漏依赖（作者已在 stable tag 中注明）。

## 参考链接

- lore（v3 cover）: https://lore.kernel.org/all/20260930142412.552765-1-jpiecuch@google.com/
- lore（v2 cover）: https://lore.kernel.org/all/20260930114725.331370-1-jpiecuch@google.com/
- lore（v1 cover）: https://lore.kernel.org/all/20260929161730.185271-1-jpiecuch@google.com/
- Tejun 的 review: https://lore.kernel.org/all/46f4b66249f016b675fa16446b2f2f99@kernel.org/

---
id: sched-20260930-001
date: '2026-09-30'
subject: 'sched_ext: Fix missing ops.dequeue() on remote local DSQ moves'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260930142412.552765-1-jpiecuch@google.com>'
lore_url: 'https://lore.kernel.org/all/20260930142412.552765-1-jpiecuch@google.com/'
authors:
  - 'Kuba Piecuch'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v3
patch_series:
  - version: v1
    msgid: '<20260929161730.185271-1-jpiecuch@google.com>'
    date: '2026-09-30'
    summary: '3 补丁：dequeue_remote 测试 + 清 sticky_cpu 修复 + 启用测试'
    review_outcome: 'Tejun 逐条 review，要求 fix 在前、注 7.1.y 前置、检查 core_cookie 等'
  - version: v2
    msgid: '<20260930114725.331370-1-jpiecuch@google.com>'
    date: '2026-09-30'
    summary: '重排 fix 优先+测试合并；修复改为读入后立即清 sticky_cpu；补 7.1.y 前置说明；测试加固'
    review_outcome: 'Andrea 给 Reviewed-by，仅剩少量非阻塞 nit'
  - version: v3
    msgid: '<20260930142412.552765-1-jpiecuch@google.com>'
    date: '2026-09-30'
    summary: '测试进一步加固：弹尽重踢 CPU、重置 enqueue_seq、清 exit record'
    review_outcome: '保留 Andrea Reviewed-by；待 Tejun 收取'
upstream_commit: null
fixes_commit: 'ebf1ccff79c4'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '待 Tejun 收取进 sched_ext/for-7.3-fixes（并顺延 for-next）'
  next_action: 'Tejun 应用进 for-7.3-fixes，注意 for-next 的 selftests Makefile trivial 冲突'
contribution_opportunities:
  - kind: testing
    description: '在带 core scheduling cookie 的混合负载下验证 v3 无回归，回帖补 Tested-by'
  - kind: review
    description: '核对 7.1.y 前置依赖 18d62044cda7 是否已进入对应 stable 分支'
generated_at: '2026-10-01T01:00:00'
source_email_count: 19
related_articles: []
tags:
  - sched_ext
---
