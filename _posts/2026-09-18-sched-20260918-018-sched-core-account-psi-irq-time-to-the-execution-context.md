---
id: sched-20260918-018
date: '2026-09-18'
subject: 'sched/core: Account PSI IRQ time to the execution context'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260918132915.1236312-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260918132915.1236312-1-zhanxusheng@xiaomi.com>
  date: '2026-09-18'
  summary: sched_tick 改传 rq->curr 给 psi_account_irqtime
  review_outcome: 本日无回复
upstream_commit: null
fixes_commit: af0c8b2bf67b
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待维护者 review；可补充 donor/curr 区分用例
contribution_opportunities:
- kind: testing
  description: 构造 donor 阻塞而 curr 烧 CPU 的用例验证 PSI 记账
- kind: review
  description: 排查 proxy 路径其他 donor/curr 口径不一致的记账点
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
- psi
- proxy_execution
title: 'sched/core: Account PSI IRQ time to the execution context'
layout: article
---

## TL;DR
Zhan Xusheng 提交修复：proxy execution 下 `sched_tick()` 把 PSI IRQ 时间记到 `rq->donor`，而 `__schedule()` 记到 `rq->curr`，二者不一致导致 IRQ 时间被记到错误的 cgroup。修复是让 `sched_tick()` 改传 `rq->curr`（恢复 split 之前的语义）。仅影响 `CONFIG_SCHED_PROXY_EXEC=y`（依赖 EXPERT）的配置。

## 背景与问题
`psi_account_irqtime()` 有两个调用者共享 `rq->psi_irq_time`，却对"上下文"口径不一致：`__schedule()` 传的是出站的 `rq->curr`，`sched_tick()` 传的却是 `rq->donor`。proxy execution 下 donor 阻塞在 mutex 上、而 `rq->curr` 真正烧 CPU：此时 tick 把 `PSI_IRQ_FULL` 记到 donor 的 cgroup 并推进时间戳，随后 `__schedule()` 发现 delta<=0 什么都不记——delta 没有重复计算，却落到了错误的 cgroup。

## 技术方案
`kernel/sched/core.c` 中 `sched_tick()` 将 `psi_account_irqtime(rq, donor, NULL)` 改为 `psi_account_irqtime(rq, curr, NULL)`，即恢复 commit af0c8b2bf67b（"sched: Split scheduler and execution contexts"）之前读到 `rq->curr` 的语义。未开启 `CONFIG_SCHED_PROXY_EXEC` 时 rq->curr 与 rq->donor 是 union，故行为不变；仅在该选项（依赖 EXPERT）开启时有差异。

## 版本演进与当前进展
- v1（09-18，`<20260918132915.1236312-1-zhanxusheng@xiaomi.com>`）：首版，本日无回复。

## Maintainer 意见与讨论焦点
- 本日无维护者回复。作者自述：已在 x86_64 + `CONFIG_SCHED_PROXY_EXEC=y` + PSI + IRQ_TIME_ACCOUNTING 下构建并启动，但**没能构造出 donor 与 curr 分属不同 cgroup 的用例**——即修复的主观正确性（基于语义推理）尚未用实际场景验证。

## 合入评估
*likelihood=medium*。1 行改动、口径清晰、带 Fixes，且方向与 split 前的既有语义一致；但作者未构造出复现场景，可能影响维护者确认。*blocking_issues*：暂无阻塞；缺实际复现/验证用例。*next_action*：等待维护者 review；可补充一个能区分 donor/curr 的 PSI 计量用例。

## 效果评估
无性能数据。作者声明未构造 donor 与 curr 不同的场景，修复正确性基于代码语义推理（"作者主观判断，未见测试数据"）。

## 我可以参与的点
- kind=testing：构造一个 proxy execution 下 donor 阻塞而 curr 烧 CPU 的用例，验证 PSI IRQ 时间是否记入正确 cgroup（作者明确缺此验证）。
- kind=review：审查 proxy execution 路径中其他"donor vs curr"口径不一致的记账点（本修复提示可能存在同类问题）。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
