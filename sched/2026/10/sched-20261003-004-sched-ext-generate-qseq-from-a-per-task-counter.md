# sched_ext: Generate qseq from a per-task counter

## TL;DR

Kuba Piecuch（Google）发往 `sched_ext/for-7.3-fixes` 的单补丁正确性修复：`finish_dispatch()` 用 `ops_state` 里的 qseq 判断要 claim 的 QUEUED 实例是否就是 `scx_bpf_dsq_insert()` 当时看到的那个，但 qseq 取自 **rq 级**计数器 `rq->scx.ops_qseq`——不同 rq 计数器独立，任务在 insert 与 finish_dispatch 之间被 `sched_setaffinity()` 迁到另一个 rq 时，新 QUEUED 实例可能拿到与旧实例相同的 qseq，使过期 insert 被错误应用到新实例（破坏「针对陈旧实例的 dispatch 被忽略」的保证）。修法：qseq 改由**任务级**计数器 `p->scx.ops_qseq` 生成（仅 `scx_do_enqueue_task()` 里 rq 锁内更新、无需额外同步、塞进 64 位 `struct sched_ext_entity` 的既有空洞），且永不生成 0。Tejun Heo 当天提出 32 位上的回绕细节（用 QSEQ 字段掩码 wrap、避免移位后变 0），Kuba 确认并于同日发出 **v2** 落实。

## 背景与问题

竞态场景（补丁 commit message 原文）：

```
CPU X                          CPU Z
-----                          -----
                               enqueue p on rq A, qseq = N
ops.dispatch()
  scx_bpf_dsq_insert(p)
    records qseq N
                               sched_setaffinity(p)
                                 dequeue p from rq A
                                 enqueue p on rq B, qseq = N
finish_dispatch(p, N)
  qseq matches, p is claimed
```

claim 本身原子、核心状态不会不一致，但「为上一个 QUEUED 实例发出的 insert」被应用到 BPF 调度器刚通过 `ops.enqueue()` 收到的新实例上——`Fixes: f0e1a0643a59`（"sched_ext: Implement BPF extensible scheduler class"，即 sched_ext 落地主 commit，问题自诞生起存在）。目标分支 `for-7.3-fixes` 说明按 7.3 修复处理。

## 技术方案

- `include/linux/sched/ext.h`：`struct sched_ext_entity` 新增 `u32 ops_qseq`（`/* protected by rq lock */`，占用既有 hole）。
- `kernel/sched/ext/ext.c`：`scx_do_enqueue_task()` 里 `p->scx.ops_qseq` 自增生成 qseq（替代 `rq->scx.ops_qseq`），移除已无用的 rq 级计数器。
- **永不生成 0**：NONE 与 DISPATCHING 态不携带 qseq，对这两种态的 `scx_bpf_dsq_insert()` 记录 0；任务级计数下每个任务首次 QUEUED 都会是 0，会被这类 insert 错误 claim——故跳过 0。
- **v2（Tejun 意见）**：在 QSEQ 字段自身回绕处 wrap，`((p->scx.ops_qseq + 1) & (SCX_OPSS_QSEQ_MASK >> SCX_OPSS_QSEQ_SHIFT)) ?: 1`——32 位上移位会丢计数器高两位，用掩码保证计数器不会达到「移位后为 0」的值。
- 4 文件 +17/−5。

## 版本演进与当前进展

- v1（10-03，`<20261002205242.3820674-1-jpiecuch@google.com>`）：任务级计数器 + 跳过 0。
- Tejun 回帖（同日）：wrap 建议与具体表达式。
- v2（10-03，`<20261003115317.43001-1-jpiecuch@google.com>`）：采纳 wrap；changelog 补「Wrap the counter where the QSEQ field wraps so that it can't reach a value that shifts to 0 on 32bit either」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：唯一意见是 32 位回绕细节，给出可直接采用的表达式。无其他异议。
- 补丁带 `Assisted-by: Claude:claude-opus-5.5`（AI 辅助署名，社区近年接受的做法）。

## 合入评估

*likelihood=high*。单补丁、目标 `for-7.3-fixes`、维护者唯一技术意见已在同日 v2 落实、`Fixes:` 指向 sched_ext 主 commit——只待 Tejun 收取（他是该分支 owner）。*blocking_issues*：v2 尚无收取回帖。*next_action*：Tejun 收取进 `sched_ext/for-7.3-fixes`，回合 stable 时随 7.3.x 流转。

## 效果评估

正确性修复，无 benchmark。竞态演示（commit message 的 CPU X/Z 时序图）即问题证据；修复后跨 rq 迁移不再产生重复 qseq。

## 我可以参与的点

- `testing`：构造 `ops.dispatch()` 期间 `sched_setaffinity()` 迁移的负载（BPF 侧记录 insert 时 qseq 与 finish 时对比），验证 v2 下 stale insert 确被忽略。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261003115317.43001-1-jpiecuch@google.com/
- lore（v1）: https://lore.kernel.org/all/20261002205242.3820674-1-jpiecuch@google.com/
- lore（Tejun 意见）: https://lore.kernel.org/all/86a16fc6ea0a57cea7459ac2ebfdfc1b@kernel.org/

---
id: sched-20261003-004
date: '2026-10-03'
subject: 'sched_ext: Generate qseq from a per-task counter'
subsystem: sched_ext
type: fix
status: under_review
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
    summary: '在 QSEQ 字段回绕处 wrap（采纳 Tejun 表达式）'
    review_outcome: '待 Tejun 收取进 for-7.3-fixes'
upstream_commit: null
fixes_commit: 'f0e1a0643a59'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'v2 尚无 Tejun 收取回帖'
  next_action: 'Tejun 收取进 sched_ext/for-7.3-fixes'
contribution_opportunities:
  - kind: testing
    description: '构造 dispatch 期间 setaffinity 迁移负载，验证 v2 下 stale insert 被忽略'
generated_at: '2026-10-04T01:00:00'
source_email_count: 4
related_articles: []
tags:
  - sched_ext
  - concurrency
---
