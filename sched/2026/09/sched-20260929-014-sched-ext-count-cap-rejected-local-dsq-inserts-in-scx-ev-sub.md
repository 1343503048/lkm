# sched_ext: Count cap-rejected local DSQ inserts in SCX_EV_SUB_REJECT

> **subject**：`sched_ext: Count cap-rejected local DSQ inserts in SCX_EV_SUB_REJECT`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260925-019：Liang Luo 发单枚统计补全——`__scx_resolve_local_dsq()` 对「缺 cap 的 local DSQ 入队」三种结果中前两种（强制 admit、rescue）都有计数器，唯独第三种「转入 reject DSQ」没有，补丁新增 `SCX_EV_SUB_REJECT` 补齐可观测面。
- sched-20260929-014（今天）：补丁被**撤回**。Tejun 先要求给出「为何单独计这个」的理由并 drop `Fixes:`；v2 照做后，Andrea Righi 仍认为不需要该事件——BPF 调度器能通过 `SCX_TASK_REENQ_CAP` 自己计数；作者 Liang Luo 回复「Fair enough... Withdrawing the patch.」

## 背景与问题

（承接 sched-20260925-019）缺 cap 的 local DSQ 入队在 `__scx_resolve_local_dsq()` 里有三种出路：因 rq 离线 drain/migration-disabled/pending 迁移而强制 admit（`SCX_EV_SUB_FORCED_ADMIT`）、请求了 rescue 走 rescue 路径（`SCX_EV_SUB_RESCUE`）、或转入 reject DSQ 重入队让 BPF 重新决策（无计数）。作者的初始动机是让三种结果都可观测。今天该动机被两位维护者先后质疑，最终撤回。

## 技术方案

（承接）在 `struct scx_event_stats` 加 `SCX_EV_SUB_REJECT` 并纳入 `SCX_EVENTS_LIST`，在 reject 分流点 +1（kernel/sched/ext/internal.h +10/+1、sub.c +2）。v2 仅按 Tejun 意见改写 commit message 理由并 drop `Fixes:`，代码无变化。最终撤回，未合入。

## 版本演进与当前进展

- v1（09-25，`<20260925070500.565561-1-luoliang@kylinos.cn>`）：带 `Fixes: 75a8c8202c91`。
- v2（09-29，`<20260929030356.3454280-1-luoliang@kylinos.cn>`）：按 Tejun 要求重写理由、drop `Fixes:`，代码不变。
- 09-29 稍后：作者回复 Andrea「Fair enough... Withdrawing the patch.」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：不反对加计数器，但「我们并非每条路径都计数，某条未计数的分支本身不构成理由」；并指出「这没修 bug，请 drop `Fixes:`」。
- **Andrea Righi**（sched_ext 维护者）：v2 上仍「看不出需要这个事件」——BPF 调度器在 cap 相关重入队时会收到 `SCX_TASK_REENQ_CAP`，可自行计数（`scx_qmap` 已这么做）；该计数与新提议的 diversion 计数不完全等价，但 commit message 没解释这个区分为何重要，并反问「有没有具体场景是这个新计数器能诊断、而调度器侧计数不能的？」。
- **Liang Luo**（作者）：接受意见，「Fair enough... Withdrawing the patch.」，感谢两位审阅。
- 结论：补丁撤回，无遗留争议。

## 合入评估

*likelihood=rejected*。作者主动撤回，两位维护者一致认为该计数器缺乏独立必要性（可由调度器侧 `SCX_TASK_REENQ_CAP` 计数覆盖）。*blocking_issues*：无（已撤回）。*next_action*：无需跟进；若日后有「调度器侧计数无法诊断」的具体场景，可再提。

## 效果评估

无运行时数据；属观测面补全的尝试，最终因「可由调度器侧替代」而未落地。

## 我可以参与的点

- 当前阶段已撤回，无明显参与空间；可关注后续是否有基于真实诊断场景重新提出的版本。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20260929030356.3454280-1-luoliang@kylinos.cn/
- Andrea 回复: https://lore.kernel.org/all/artII3WkutGPf7VQ@gpd4/
- 作者撤回: https://lore.kernel.org/all/20260929061213.241696-1-luoliang@kylinos.cn/

---
id: sched-20260929-014
date: '2026-09-29'
subject: 'sched_ext: Count cap-rejected local DSQ inserts in SCX_EV_SUB_REJECT'
subsystem: sched
type: fix
status: superseded
severity: low
thread_root_msgid: '<20260929030356.3454280-1-luoliang@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260929030356.3454280-1-luoliang@kylinos.cn/'
authors:
  - 'Liang Luo'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260925070500.565561-1-luoliang@kylinos.cn>'
    date: '2026-09-25'
    summary: '新增 SCX_EV_SUB_REJECT 计数，带 Fixes: 75a8c8202c91'
    review_outcome: 'Tejun 要求给理由并 drop Fixes'
  - version: v2
    msgid: '<20260929030356.3454280-1-luoliang@kylinos.cn>'
    date: '2026-09-29'
    summary: '重写 commit message 理由、drop Fixes，代码不变'
    review_outcome: 'Andrea 认为无需该事件（可 SCX_TASK_REENQ_CAP 计数），作者撤回'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues: []
  next_action: '无需跟进；如有真实诊断场景可再提'
contribution_opportunities: []
generated_at: '2026-09-30T01:15:00'
source_email_count: 5
related_articles:
  - sched-20260925-019
tags:
  - sched_ext
---