# sched_ext: Fix missing ops.dequeue() on remote local DSQ moves

> **subject**：`sched_ext: Fix missing ops.dequeue() on remote local DSQ moves`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260930-001：Kuba Piecuch 的 sched_ext 修复——任务被迁到**另一 CPU 的 local DSQ** 时 `ops.dequeue()` 不在插入目标 DSQ 时被调用，而是推迟到被 pick 时以 `SCX_DEQ_CORE_SCHED_EXEC` 报告；根因是 `enqueue_task_scx()` 在插入之后才清 `p->scx.sticky_cpu`。v3（fix 优先 + 加固测试）已获 Andrea Righi `Reviewed-by`、Tejun Heo「fix looks good」，带 `Fixes: ebf1ccff79c4` 与 `Cc: stable # 7.1.x`。
- sched-20261001-004（今天）：Tejun Heo 回帖「Applied 1-2 to sched_ext/for-7.3-fixes.」——系列前两枚（修复 + 测试）已收取进 `sched_ext/for-7.3-fixes` 分支，等价于合入维护者树，将随 for-7.3-fixes 进入 stable 修复通道。

## 背景与问题

（承接 sched-20260930-001）commit ebf1ccff79c4 确立「每个进入 BPF 调度器 custody 的任务在离开时恰好得到一次 `ops.dequeue()`，派发到 terminal DSQ 时以无 flag 的 dequeue 结束 custody」的语义；但任务被移到非其所在 rq 对应 CPU 的 local DSQ 时（`SCX_DSQ_LOCAL_ON` 派发、`scx_bpf_dsq_move_to_local()` 等），`move_remote_task_to_local_dsq()` 设的 `p->scx.sticky_cpu` 在 `enqueue_task_scx()` 插入之后才被清，`task_leave_custody()` 因此在插入时跳过 custody 退出。任务带着 `SCX_TASK_IN_CUSTODY` 置位坐在 local DSQ 上，BPF 调度器只在被 pick 时收到迟到的 `ops.dequeue(SCX_DEQ_CORE_SCHED_EXEC)`。今天无新背景，事件是收取落地。

## 技术方案

（承接）v3 两补丁：修复把 `p->scx.sticky_cpu` 在读入局部变量后立即清为 -1（等效 revert b75aaea24c9f 的 enqueue 侧），使 `ops.dequeue()` 在目标 rq 插入 local DSQ 时即被调用；配套 `dequeue_remote` 测试跟踪每任务 custody 状态、在迟到 `SCX_DEQ_CORE_SCHED_EXEC`、未先经 dequeue 就运行、或 enqueue/dequeue 不配对时触发 `scx_bpf_error()`。今天无代码变更。

## 版本演进与当前进展

- v1（09-29）→ v2（09-30，重排 fix 优先 + 测试加固，Andrea `Reviewed-by`）→ v3（09-30，测试再加固，保留 R-b）。
- 10-01：Tejun 应用 1-2 到 `sched_ext/for-7.3-fixes`（`<b595d8eb3a1a279a7863bbd2d0cfdee7@kernel.org>`）。系列为 2 补丁时「Applied 1-2」即全量收取。

## Maintainer 意见与讨论焦点

- **Tejun Heo**：「Applied 1-2 to sched_ext/for-7.3-fixes. Thanks.」——收取完成，此前其全部 review 意见（fix 在前、7.1.y 前置 18d62044cda7、core_cookie 检查、sched_getaffinity 数 CPU 等）均已落地。
- **Andrea Righi**：v2/v3 两轮 `Reviewed-by`。
- 无 NAK、无未决争议。

## 合入评估

*likelihood=merged*。Tejun 已把 1-2 应用进 `sched_ext/for-7.3-fixes`，系列收取完成；`Fixes: ebf1ccff79c4` + `Cc: stable # 7.1.x` 意味着后续会向 7.1.x 回合，但 7.1.y 需先合入前置依赖 18d62044cda7（v2 cover 已注明）。*blocking_issues*：无（上游收取已完成）；stable 回合依赖 18d62044cda7 是否已进 7.1.y。*next_action*：跟踪 for-7.3-fixes 进入主线及 stable 回合；可在 7.1.x 上验证。

## 效果评估

本日无新数据。既有测试结果（09-30）：无修复时 `dequeue_remote` 30/30 全失败、全套 selftest 31 通过/1 跳过/1 失败；加修复后 30/30 通过、每轮约 140k 次 custody enqueue 且约 90k 次任务最终跑到非 enqueue CPU、全套 32 通过/1 跳过/0 失败。环境 x86_64 virtme-ng、4 vCPU、`CONFIG_SCHED_CORE=y`。

## 我可以参与的点

- `testing`：在 7.1.x stable 上验证该修复与前置 18d62044cda7 的回合（若 stable 已收），回帖补 `Tested-by`。
- `review`：跟踪 for-7.3-fixes 合入主线后的实际 commit，确认 stable tag 完整。

## 参考链接

- Tejun 的收取通告: https://lore.kernel.org/all/b595d8eb3a1a279a7863bbd2d0cfdee7@kernel.org/
- v3 cover: https://lore.kernel.org/all/20260930142412.552765-1-jpiecuch@google.com/
- Tejun 的 review: https://lore.kernel.org/all/46f4b66249f016b675fa16446b2f2f99@kernel.org/

---
id: sched-20261001-004
date: '2026-10-01'
subject: 'sched_ext: Fix missing ops.dequeue() on remote local DSQ moves'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<20260930142412.552765-1-jpiecuch@google.com>'
lore_url: 'https://lore.kernel.org/all/b595d8eb3a1a279a7863bbd2d0cfdee7@kernel.org/'
authors:
  - 'Kuba Piecuch'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260930142412.552765-1-jpiecuch@google.com>'
    date: '2026-09-30'
    summary: 'fix 优先（读入后立即清 sticky_cpu）+ dequeue_remote 测试加固'
    review_outcome: 'Andrea Reviewed-by；10-01 Tejun 应用 1-2 进 sched_ext/for-7.3-fixes'
upstream_commit: null
fixes_commit: 'ebf1ccff79c4'
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 for-7.3-fixes 进主线与 stable 回合（7.1.y 需前置 18d62044cda7）'
contribution_opportunities:
  - kind: testing
    description: '在 7.1.x stable 上验证修复与前置依赖的回合，回帖补 Tested-by'
  - kind: review
    description: '确认 stable tag 与前置依赖在 7.1.y 的完整性'
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260930-001
tags:
  - sched_ext
---
