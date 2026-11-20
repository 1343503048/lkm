# sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-006 / 20261106-004 / 20261111-013：李坤宇（Li kunyu）的补丁在 wakeup 路径、目标 runqueue 深度达平均 nr_running 3 倍时改用「分布」策略导流突发唤醒任务；Kayra Cizmeci 与 K Prateek Nayak 给密集意见，多次 rebase 迭代。
- sched-20261120-022（今天）：**作者 ping**——请求 Peter 复审并告知是否有其它需要修改的地方。无新版本、无新评审意见。

## 背景与问题

（承接）突发唤醒（burst-woken）场景下任务集中落到某 runqueue 造成瞬时拥塞；补丁在目标 rq 深度达到「平均 nr_running 3 倍」阈值时改用分布策略。系列经历 v1→v2→… 多轮 rebase 与评审（此前 Kayra/Prateek 指出过「补丁不适用于 mainline」等结构性问题）。

## 技术方案

（承接）3x 阈值触发分布导流（此前已把阈值预计算缓存进 root_domain、改用 `rq->next_balance` 等）。今日无代码变化。

## 版本演进与当前进展

*current_version: v4（2026-11-11，`<20261111061803.337042-1-likunyu@open-hieco.net>`）*。今日为作者 ping、无新版本：请求 Peter 复审并告知后续修改点。

## Maintainer 意见与讨论焦点

- **Li kunyu（作者）**：ping 请求 Peter 复审。
- 无维护者当日表态；无 NAK。此前的结构性质疑（是否适用于 mainline）仍是悬而未决的焦点。

## 合入评估

*likelihood=unknown*。作者在等维护者复审，但此前「补丁是否适用于 mainline」的结构性质疑未化解、当日无任何新评审，进展停滞。*blocking_issues*：等维护者复审；此前结构性意见未闭环。*next_action*：Peter 复审并给出下一步意见。

## 效果评估

无新数据；此前各版的效果数据未在当日讨论中更新。

## 我可以参与的点

- **review**：对照此前 Kayra/Prateek 的结构性质疑（mainline 适用性、阈值语义），给出该启发式是否值得合入的判断。

## 参考链接

- lore thread（作者 ping）: https://lore.kernel.org/all/9cc3d7d8-a0ae-6c14-3464-f1cdb17838b5@open-hieco.net/

---
id: sched-20261120-022
date: '2026-11-20'
subject: "sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average"
subsystem: sched
type: feature
status: stalled
severity: none
thread_root_msgid: "<20261111061803.337042-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/9cc3d7d8-a0ae-6c14-3464-f1cdb17838b5@open-hieco.net/"
authors: [Li kunyu]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: "<20261111061803.337042-1-likunyu@open-hieco.net>"
    date: '2026-11-11'
    summary: "3x 阈值触发分布导流"
    review_outcome: "作者 ping 求复审，无新评审"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["等维护者复审", "此前结构性意见未闭环"]
  next_action: "Peter 复审并给出下一步意见"
contribution_opportunities:
  - kind: review
    description: "对照此前结构性质疑给出该启发式是否值得合入的判断"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: [sched-20261105-006, sched-20261106-004, sched-20261111-013]
tags: [cfs, load_balance]
---