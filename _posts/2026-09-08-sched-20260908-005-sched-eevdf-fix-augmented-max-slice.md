---
id: sched-20260908-005
date: '2026-09-08'
subject: 'sched/eevdf: Fix augmented max_slice'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260907123855.1297976-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/a6fe8f72-256a-4374-a1d4-daaa70ed6882@amd.com/
upstream_commit: null
fixes_commit: 6e3c0a4e1ad1
merged_branch: null
current_version: v1
generated_at: '2026-09-09T00:48:00'
authors:
- Vincent Guittot
maintainers_involved:
- K Prateek Nayak
patch_series:
- version: v1
  msgid: <20260907123855.1297976-1-vincent.guittot@linaro.org>
  date: '2026-09-07'
  summary: '__enqueue_entity() 在 se->min_slice = se->slice 之后补 se->max_slice = se->slice，避免新入队实体携带上次作为树内部节点时的陈旧
    max_slice；+2 行，Fixes: 6e3c0a4e1ad1。'
  review_outcome: '09-08: K Prateek Nayak 无条件给出 Reviewed-by（"Feel free to include"），未要求改动、未附数据；仍无
    Peter Zijlstra 的 Ack 与 tip 收录。'
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚缺 Peter Zijlstra 的 Ack，未见 tip 收取
  - 跨两天仍无任何可观测症状或实测数据，影响 urgent 与常规窗口的定级
  next_action: 维护者收取；建议与同作者的 RB 多字段搬运补丁成对合入，避免只补一个破口
contribution_opportunities:
- kind: testing
  description: 在混合 slice 且频繁 enqueue/dequeue 的负载下用 ftrace 或 /proc/sched_debug 抓 entity_lag()
    钳制值越出理论界的实例并回帖，补上至今缺失的症状证据
- kind: review
  description: 把本补丁与 sched-20260908-004 作为同一不变式的两处破口整体评估，回帖提醒维护者成对收取
- kind: new_patch
  description: 与多字段搬运那条一起回合到 OLK-6.6（该分支 __enqueue_entity() 同样只预置 min_slice），Fixes
    引用自家分支 commit
source_email_count: 1
related_articles:
- sched-20260907-001
- sched-20260908-004
tags:
- eevdf
- cfs
title: 'sched/eevdf: Fix augmented max_slice'
layout: article
---

## TL;DR

本文为增量更新，完整背景与代码分析见 related_articles 中的 sched-20260907-001。09-08 该补丁拿到 K Prateek Nayak 的 `Reviewed-by`，评审面已无异议；同一天作者另发了一条同源的独立补丁 `sched/eevdf: fix rb augmented with multi fields`（本文不覆盖，见 sched-20260908-004），说明他把「增广字段完整性」当成一组缺陷在处理。本补丁本身进度：v1 带 `Fixes`、有 RB，仍等 tip 收取。

## 背景与问题

单行摘要（详见前一篇）：`__enqueue_entity()` 只把 `se->min_slice` 预置成 `se->slice`，漏了同样需要预置的 `se->max_slice`；由于 `rb_add_augmented_cached()` 的 propagate 只重算新节点的祖先、不重算节点自身，实体就会带着上次作为树内部节点时被刷大的 `max_slice` 参与增广，并被 `__max_slice_update()` 继续往上传，最终使 `cfs_rq_max_slice()` 偏大、`entity_lag()` 的钳制上界被放松。补丁 +2 行，`Fixes: 6e3c0a4e1ad1 ("sched/fair: Fix lag clamp")`。

## 技术方案

无变化——本日没有新版本，作者没有因任何意见改代码。方案仍是 `__enqueue_entity()` 里在 `se->min_slice = se->slice;` 之后补 `se->max_slice = se->slice;`。

需要留意的是同作者在 09-08 21:55 发出的那条新补丁：它指出 `_copy`/`_rotate` 两个增广回调同样只搬 `min_vruntime` 而丢掉 `min_slice`/`max_slice`。两条补丁修的是同一个不变式的两个破口（入队预置、树再平衡搬运），彼此不冲突，但**若只回合本补丁，`max_slice` 仍会在旋转/擦除路径上被搬错**。这一点本日邮件里没有人说破。

## 版本演进与当前进展

- 09-07 20:38 Vincent Guittot 发出 v1（`<20260907123855.1297976-1-vincent.guittot@linaro.org>`），`kernel/sched/fair.c | 2 ++`。
- 09-08 10:56 K Prateek Nayak 回帖："Hello Vincent, Feel free to include: Reviewed-by: K Prateek Nayak <kprateek.nayak@amd.com>"。这是本线程唯一一封回帖，全文仅一句致谢加 tag，没有任何技术追问。
- 本日无 v2、无 tip-bot、无 stable。

## Maintainer 意见与讨论焦点

- **K Prateek Nayak（AMD）**：给了无条件 `Reviewed-by`，措辞是 "Feel free to include"——即他没要求作者改任何东西，也没有附测试数据或追问症状。他的意见分量在于：他是 `6e3c0a4e1ad1`（lag clamp）那次的测试者之一，对这段 clamp 逻辑的语义熟悉。
- 未解决的分歧：**依然没有人确认症状**。两天下来，这个线程里没有出现任何一个「实测到 lag 越界/放置异常」的回报，包括给出 RB 的 Prateek 也只签了代码正确性。作者自己也没补数据。
- Peter Zijlstra 本日未在本线程出现（他在另一条 exec-context tick 线程里活跃）。

## 合入评估

`likelihood=high`。带 `Fixes`、2 行纯补漏、来自 fair/EEVDF 维护者、已有一位熟悉该逻辑的评审者签 RB、全文无反对意见——按「评审无异议待收取」的口径归为 high。剩余卡点只有一个：还没有 Peter Zijlstra 的 Ack，也未见 tip 收录。`next_action` 是维护者收取；同作者的 `fix rb augmented with multi fields`（sched-20260908-004）若被认可，两条很可能成对进 `sched/urgent` 或同一个常规提交。

## 效果评估

仍然没有任何效果数据。本日唯一新增的是一个人的签名，不含测试与数字；本补丁从提出到现在（跨两天）都没有 benchmark、没有 bug 复现日志、也没有修复前后对比。前一篇里作为间接佐证引用的 `6e3c0a4e1ad1` 动机（mixed slice workload 下 undue lag clamping）来自主线提交说明，不是本补丁新症状的证据。

## 我可以参与的点

- `testing`：这条已经不需要「找反对意见」，缺的是症状证据。若能在混合 slice + 频繁 enqueue/dequeue 的负载下，用 ftrace 或 `/proc/sched_debug` 抓到 `entity_lag()` 的钳制值越出理论界（`-limit < vlag < limit`）的实例并回帖，能直接决定它是否走 urgent。
- `review`：把本补丁与 sched-20260908-004 作为一个整体看——只合一条会留下另一半破口。值得回帖提醒维护者成对收取，这比再找一个 Ack 更有价值。
- `new_patch`：自家 OLK-6.6 分支同样只预置 `min_slice`（前一篇已确认 `kernel/sched/fair.c` 第 1170 行附近的状态），而 `min_vruntime_update()` 已在算 `max_slice`。回合时与本条 + 多字段搬运那条一起打，`Fixes` 引用 OLK-6.6 自身的 commit。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/
- K Prateek Nayak 的 Reviewed-by: https://lore.kernel.org/all/a6fe8f72-256a-4374-a1d4-daaa70ed6882@amd.com/
- 同日同源补丁（增广多字段搬运）: https://lore.kernel.org/all/20260908135526.2783039-1-vincent.guittot@linaro.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
