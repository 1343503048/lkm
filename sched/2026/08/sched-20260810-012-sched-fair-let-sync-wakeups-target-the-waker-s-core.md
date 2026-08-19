# sched/fair: Let sync wakeups target the waker's core

## TL;DR
Madadi Vineeth Reddy 提交「让同步唤醒目标落在唤醒者所在 core」，附 Kayra Cizmeci 在 8/10 提供的 x86 实测数据（部分负载 IPC/延迟改善）。under_review。

## 背景与问题
同步唤醒（waker 立即睡眠、被唤醒者接手）常见于生产者-消费者等模式。若被唤醒者被放到远离 waker 的 CPU，会损失 waker 留下的缓存/内存局部性。现有 wake_affine 逻辑未明确把 sync wakeup 目标绑定到 waker 的 core。

## 技术方案
在 sync wakeup 路径，把候选目标优先限定在 waker 所在 core（含其 SMT 兄弟），提升局部性。设计取舍：以局部性优先，但需避免在该 core 已满载时强塞（应有回退）。

## 版本演进与当前进展
当前 v1。Kayra 8/10 提供 x86 实测数据，显示部分负载改善。

## Maintainer 意见与讨论焦点
焦点：x86 改善是否在所有架构/负载通用，是否存在回退场景（如目标 core 已满载）。

## 合入评估
合入可能性 medium。需更多架构数据支撑普适性。

## 效果评估
x86 部分负载 IPC/延迟改善（来自 Kayra 数据），需更多架构验证。

## 我可以参与的点
- 在 ARM64 等架构复现局部性改善，检查回归；
- 评审与 wake_affine 逻辑的协调。

## 参考链接
- lore: 未获取到

---
subject: "sched/fair: Let sync wakeups target the waker's core"
id: sched-20260810-012
date: 2026-08-10
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260810xxxxxx-madadi@kernel.org>"
lore_url: "未获取到"
authors: [Madadi Vineeth Reddy, Kayra Cizmeci]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Ingo Molnar, K Prateek Nayak]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260810xxxxxx-madadi@kernel.org>"
    date: 2026-08-10
    summary: "让同步唤醒（sync wakeup）的目标优先落在唤醒者（waker）所在的 core，提升缓存/内存局部性；附 x86 实测数据。"
    review_outcome: "Kayra Cizmeci 在 8/10 提供 x86 实测数据（部分负载下 IPC/延迟改善），讨论是否对所有架构/负载通用。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需确认对不同架构/负载的通用性，避免回归"]
  next_action: "等待更多架构数据与维护者确认目标 core 选取的普适性。"
contribution_opportunities:
  - kind: testing
    description: "在 ARM64/其它架构上复现 x86 的局部性改善，检查是否有回归。"
  - kind: review
    description: "评审 sync wakeup 目标 core 选取与现有 wake_affine 逻辑的协调。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 1
related_articles: []
tags: [sched/fair, wake_affine]
---
