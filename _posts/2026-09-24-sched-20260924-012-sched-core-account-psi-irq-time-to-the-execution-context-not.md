---
id: sched-20260924-012
date: '2026-09-24'
subject: 'sched/core: Account PSI IRQ time to the execution context, not the scheduling
  context'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260918132915.1236312-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
authors:
- Zhan Xusheng
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
current_version: v1
patch_series:
- version: v1
  msgid: <20260918132915.1236312-1-zhanxusheng@xiaomi.com>
  date: '2026-09-18'
  summary: PSI IRQ 时间计入执行上下文（sched_tick 改传 rq->curr）
  review_outcome: 已合入 tip/sched/urgent
upstream_commit: a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3
fixes_commit: af0c8b2bf67b
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 拉取进 mainline 及可能的 stable 回合
contribution_opportunities: []
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles:
- sched-20260922-014
- sched-20260919-005
- sched-20260918-018
tags:
- psi
- cfs
title: 'sched/core: Account PSI IRQ time to the execution context, not the scheduling
  context'
layout: article
---

## TL;DR
- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-018-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260918-018</a> / <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-005-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260919-005</a> / <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-014-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260922-014</a>：Zhan Xusheng 的「把 PSI IRQ 时间计入执行上下文」补丁，与 Peter Zijlstra 多轮往返后被确认合入。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-012-sched-core-account-psi-irq-time-to-the-execution-context-not.html">sched-20260924-012</a>（今天，合并确认）：tip-bot2 发出正式合入通知——该补丁已进 tip 的 `sched/urgent` 分支，提交 `a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3`，作者 Zhan Xusheng，committer Ingo Molnar，同时带 Peter 与 Zhan 的 Signed-off-by。系列以 merged 落地，本次增量补齐了此前缺失的正式 commit hash。

## 背景与问题
- 背景见 <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-005-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260919-005</a>：`psi_account_irqtime()` 有两个共享 `rq->psi_irq_time` 的调用方，但它们对「上下文」的理解不一致——`__schedule()` 传 outgoing `rq->curr`，`sched_tick()` 传 `rq->donor`。proxy execution 下 donor 阻塞在 mutex 上、`rq->curr` 在烧 CPU。
- 提交正文：tick 把 PSI_IRQ_FULL 记到 donor 的 cgroup 并推进时间戳，`__schedule()` 随后发现 delta <= 0、什么都没记——PSI 时间没被重复计数，却落到了**错误的 cgroup**。

## 技术方案
- 见 <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-005-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260919-005</a>。提交正文明确：改传 `rq->curr`（这正是 commit `af0c8b2bf67b` "sched: Split scheduler and execution contexts" 把 `curr` 改名为 `donor` 之前、`sched_tick()` 一处调用方原本读的值）。无 `CONFIG_SCHED_PROXY_EXEC` 时两个 rq 成员是 union，因此该改动只在启用该选项时生效，且依赖 EXPERT。
- 本日 `sched_tick()` 里 `psi_account_irqtime(rq, donor, NULL)` → `psi_account_irqtime(rq, curr, NULL)`（kernel/sched/core.c，1 行）。

## 版本演进与当前进展
- 提交 `a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3`（AuthorDate 09-18，CommitterDate 09-24）已进 `tip/sched/urgent`。`Fixes: af0c8b2bf67b`。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（Intel）** 在提交中署名 Signed-off-by（此前经 `In it goes` 确认合入，见 <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-014-sched-core-account-psi-irq-time-to-the-execution-context.html">sched-20260922-014</a>）；**Ingo Molnar** 为 committer。无争议，系列已收尾。

## 合入评估
*likelihood=merged*。已正式进 tip 的 `sched/urgent` 分支，提交 `a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3`。*blocking_issues*：无。*next_action*：随 sched/urgent 拉取进 mainline（及可能的 stable 回合）。

## 效果评估
无性能数据；正确性修复——恢复 PSI IRQ 时间到正确执行上下文，避免 proxy execution 下 PSI 时间被记入错误的 cgroup。

## 我可以参与的点
当前阶段暂无明显参与空间——已合并进 tip/sched/urgent，可持续观察其进入 mainline 与 stable 的节奏。

## 参考链接
- lore (补丁): https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
- tip commit: https://git.kernel.org/tip/a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3
