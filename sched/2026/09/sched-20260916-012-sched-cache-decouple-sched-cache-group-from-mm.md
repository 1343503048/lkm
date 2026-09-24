# sched/cache: Decouple sched_cache_group from mm

## TL;DR
Tim Chen 的 cache-aware 系列 patch 3/4（本日为 Peter Zijlstra 评审轮）：把 `sched_cache_group` 从 mm 中解耦。Peter 密集提了多条正确性意见——注释误导（rcu-free 上下文、RT 下 free_percpu 不可在原子上下文）、发布需 store-release、疑似 TOCTOU、建议用 `READ_ONCE(mm->sched_cache_grp)` 局部变量。合入可能性中等，需作者逐条落实。

## 背景与问题
`struct sched_cache_group`（cache-aware 调度的分组结构）此前挂在 mm 上，按某种 RCU/引用计数的生命周期管理。本 patch 试图把它从 mm 解耦。该系列是 cache-aware 调度上周期合入后的跟进修复/重构。

## 技术方案
patch 本体代码不在今日邮件正文，仅 Peter 评审意见可见。Peter 的聚焦点：解耦后的发布/访问语义——若是一次 publish，需要 store-release；`mm->sched_cache_grp` 的读取建议用 `READ_ONCE` 存到局部变量（否则编译器可反复重载）；并质疑是否存在 TOCTOU 竞态。

## 版本演进与当前进展
- 本日为 Peter 对 4-patch 系列 patch 3/4 的评审（107233），首次意见集中在内存序与生命周期上。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：①注释有误导性——这是 rcu-free 上下文，且 RT 下 `free_percpu()` 不允许在真正的原子上下文调用；②若为 publish，需要 store-release；③疑似存在 TOCTOU；④建议引入 `struct sched_cache_group *scg = READ_ONCE(mm->sched_cache_grp)` 局部变量（编译器允许反复重载该字段）。
- 分歧点：生命周期/发布语义尚未对齐，作者还未公开回应。

## 合入评估
*likelihood=medium*。Peter 已深度参与并提出具体的正确性关切（store-release/TOCTOU/RT），方向未否，但需要作者逐条回应并可能调整 patch 结构。*blocking_issues*：store-release 发布语义、TOCTOU 疑点、注释与 RT 上下文描述需修正。*next_action*：作者回应 Peter 并给出修订版。

## 效果评估
本日评审未涉及性能数据，属生命周期/内存序正确性讨论。

## 我可以参与的点
- kind=review：分析 `sched_cache_group` 解耦后的 RCU 生命周期与 free_percpu 时机，确认是否存在 use-after-free 窗口。
- kind=discussion：论证 TOCTOU 是否存在，并评估改用 READ_ONCE 局部变量的收益。

## 参考链接
- Peter 评审：https://lore.kernel.org/all/20260916125440.GF776954@noisy.programming.kicks-ass.net/

---
id: sched-20260916-012
date: '2026-09-16'
subject: 'sched/cache: Decouple sched_cache_group from mm'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<cb678eddae708e2865ec69a04edf999119c2168a.1789061845.git.tim.c.chen@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/cb678eddae708e2865ec69a04edf999119c2168a.1789061845.git.tim.c.chen@linux.intel.com/'
authors:
  - 'Tim Chen'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: null
patch_series:
  - version: v1
    msgid: '<cb678eddae708e2865ec69a04edf999119c2168a.1789061845.git.tim.c.chen@linux.intel.com>'
    date: '2026-09-15'
    summary: '将 sched_cache_group 从 mm 解耦'
    review_outcome: 'Peter 提出 store-release / TOCTOU / RT 上下文 / READ_ONCE 等意见'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '发布语义需 store-release'
    - '疑似 TOCTOU'
    - '注释与 RT 上下文描述需修正'
  next_action: '作者回应 Peter 并给出修订版'
contribution_opportunities:
  - kind: review
    description: '分析解耦后的 RCU 生命周期与 free_percpu 时机，确认无 UAF 窗口'
  - kind: discussion
    description: '论证 TOCTOU 是否存在及 READ_ONCE 局部变量收益'
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - cfs
---