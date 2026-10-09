# sched_ext: Generate qseq from a per-task counter

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261003-004：Kuba Piecuch（Google）发往 `sched_ext/for-7.3-fixes` 的单补丁——qseq 从 rq 级计数器改为任务级 `p->scx.ops_qseq`（跨 rq 迁移不再撞号）、永不生成 0；Tejun Heo 当天提出 32 位回绕 wrap 细节，Kuba 同日发 v2 落实。
- sched-20261004-003（今天）：**Tejun 回帖「Applied to sched_ext/for-7.3-fixes」**——合入时补写了 `scx_do_enqueue_task()` 里的注释，并追加 `Cc: stable@vger.kernel.org # v6.12+`（sched_ext 自 6.12 进主线，`Fixes: f0e1a0643a59` 指向其主 commit，stable 回合窗口全开）。v1→v2→合入共两天，review 闭环完整。

## 背景与问题

（承接 sched-20261003-004）`finish_dispatch()` 用 qseq 判断要 claim 的 QUEUED 实例是否 `scx_bpf_dsq_insert()` 当时所见。rq 级计数器下，任务在 insert 与 finish_dispatch 之间被 `sched_setaffinity()` 迁到另一 rq 时新实例可撞上旧 qseq，过期 insert 被错误应用到新实例（破坏「针对陈旧实例的 dispatch 被忽略」保证）。

## 技术方案

（承接 v2）`p->scx.ops_qseq` 任务级计数器（rq 锁内更新、占 64 位 struct 既有 hole）；在 QSEQ 字段自身回绕处 wrap（`(qseq + 1) & (SCX_OPSS_QSEQ_MASK >> SCX_OPSS_QSEQ_SHIFT)) ?: 1`），32 位上也不产生移位后为 0 的值；移除 `rq->scx.ops_qseq`。合入版由 Tejun 补写 `scx_do_enqueue_task()` 注释。

## 版本演进与当前进展

- v1（10-03）→ Tejun wrap 意见 → v2（10-03，`<20261003115317.43001-1-jpiecuch@google.com>`）→ 10-04 Tejun 应用进 `sched_ext/for-7.3-fixes`（回帖 `<a3d7cb12303bcefcf53418bcab5bee26@kernel.org>`），追加 stable Cc（v6.12+）。

## Maintainer 意见与讨论焦点

- Tejun Heo：唯一技术意见（wrap 表达式）已落实；收取时仅做注释补写与 stable 标记，无进一步改动。

## 合入评估

*likelihood=merged*。已应用进 `sched_ext/for-7.3-fixes`（sched_ext 修复分支），随 7.3.x stable 流转；`Cc: stable@vger.kernel.org # v6.12+` 明示回合诉求。*blocking_issues*：无。*next_action*：关注其随 for-7.3-fixes 进主线与 stable 回合进度。

## 效果评估

（承接）正确性修复：竞态由 commit message 时序图论证；无 benchmark。合入未新增数据。

## 我可以参与的点

- （无——已合入；stable 回合由维护者流程处理。）

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261003115317.43001-1-jpiecuch@google.com/
- lore（Tejun applied 回帖）: https://lore.kernel.org/all/a3d7cb12303bcefcf53418bcab5bee26@kernel.org/

---
id: sched-20261004-003
date: '2026-10-04'
subject: 'sched_ext: Generate qseq from a per-task counter'
subsystem: sched_ext
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<20261003115317.43001-1-jpiecuch@google.com>'
lore_url: 'https://lore.kernel.org/all/20261003115317.43001-1-jpiecuch@google.com/'
authors:
  - 'Kuba Piecuch'
maintainers_involved:
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261002205242.3820674-1-jpiecuch@google.com>'
    date: '2026-10-03'
    summary: 'qseq 改任务级计数器，永不生成 0'
    review_outcome: 'Tejun 提出 32 位回绕 wrap 细节'
  - version: v2
    msgid: '<20261003115317.43001-1-jpiecuch@google.com>'
    date: '2026-10-03'
    summary: '在 QSEQ 字段回绕处 wrap'
    review_outcome: '10-04 Tejun 应用进 sched_ext/for-7.3-fixes，加 Cc stable v6.12+'
upstream_commit: null
fixes_commit: 'f0e1a0643a59'
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '随 for-7.3-fixes 进主线与 stable 回合'
contribution_opportunities: []
generated_at: '2026-10-05T01:00:00'
source_email_count: 1
related_articles:
  - sched-20261003-004
tags:
  - sched_ext
  - concurrency
---
