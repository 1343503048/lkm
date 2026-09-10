# sched/eevdf: Fix augmented max_slice

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260908-005。Vincent Guittot 的 max_slice 初始化修复已被 Peter Zijlstra 合入 tip/sched/urgent（commit 9a8bc9bb4c3f，09-10 10:22 +0200），与同日的多字段拷贝修复（sched-20260910-004）一起构成 EEVDF 增广树的两枚紧急修复。

## 背景与问题
se->max_slice 是 EEVDF 运行树的增广字段之一，用于在父级维护子树内最大 slice。__enqueue_entity() 此前只用 se->slice 初始化了 se->min_vruntime 与 se->min_slice，没有初始化 se->max_slice，导致增广回调在父级计算 max_slice 时基于陈旧值，结果错误。Fixes: 6e3c0a4e1ad1 ("sched/fair: Fix lag clamp")。

## 技术方案
两行修复：在 __enqueue_entity() 中、调用 rb_add_augmented_cached() 之前补 `se->max_slice = se->slice;`，与 min_slice 的处理对称，使增广回调自底向上计算时初值正确。合入版本 diffstat：kernel/sched/fair.c | 2 ++。

## 版本演进与当前进展
- v1（2026-09-07，msgid `<20260907123855.1297976-1-vincent.guittot@linaro.org>`）：首发，09-08 Prateek 无条件 Reviewed-by（"Feel free to include"）。
- 09-10：Peter 直接以 v1 合入 tip/sched/urgent（Commit-ID 9a8bc9bb4c3fb3218b4f151f98a722fbeb5b5c34，AuthorDate 09-07 14:38:55 +0200，CommitterDate 09-10 10:22:51 +0200），无 v2。

## Maintainer 意见与讨论焦点
K Prateek Nayak 的 Reviewed-by 已随合入 commit 记录；Peter Zijlstra 作为 committer 直接收取。本日无新讨论、无分歧。

## 合入评估
已合入：tip/sched/urgent，commit 9a8bc9bb4c3fb3218b4f151f98a722fbeb5b5c34（likelihood: merged）。与 51b0e68cfa0a（多字段拷贝修复）同批进入 urgent 分支，预计随下一轮 -rc 修复进入主线。

## 效果评估
合入邮件未附 benchmark 或复现数据；修复正确性由增广字段初始化语义静态可证。暂无效果数据。

## 我可以参与的点
当前阶段修复已合入 urgent，无明显参与空间；可顺带确认自家分支若回合 6e3c0a4e1ad1 则需同时回合本修复与 51b0e68cfa0a，两枚是同一根因面的配套修复（review）。

## 参考链接
- lore thread（v1 补丁）: https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/
- tip-bot 合入通知: https://lore.kernel.org/all/178903092750.623050.7543123540318471247.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/9a8bc9bb4c3fb3218b4f151f98a722fbeb5b5c34

---
id: sched-20260910-005
date: 2026-09-10
subject: "sched/eevdf: Fix augmented max_slice"
subsystem: sched
type: bug
status: merged_tip
severity: medium
thread_root_msgid: "<20260907123855.1297976-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/"
upstream_commit: "9a8bc9bb4c3fb3218b4f151f98a722fbeb5b5c34"
fixes_commit: "6e3c0a4e1ad1"
merged_branch: "tip/sched/urgent"
current_version: v1
generated_at: "2026-09-11T10:15:00"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "Peter Zijlstra"
  - "K Prateek Nayak"
patch_series:
  - version: v1
    msgid: "<20260907123855.1297976-1-vincent.guittot@linaro.org>"
    date: "2026-09-07"
    summary: "__enqueue_entity() 中补 se->max_slice = se->slice 初始化，使增广回调在父级正确计算 max_slice。"
    review_outcome: "09-08 Prateek 无条件 Reviewed-by；09-10 Peter 以 v1 原样合入 tip/sched/urgent。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 tip/sched/urgent，等待进入 -rc"
contribution_opportunities:
  - kind: review
    description: "自家分支若回合 6e3c0a4e1ad1，需同时回合本修复与 51b0e68cfa0a，确认两枚配套修复的回合完整性"
source_email_count: 1
related_articles:
  - "sched-20260908-005"
tags:
  - eevdf
  - cfs
---
