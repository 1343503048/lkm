---
id: sched-20261029-011
date: 2026-10-29
subject: 'sched: Split preempt-count bookkeeping from raw updates'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261028033127.82193-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20261028033127.82193-1-kmehltretter@gmail.com/
authors:
- Karl Mehltretter
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261028033127.82193-1-kmehltretter@gmail.com>
  date: 2026-10-28
  summary: 13 片 RFC：hardirq entry/return 的 preempt count raw 更新与 debug/tracing 记账分离
  review_outcome: Peter Zijlstra 评 3/13：noinstr 里的 WARN 是 fine 的，tracing 要搬但搬法太丑，建议顺带修
    preempt_notrace 的 bound 检查缺口
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - noinstr 内 WARN 的保留 vs 搬移取舍未定
  - preempt_{en,dis}able_notrace() 的 bound 检查缺口被点名要先修
  - 重构形态需作者按 Peter 意见重做
  next_action: 作者收敛 WARN 处理、以 preempt_notrace 修正为切入口重构后发 v3
contribution_opportunities:
- kind: review
  description: 分析 preempt_en/disable_notrace() 为何跳过 bound 检查，及 noinstr 里 WARN/tracing
    的取舍
- kind: discussion
  description: 就 raw 更新与记账/tracing 的拆分边界（哪些留 noinstr、哪些后置）给出建议
generated_at: '2026-10-30T09:30:00'
source_email_count: 1
related_articles: []
tags:
- preempt
title: 'sched: Split preempt-count bookkeeping from raw updates'
layout: article
---

## TL;DR
Karl Mehltretter 的 13 片 RFC v2 系列（patch 3「Split preempt-count bookkeeping from raw updates」）试图把 preempt count 的**原始更新**与**记账/debug/tracing**拆开：hardirq 最早入口在可插桩的 debug/tracing 代码能跑之前就必须更新 preempt count，因此引入 `irqentry_hardirq_count_start()/finish()/sub_prepare()` 一组 header，在 noinstr 里做 raw 加减、再补 debug 检查与 latency tracing。今日 Peter Zijlstra 审 patch 3，评价「Urgh, so much crazy」：认为 **noinstr 里的 WARN 是「fine」的**（本不该发生，发生了就要 ASAP 打出来，哪怕挂机），tracing 确实要搬走，但「搬的方式不该这么丑」，并提醒这顺带给了修正 `preempt_{en,dis}able_notrace()` 的机会（它们当前跳过 bound 检查）。

## 背景与问题
很早期的 hardirq entry 代码需要在可插桩的 debug/tracing 代码之前更新 preempt count；对称地，hardirq return 需要在 raw teardown 之前完成可插桩的校验与 latency tracing。现有实现把 raw 更新与 debug/tracing 记账混在一条路径里，作者想拆开，使 raw 更新 noinstr 安全、记账/tracing 放回可插桩路径。patch 3 是该目标的一环。

## 技术方案
（据 patch 3 的 commit 描述，被 Peter 引用在回帖里）引入小型 hardirq-entry header：

- `irqentry_hardirq_count_start()`：staging raw 的 `HARDIRQ_OFFSET` 加法，并用一个 opaque cookie 记录「是否确实加了」；`DEBUG_PREEMPT` 且无 separate reschedule bits 时，把已为负的 count 走一个 noinstr slow helper，保留既有 `DEBUG_LOCKS_WARN_ON()` oops 短路。
- `irqentry_hardirq_count_finish()`：上报被拒绝的加法，或完成 post-add 的 debug 检查与 latency tracing。
- `irqentry_hardirq_count_sub_prepare()`：在做 raw 减法前完成校验与 tracing。
- 保持 `preempt_count_add()`/`preempt_count_sub()` 行为与顺序不变；start/stop helper 强制 inline（trace provenance 依赖其栈帧）；latency tracing 留在各调用路径以保 `CALLER_ADDR0` 识别调用者。

Peter 的修正意见：① noinstr 里的 WARN 无需搬走——「WARN in noinstr code are fine」；② tracing 确实要搬，但当前的搬法「should not be this ugly」；③ 顺带把 `preempt_{en,dis}able_notrace()` 修掉（它们现在跳过 bound 检查）。

## 版本演进与当前进展
*current_version: v2 (RFC)*（2026-10-28，cover `<20261028033127.82193-1-kmehltretter@gmail.com>`；当日无缓存，今日由 Peter 的 review 反推）。今日 Peter 对 patch 3 给出结构性反馈（「重构方式太丑，应先修 preempt_notrace 的 bound 检查缺口」），暂无 v3 或作者回应。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（维护者）**：明确「noinstr 里的 WARN 是 OK 的（不该发生，发生了要 ASAP 打出来、挂机也没关系，参见 x86 `asm/bug.h` 的 `instrumentation_{begin,end}()`）」，即作者「把 WARN 从 noinstr 搬走」的动机需要收敛；认可 tracing 要搬，但当前机械搬法「ugly」；并给出具体附带收益——`preempt_{en,dis}able_notrace()` 目前跳过 bound 检查，应趁重构一并修掉。
- 未解决焦点：noinstr 中 debug 校验（WARN 路径）到底留多少在 noinstr、tracing 用什么形态搬出，作者尚未回应。

## 合入评估
*likelihood=low*。RFC 尚在早期，Peter 对 patch 3 的结构性不满（「ugly」）意味着需要重构；方向（raw 更新与记账分离）本身未被否定，但形态要变。*blocking_issues*：noinstr 内 WARN 的保留 vs 搬移取舍未定；`preempt_{en,dis}able_notrace()` 的 bound 检查缺口被点名要先修；重构形态需作者重做。*next_action*：作者按 Peter 意见收敛 WARN 处理、用 `preempt_notrace` 修正作为切入口重构后发 v3。

## 效果评估
无性能数据。该系列是 preempt count 记账的 noinstr 安全化重构，正确性/可维护性导向；Peter 的反馈不涉及 benchmark。

## 我可以参与的点
- **review**：分析 `preempt_{en,dis}able_notrace()` 当前为何跳过 bound 检查（Peter 点名的缺口），以及 noinstr 里 WARN 与 tracing 的取舍，帮作者收敛方案。
- **discussion**：就「raw 更新与 debug/tracing 记账的拆分边界」给出建议（哪些必须留 noinstr、哪些应后置）。

## 参考链接
- lore thread（RFC v2 cover）: https://lore.kernel.org/all/20261028033127.82193-1-kmehltretter@gmail.com/
- Peter Zijlstra 对 3/13 的 review: https://lore.kernel.org/all/20261029093219.GH1779021@noisy.programming.kicks-ass.net/
