---
id: sched-20261110-005
date: '2026-11-10'
subject: 'sched_ext: make DSQ iterator stay drained after NULL'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
lore_url: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
authors:
- Kang Chen
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
  date: '2026-11-10'
  summary: 在游标 flag 记住 DRAINED 状态，next() 返回 NULL 后持续返回 NULL
  review_outcome: 当日无评审回复
upstream_commit: null
fixes_commit: 650ba21b131e
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 新增 flag 位 1U<<28 与既有迭代 flag 掩码无冲突待复核
  next_action: Tejun 评审后收取到 sched_ext 分支
contribution_opportunities:
- kind: review
  description: 核对 1U<<28 与 HAS_REENQ/HAS_SLICE/HAS_VTIME 及 ALL_FLAGS 掩码的位冲突
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: make DSQ iterator stay drained after NULL'
layout: article
---

## TL;DR

Kang Chen 修 sched_ext DSQ 迭代器的一个 verifier 契约违约：`bpf_iter_scx_dsq_next()` 走到队列末尾时 `nldsq_cursor_next_task()` 会把迭代游标从链表摘除，下一次调用见到 `list_empty(&cursor->node)` 就从 DSQ 头重新开始、返回同一轮迭代的第一个任务。而 verifier 依赖「next() 一旦返回 NULL 就持续返回 NULL」的契约（`process_iter_next_call()` 把迭代器标记为 DRAINED、把后续调用结果当常量 0），于是重启的迭代会把任务指针交给 BPF 程序、verifier 却认为 R0==0。修复在游标 flag 里记住 drained 状态，此后 next() 永远返回 NULL。单补丁，`Fixes: 650ba21b131e ("sched_ext: Implement DSQ iterator")`。

## 背景与问题

sched_ext 的 DSQ 迭代器给 BPF 调度器提供遍历 dispatch queue 的 kfunc。迭代契约要求 next() 在返回一次 NULL 后保持返回 NULL，这是 BPF verifier 对迭代器的假设：`process_iter_next_call()` 一旦看到 NULL 就把迭代器置为 DRAINED，并把后续 next() 调用的返回值当作常量 0 来处理。但 `nldsq_cursor_next_task()` 在到达队列尾时会 unlink 游标，导致下一次调用 `list_empty(&cursor->node)` 为真、从 DSQ 头重新遍历——返回「同一轮迭代的第一个任务」。这会让 BPF 程序拿到真实任务指针，而 verifier 仍以为 R0==0，构成 verifier 与运行时语义的分裂（潜在的类型/指针正确性问题）。

## 技术方案

在游标 flag 里新增 `__SCX_DSQ_ITER_DRAINED`（用游标空闲的高位 bit，`1U << 28`），`bpf_iter_scx_dsq_next()` 开头检查 `kit->dsq` 为 NULL **或** drained 标志则直接返回 NULL；遍历返回 `p == NULL` 时置上该标志。游标有富余 flag 位，且 BPF 可见的迭代器布局不变。改动 `kernel/sched/ext/ext.c` +15/-2。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261110125113.2935742-1-k.chen@smail.nju.edu.cn>`）*。单补丁首版，当日无评审回复。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。补丁带 `Fixes:`、触及 verifier 契约，属明确正确性修复，无 NAK。

## 合入评估

*likelihood=medium*。修复逻辑清晰、`Fixes:` 齐全、改动小，适合 Tejun 直接收取；但尚无评审。*blocking_issues*：① 需确认新增 flag 位 `1U<<28` 与既有 `__SCX_DSQ_ITER_USER_FLAGS` 等掩码无冲突（作者声称布局不变，评审需复核）。*next_action*：Tejun 评审后收取到 sched_ext 分支。

## 效果评估

无性能数据。价值在 verifier 契约正确性（消除「运行时给真指针、verifier 以为 0」的分裂），cover/正文未给 benchmark。

## 我可以参与的点

- **review**：核对 `__SCX_DSQ_ITER_DRAINED = 1U<<28` 与 `__SCX_DSQ_ITER_HAS_REENQ/HAS_SLICE/HAS_VTIME`（29/30/31 位）以及 `__SCX_DSQ_ITER_ALL_FLAGS` 的组合是否把新位暴露给用户或与其它位冲突。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
