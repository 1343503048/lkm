---
id: sched-20260925-007
date: 2026-09-25
subject: 'sched/eevdf: Ensure that vprot will never go above a min slice'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <179033364613.2819794.18177332963834046075.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033364613.2819794.18177332963834046075.tip-bot2@tip-bot2/
upstream_commit: aae2a33ea66299f39252bc1891bb4f05f631255d
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
  msgid: <20260921152238.3804392-2-vincent.guittot@linaro.org>
  date: 2026-09-21
  summary: 将 vprot 无条件钳制在 min slice 上界，删除 PREEMPT_SHORT else 分支
  review_outcome: 09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities:
- kind: review
  description: 该 EEVDF 短切片系列其余 5 枚尚未全部合入，可关注后续版本并跟进评审
source_email_count: 1
related_articles:
- sched-20260922-011
- sched-20260921-001
tags:
- eevdf
- cfs
title: 'sched/eevdf: Ensure that vprot will never go above a min slice'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-011-improving-latency-of-short-slice-tasks.html">sched-20260922-011</a> / <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>（Vincent Guittot 的「Improving latency of short slice tasks」8 补丁 EEVDF 短切片延迟改进系列）。本枚已被 Peter Zijlstra 合入 tip/sched/core（commit aae2a33ea66299f39252bc1891bb4f05f631255d，09-25 12:45:58 +0200），与 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-008-sched-eevdf-align-update-protect-slice-to-set-protect-slice.html">sched-20260925-008</a>、<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-009-sched-eevdf-handle-more-short-slice-waking-cases.html">sched-20260925-009</a> 同批合入该系列的 3 枚。

## 背景与问题

EEVDF 的 protect slice（保护当前任务的切片，避免短任务频繁互相抢占）在 `set_protect_slice()` 里计算 `vprot` 时存在一个边界：`ineligible_vruntime()` 可能落在超过一个 min slice 时长的位置，但我们希望保证当前任务最多只多跑一个 min slice，而不是跟着 ineligible_vruntime 无限拉长。

## 技术方案

把 `vprot = min_vruntime(vprot, se->vruntime + calc_delta_fair(slice, se))` 提到 `if (slice != se->slice)` 判断之外、无条件执行，删除原 `else` 分支里只在 `!sched_feat(PREEMPT_SHORT)` 时才做的同一赋值。这样无论 PREEMPT_SHORT 开关如何，vprot 都被钳制在「一个 min slice 之后」的上界。合入版本 diffstat：kernel/sched/fair.c 共 1 insertion(+), 2 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-21，`<20260921152238.3804392-2-vincent.guittot@linaro.org>`）：本枚为系列 2/8。
- 09-25：Peter 合入 tip/sched/core（Commit-ID aae2a33ea66299f39252bc1891bb4f05f631255d）。

## Maintainer 意见与讨论焦点

系列整体在 v1 阶段由 Peter 提出过若干意见（4/8 衰减算法、5/8 idle 重置、6/8 缓存位置、8/8 扫描去重，见 <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-011-improving-latency-of-short-slice-tasks.html">sched-20260922-011</a>）；本枚为切片保护上界钳制的确定性修正，Peter 作为 committer 收取，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit aae2a33ea66299f39252bc1891bb4f05f631255d。*blocking_issues* 无。

## 效果评估

合入邮件未附 benchmark；修正保证短任务最多多跑一个 min slice 的确定性行为，属静态可证。暂无效果数据。

## 我可以参与的点

修复已合入，无代码参与空间；该系列其余 5 枚（含衰减算法、idle 重置等）尚未全部合入，可关注后续版本（*review*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364613.2819794.18177332963834046075.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/aae2a33ea66299f39252bc1891bb4f05f631255d
- v1 补丁: https://lore.kernel.org/all/20260921152238.3804392-2-vincent.guittot@linaro.org/
