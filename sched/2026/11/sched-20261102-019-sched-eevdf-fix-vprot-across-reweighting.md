# sched/eevdf: Fix vprot across reweighting

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261016-001：Kayra Cizmeci 修 EEVDF 的 vprot（slice protection）在 reweighting 时的正确性 bug；v3→v4→v5 快速迭代，Vincent Guittot 全程 review 并给出 Reviewed-by，v5 收敛等 Peter 收取。
- sched-20261102（今天）：作者对 Peter 温和 ping（"Gentle ping... Do you think its ready to be applied?"）——补丁已具备 RB、等待 Peter 收取，暂无进一步异议。

## 背景与问题

（承接）`reweight_eevdf()` 权重变化时 vprot 未跟 vruntime 平移，导致死掉的 protection 复活、活着的增减甚至死掉。

## 技术方案

（承接）v5 形态分两处：`reweight_eevdf()` 的 `on_rq` 分支平移/重置 `se->vprot`；`enqueue_task_fair()` 的 `!curr` 路径在 `place_entity()` 后按 `task_current_donor()` 调 `cancel_protect_slice(se)`。

## 版本演进与当前进展

v5；今日为等待收取的 ping，无版本变化。

## Maintainer 意见与讨论焦点

Vincent（维护者）已 RB；Peter 尚未 finalize（作者 ping 提醒）。

## 合入评估

likelihood=high。已有维护者 RB、无遗留 objection，只差 Peter 收取。

## 效果评估

（承接）正确性修复，无性能数字。

## 我可以参与的点

当前阶段暂无明显参与空间，等待 Peter 收取。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261016153721.7843-1-kayracizmeci@gmail.com/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261016153721.7843-1-kayracizmeci@gmail.com>
authors:
- Kayra Cizmeci
maintainers_involved: []
current_version: v5
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Peter Zijlstra 收取
contribution_opportunities: []
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261016-001
tags:
- eevdf
- cfs
id: sched-20261102-019
subject: 'sched/eevdf: Fix vprot across reweighting'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
