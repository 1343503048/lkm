# sched_ext: Move reject DSQ draining into core

## TL;DR
Andrea Righi 提交 v5「Prefer fully idle cores for NOHZ balancing」。NOHZ 均衡选核时优先选「所有兄弟线程都空闲」的 core，减少 SMT 干扰。Peter 在 8/10 报告已 pull v4 进 tip/sched/core，v5 待整理。合入可能性高。

## 背景与问题
NOHZ（tickless）负载均衡把任务搬到空闲 CPU。但若目标 core 仍有兄弟线程（SMT 另一线程）在运行，新任务会与之共享执行资源，带来干扰与吞吐下降。原逻辑未区分「core 级空闲」与「thread 级空闲」。

## 技术方案
在 NOHZ 均衡的目标选择中，优先挑选「完全空闲」的 core（core 内所有 SMT 兄弟线程均空闲）。仅在无完全空闲 core 时才退回到单线程空闲。设计取舍：把 core 级空闲作为更优目标，可能增加均衡搜索的复杂度，但显著降低 SMT 干扰。

## 版本演进与当前进展
当前 v5。Peter 8/10 报告 v4 已被 pull 进 tip/sched/core，v5 等待后续整理提交。

## Maintainer 意见与讨论焦点
焦点：完全空闲 core 判定的搜索开销，以及多 LLC/NUMA 下的回退策略。v4 已被接受说明方向获认可。

## 合入评估
合入可能性 high。v4 已进入 tip，v5 为增量改进。

## 效果评估
无独立 benchmark；预期降低 SMT 干扰、提升均衡后吞吐（需在 SMT 机器实测）。

## 我可以参与的点
- 在 SMT 机器上跑负载对比 v5 前后均衡核分布与吞吐；
- 评审完全空闲 core 判定的开销。

## 参考链接
- lore: 未获取到
- tip 分支: tip/sched/core（v4 已 pull）

---
subject: "sched_ext: Move reject DSQ draining into core"
id: sched-20260810-009
date: 2026-08-10
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260809203020.xxxxxx-righi@kernel.org>"
lore_url: "未获取到"
authors: [Andrea Righi]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Joel Fernandes, Ingo Molnar]
current_version: v5
patch_series:
  - version: v5
    msgid: "<20260809203020.xxxxxx-righi@kernel.org>"
    date: 2026-08-09
    summary: "v5：NOHZ 负载均衡在选核时优先选择「完全空闲」的 core（所有兄弟线程均空闲），降低把任务放到尚有兄弟线程运行的核上带来的 SMT 干扰。"
    review_outcome: "Peter 在 8/10 报告已 pull v4 进入 tip/sched/core，等待 v5 后续整理。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 v5 整理后被 pull 进 tip/sched/core（v4 已被 pull）。"
contribution_opportunities:
  - kind: testing
    description: "在 SMT 开启的机器上对比 v5 前后 NOHZ 均衡的核选择分布与吞吐。"
  - kind: review
    description: "评审「完全空闲 core」判定在多 LLC/NUMA 拓扑下的代价。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 1
related_articles: []
tags: [sched/fair, nohz, idle]
---
