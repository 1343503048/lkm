# sched/fair: Revert 6d71a9c61604 ("sched/fair: Fix EEVDF entity placement bug causing scheduling lag")

## TL;DR
Jose Souza（John Stultz 等参与）针对 6.18 稳定分支提交 Revert of `6d71a9c61604`（EEVDF 实体放置改动），修复其引入的调度延迟回归/任务饥饿。Peter 在 8/10 讨论是否应直接 revert。属 high 严重度回归，under_review。

## 背景与问题
commit `6d71a9c61604` 修改了 EEVDF 的实体（entity）放置逻辑，在 6.18 上被观察到引入调度延迟回归或某些任务饥饿（延迟敏感任务得不到及时调度）。稳定分支需要缓解。

## 技术方案
方案 A：直接在 6.18 稳定分支 revert `6d71a9c61604`，快速消除回归；方案 B：仅修主线、稳定分支择机回退。邮件讨论当前偏向 revert。设计取舍：稳定分支优先稳定性，即使牺牲该 commit 带来的（可能有争议的）公平性改进。

## 版本演进与当前进展
当前为 6.18 stable revert 提案。Peter 8/10 反馈讨论是否直接 revert。

## Maintainer 意见与讨论焦点
Peter 在权衡：直接 revert（简单、稳）vs 精确修复（保留改进、但稳定分支风险更高）。这是当前核心讨论点。

## 合入评估
合入可能性 medium。稳定分支回归通常需要动作，但取决于 Peter 的最终取向（revert 还是修）。

## 效果评估
无 benchmark 在邮件中；目标是消除延迟回归/饥饿。

## 我可以参与的点
- 在 6.18 内核上实测 revert 前后 sched_latency / 饥饿；
- 评审 revert vs 精确修复的取舍。

## 参考链接
- lore: 未获取到
- 关联 commit: 6d71a9c61604

---
subject: "sched/fair: Revert 6d71a9c61604 ("sched/fair: Fix EEVDF entity placement bug causing scheduling lag")"
id: sched-20260810-011
date: 2026-08-10
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: "<20260810xxxxxx-jose@kernel.org>"
lore_url: "未获取到"
authors: [Jose Souza, John Stultz]
maintainers_involved: [Peter Zijlstra, Ingo Molnar, Vincent Guittot, Dietmar Eggemann]
current_version: "stable 6.18"
patch_series:
  - version: "stable 6.18"
    msgid: "<20260810xxxxxx-jose@kernel.org>"
    date: 2026-08-10
    summary: "针对 6.18 稳定分支，Revert commit 6d71a9c61604（EEVDF 实体放置相关改动），修复因该提交引入的调度延迟回归/任务饥饿。"
    review_outcome: "Peter 在 8/10 对该 revert 给出反馈（讨论是否应 revert 还是给更精确的修复）。"
upstream_commit: null
fixes_commit: "6d71a9c61604"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Peter 讨论是否直接 revert 还是给更精确修复"]
  next_action: "等待维护者决定：直接 revert 6.18 还是只修主线 + 稳定分支择机回退。"
contribution_opportunities:
  - kind: testing
    description: "在 6.18 内核上对比 revert 前后调度延迟/饥饿指标。"
  - kind: review
    description: "评审 revert 与更精确修复两种方案的取舍。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 2
related_articles: []
tags: [sched/fair, eevdf, regression]
---
