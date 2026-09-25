---
id: sched-20260925-008
date: 2026-09-25
subject: 'sched/eevdf: Align update_protect_slice to set_protect_slice'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <179033364470.2819794.1149607755856219834.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033364470.2819794.1149607755856219834.tip-bot2@tip-bot2/
upstream_commit: 4bf32ec3327d2d2286e96508cd128ce1592f43ce
fixes_commit: null
merged_branch: tip/sched/core
current_version: v1
generated_at: '2026-09-26T01:15:00'
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: <20260921152238.3804392-3-vincent.guittot@linaro.org>
  date: 2026-09-21
  summary: 让 update_protect_slice 应用与 set_protect_slice 相同的逻辑，删除不再成立的 WARN_ON_ONCE(!curr)
  review_outcome: 09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities:
- kind: review
  description: 该 EEVDF 短切片系列其余未合入补丁可继续跟进评审
source_email_count: 1
related_articles:
- sched-20260922-011
- sched-20260921-001
tags:
- eevdf
- cfs
title: 'sched/eevdf: Align update_protect_slice to set_protect_slice'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-011-improving-latency-of-short-slice-tasks.html">sched-20260922-011</a> / <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>（Vincent Guittot 的「Improving latency of short slice tasks」系列）。本枚已被 Peter Zijlstra 合入 tip/sched/core（commit 4bf32ec3327d2d2286e96508cd128ce1592f43ce，09-25 12:45:59 +0200），与 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-007-sched-eevdf-ensure-that-vprot-will-never-go-above-a-min-slic.html">sched-20260925-007</a>、<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-009-sched-eevdf-handle-more-short-slice-waking-cases.html">sched-20260925-009</a> 同批合入。

## 背景与问题

EEVDF 的 protect slice 有两处维护点：初次设置 `set_protect_slice()` 与更新 `update_protect_slice()`。二者此前逻辑不一致；`ineligible_vruntime()` 内部还有一个 `WARN_ON_ONCE(!curr)`——它只能从 `set_next_task_fair(.first=true)` / `set_protect_slice()` 调用，前提是 curr 已设置且 on_rq，但该前提并不总是成立，会导致误报。

## 技术方案

让 `update_protect_slice()` 应用与 `set_protect_slice()` 相同的逻辑；删除 `ineligible_vruntime()` 里不再成立的 `WARN_ON_ONCE(!curr)`（及对应注释）。合入版本 diffstat：kernel/sched/fair.c 共 11 insertions(+), 8 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-21，`<20260921152238.3804392-3-vincent.guittot@linaro.org>`）：本枚为系列 3/8。
- 09-25：Peter 合入 tip/sched/core（Commit-ID 4bf32ec3327d2d2286e96508cd128ce1592f43ce）。

## Maintainer 意见与讨论焦点

无单独针对本枚的争论；系列整体 review 见 <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-011-improving-latency-of-short-slice-tasks.html">sched-20260922-011</a>。Peter Zijlstra 作为 committer 收取，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit 4bf32ec3327d2d2286e96508cd128ce1592f43ce。*blocking_issues* 无。

## 效果评估

合入邮件未附 benchmark；属一致性与误报清理的确定性修正。暂无效果数据。

## 我可以参与的点

修复已合入，无代码参与空间；可关注该系列其余未合入补丁（*review*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364470.2819794.1149607755856219834.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/4bf32ec3327d2d2286e96508cd128ce1592f43ce
- v1 补丁: https://lore.kernel.org/all/20260921152238.3804392-3-vincent.guittot@linaro.org/
