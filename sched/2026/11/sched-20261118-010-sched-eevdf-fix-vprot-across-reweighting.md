# sched/eevdf: Fix vprot across reweighting

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261102-019：Kayra Cizmeci 修 EEVDF 的 vprot（slice protection）在 reweighting 时的正确性 bug（v3→v4→v5 迭代，Vincent 全程 RB，v5 收敛等 Peter 收取）。作者当日对 Peter 温和 ping。
- sched-20261118-010（今天）：**作者自述「等得无聊就实测了」**——验证两件事：只有 sched 变更走新加路径、所有任务的 protection 处理正确；结果 ~318000 次 curr 的 reweight、其中 ~48000 次存活，无一异常。补丁仍处「等 Peter 收取」状态。

## 背景与问题

（承接 sched-20261102-019）`reweight_eevdf()` 权重变化时 vprot 未跟 vruntime 平移，导致死掉的 protection 复活、活着的增减甚至死掉。v5 已收敛、具备 Vincent 的 RB，只差 Peter 收取。作者今日补上一份自测数据以推动收取。

## 技术方案

（承接）v5 形态两处：`reweight_eevdf()` 的 `on_rq` 分支平移/重置 `se->vprot`；`enqueue_task_fair()` 的 `!curr` 路径在 `place_entity()` 后按 `task_current_donor()` 调 `cancel_protect_slice(se)`。今日无代码变化。

## 版本演进与当前进展

*current_version: v5（2026-10-16 发出，`<20261016153721.7843-1-kayracizmeci@gmail.com>`）*。今日为「等收取 + 补自测」：作者实测 v5，无新版本。

## Maintainer 意见与讨论焦点

- 作者自测了两点：① 只有 sched 变更进入 `enqueue_task_fair()` 新加路径；② 所有任务的 protection 处理正确。~318000 次 curr reweight、~48000 次存活，无异常。
- Vincent（维护者）此前已 RB；Peter 尚未 finalize。

## 合入评估

*likelihood=high*。已有维护者 RB、作者补了自测数据、无遗留 objection，只差 Peter 收取。*blocking_issues*：无。*next_action*：等 Peter 收取。

## 效果评估

正确性修复，无性能数字。作者今日给出自测规模：~318000 次 curr 的 reweight（其中 ~48000 次 alive），无一异常。

## 我可以参与的点

当前阶段暂无明显参与空间，等待 Peter 收取。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261016153721.7843-1-kayracizmeci@gmail.com/
- Kayra 今日自测: https://lore.kernel.org/all/avx3Q0WvV5lgAhWA@scheduler.schedules/

---
id: sched-20261118-010
date: '2026-11-18'
subject: "sched/eevdf: Fix vprot across reweighting"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261016153721.7843-1-kayracizmeci@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261016153721.7843-1-kayracizmeci@gmail.com/"
authors: [Kayra Cizmeci]
maintainers_involved: [Vincent Guittot]
current_version: v5
patch_series:
  - version: v5
    msgid: "<20261016153721.7843-1-kayracizmeci@gmail.com>"
    date: '2026-10-16'
    summary: "reweight_eevdf on_rq 分支平移 vprot + enqueue_task_fair cancel_protect_slice"
    review_outcome: "Vincent RB，等 Peter 收取；今日作者补自测"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 Peter 收取"
contribution_opportunities: []
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-019]
tags: [eevdf]
---
