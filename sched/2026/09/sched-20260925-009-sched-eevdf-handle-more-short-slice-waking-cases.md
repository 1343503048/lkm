# sched/eevdf: Handle more short slice waking cases

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 sched-20260922-011 / sched-20260921-001（Vincent Guittot 的「Improving latency of short slice tasks」系列）。本枚已被 Peter Zijlstra 合入 tip/sched/core（commit d2e0100827578641df2f85546bdb57bb1d8ff55b，09-25 12:45:59 +0200），与 sched-20260925-007、sched-20260925-008 同批合入。

## 背景与问题

EEVDF 的 `set_short_buddy()` 用于把刚唤醒的短切片任务设为 preempt buddy，改善短任务延迟。但当**多个短切片任务同时被唤醒**时，`next` 候选的选拔只比较了 slice 大小，未处理相等 slice 时的顺序，导致 `next` 可能被反复覆盖或选出非最早实体。

## 技术方案

`set_short_buddy()` 中，若 `cfs_rq->next` 已存在：先比较 slice，`next->slice < pse->slice` 时返回 false；再处理相等 slice 的情形——若 `next->slice == pse->slice` 且 `entity_before(cfs_rq->next, pse)`，也返回 false（保留更早的实体）。合入版本 diffstat：kernel/sched/fair.c 共 8 insertions(+), 2 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-21，`<20260921152238.3804392-4-vincent.guittot@linaro.org>`）：本枚为系列 4/8。
- 09-25：Peter 合入 tip/sched/core（Commit-ID d2e0100827578641df2f85546bdb57bb1d8ff55b）。

## Maintainer 意见与讨论焦点

系列整体 review 见 sched-20260922-011；本枚为短任务并发唤醒时 preempt buddy 选择的确定性修正。Peter Zijlstra 作为 committer 收取，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit d2e0100827578641df2f85546bdb57bb1d8ff55b。*blocking_issues* 无。

## 效果评估

合入邮件未附 benchmark；短并发唤醒下 preempt buddy 选择的正确性属静态可证。暂无效果数据。

## 我可以参与的点

修复已合入，无代码参与空间；可关注该系列其余未合入补丁（*review*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364338.2819794.17721544590591938311.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/d2e0100827578641df2f85546bdb57bb1d8ff55b
- v1 补丁: https://lore.kernel.org/all/20260921152238.3804392-4-vincent.guittot@linaro.org/

---
id: sched-20260925-009
date: 2026-09-25
subject: "sched/eevdf: Handle more short slice waking cases"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<179033364338.2819794.17721544590591938311.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179033364338.2819794.17721544590591938311.tip-bot2@tip-bot2/"
upstream_commit: "d2e0100827578641df2f85546bdb57bb1d8ff55b"
fixes_commit: null
merged_branch: "tip/sched/core"
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "Peter Zijlstra"
patch_series:
  - version: v1
    msgid: "<20260921152238.3804392-4-vincent.guittot@linaro.org>"
    date: 2026-09-21
    summary: "处理多个短切片任务同时唤醒时 set_short_buddy 的相等 slice 顺序选择"
    review_outcome: "09-25 Peter 合入 tip/sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 tip/sched/core，等待进入合并窗口"
contribution_opportunities:
  - kind: review
    description: "该 EEVDF 短切片系列其余未合入补丁可继续跟进评审"
source_email_count: 1
related_articles:
  - "sched-20260922-011"
  - "sched-20260921-001"
tags:
  - eevdf
  - cfs
---