---
id: sched-20261111-016
date: '2026-11-11'
subject: 'sched_ext: make DSQ iterator stay drained after NULL'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
lore_url: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
authors:
- Kang Chen
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
  date: '2026-11-10'
  summary: 游标 flag 记 DRAINED 状态，next() 返回 NULL 后持续返回 NULL
  review_outcome: Tejun Heo 已应用
upstream_commit: null
fixes_commit: 650ba21b131e
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 7.4 修复批次进入 mainline
contribution_opportunities: []
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261110-005
tags:
- sched_ext
title: 'sched_ext: make DSQ iterator stay drained after NULL'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-005-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261110-005</a>：Kang Chen 修 sched_ext DSQ 迭代器的一个 verifier 契约违约：`bpf_iter_scx_dsq_next()` 走到队列末尾时游标被从链表摘除，下一次调用见 `list_empty(&cursor->node)` 就从 DSQ 头重新遍历、返回同一轮第一个任务；而 verifier 依赖「next() 返回 NULL 后持续返回 NULL」的契约，重启的迭代会把任务指针交给 BPF 程序、verifier 却认为 R0==0。修复在游标 flag 记 drained 状态。`Fixes: 650ba21b131e`。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-016-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261111-016</a>（今天）：**Tejun Heo 已应用**——「Applied to sched_ext/for-7.4-fixes. Thanks.」，本补丁进入 sched_ext 的 7.4 修复分支。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-005-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261110-005</a>）sched_ext 的 DSQ 迭代器给 BPF 调度器提供遍历 dispatch queue 的 kfunc。迭代契约要求 next() 返回一次 NULL 后保持返回 NULL（verifier 的 `process_iter_next_call()` 一旦见 NULL 就把迭代器置 DRAINED、把后续调用返回值当常量 0）。但 `nldsq_cursor_next_task()` 到队尾会 unlink 游标，下次调用 `list_empty(&cursor->node)` 为真、从 DSQ 头重遍历——BPF 程序拿到真实任务指针而 verifier 仍以为 R0==0，构成 verifier 与运行时语义的分裂。

## 技术方案

游标 flag 新增 `__SCX_DSQ_ITER_DRAINED`（用游标空闲高 bit `1U << 28`），`bpf_iter_scx_dsq_next()` 开头检查 `kit->dsq` 为 NULL 或 drained 位则直接返回 NULL；遍历返回 NULL 时置位。改动 `kernel/sched/ext/ext.c` +15/-2。BPF 可见的迭代器布局不变。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261110125113.2935742-1-k.chen@smail.nju.edu.cn>`）*。今日 Tejun 应用并致谢，无后续版本必要。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：已应用（`sched_ext/for-7.4-fixes`），无异议。

## 合入评估

*likelihood=merged*。已进入 `sched_ext/for-7.4-fixes` 分支。*blocking_issues*：无。*next_action*：随 7.4 修复批次进入 mainline（或相应 stable）。

## 效果评估

本补丁修复 verifier 契约违约（潜在的类型/指针正确性问题），作者未给量化数据。

## 我可以参与的点

当前阶段已合入维护者分支，暂无明显参与空间，可持续观察是否随 7.4 发布进入 mainline。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
- Tejun 应用确认: https://lore.kernel.org/all/9a45ee48b0984bd959becb01d1d11f1c@kernel.org/
