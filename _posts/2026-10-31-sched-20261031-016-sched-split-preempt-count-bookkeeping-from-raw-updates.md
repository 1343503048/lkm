---
id: sched-20261031-016
date: 2026-10-31
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
  review_outcome: Peter Zijlstra 评 3/13；作者确认方向并给 arm64 __always_inline 细节
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - v3 未发出，重构未落地
  - preempt_{en,dis}able_notrace() 的 bound 检查缺口需随重构一并修
  next_action: 作者按确认方向重构后发 v3
contribution_opportunities:
- kind: review
  description: 核对 arm64 上 preempt_count()/should_resched() 加 __always_inline 的副作用
- kind: discussion
  description: 就 noinstr 内 WARN 与 tracing 的最终拆分边界给出建议
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20261029-011
tags:
- preempt
title: 'sched: Split preempt-count bookkeeping from raw updates'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-011-sched-split-preempt-count-bookkeeping-from-raw-updates.html">sched-20261029-011</a>：Karl Mehltretter 的 13 片 RFC v2 系列把 preempt count 的 raw 更新与 debug/tracing 记账分离；Peter Zijlstra 评 patch 3「Urgh, so much crazy」——noinstr 里的 WARN 是 fine 的，tracing 要搬但搬法太丑，建议顺带修 `preempt_{en,dis}able_notrace()` 的 bound 检查缺口。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-016-sched-split-preempt-count-bookkeeping-from-raw-updates.html">sched-20261031-016</a>（今天）：作者回帖认可方向——已核对 `DEBUG_LOCKS_WARN_ON()` 在 noinstr 里没问题，arm64 只需给 `preempt_count()` 和 `should_resched()` 加 `__always_inline` 防 Clang outline，并表示「I will work on that」。

## 背景与问题
（承接）hardirq entry/return 需要在可插桩 debug/tracing 代码之前更新 preempt count；raw 更新与记账/tracing 混在一条路径里。今日为对 Peter 意见的具体响应，无新背景。

## 技术方案
（承接，今日为方向确认 + 细节核对）作者确认三条：

- `DEBUG_LOCKS_WARN_ON()` 在 noinstr 里已经没问题（回应 Peter「WARN in noinstr are fine」）。
- arm64 需要给 `preempt_count()` 与 `should_resched()` 加 `__always_inline`，避免 Clang 将其 outline 到可插桩代码段。
- 将按此方向重构（隐含对 `preempt_{en,dis}able_notrace()` bound 检查缺口的处理）。

## 版本演进与当前进展
*current_version: v2 (RFC)*（2026-10-28）。今日无新版本；作者确认将按 Peter 意见工作（尚未给出 v3 时间）。

## Maintainer 意见与讨论焦点
- **Karl Mehltretter（作者）**：「Yes, that's a good direction.」——完全接受 Peter 的方向，并给出 arm64 的具体前置（`__always_inline` 两处）。
- **Peter Zijlstra（维护者，前一日）**：noinstr 内 WARN 保留、tracing 搬法要更优雅、顺带修 notrace bound 检查。
- 无 NAK；分歧已收敛为「按 Peter 方向重构」，等待 v3。

## 合入评估
*likelihood=low*。RFC 仍早期，重构未落地；但方向已获维护者与作者对齐，阻塞项从「形态分歧」转为「重构工作量」。*blocking_issues*：v3 未发出；`preempt_{en,dis}able_notrace()` 的 bound 检查缺口需随重构一并修。*next_action*：作者按确认方向重构后发 v3。

## 效果评估
无性能数据。该系列为 preempt count 记账的 noinstr 安全化重构，正确性/可维护性导向。

## 我可以参与的点
- **review**：核对 arm64 上 `preempt_count()`/`should_resched()` 加 `__always_inline` 后对其它调用点是否有 ABI/性能副作用。
- **discussion**：就 noinstr 内 debug 校验（WARN）与 tracing 的最终拆分边界给出建议。

## 参考链接
- 作者今日回帖: https://lore.kernel.org/all/auXLfz6mFh_uOvRr@gmail.com/
- RFC v2 cover: https://lore.kernel.org/all/20261028033127.82193-1-kmehltretter@gmail.com/
