# sched/fair: Randomize equally shallow idle CPU picks

## TL;DR
- sched-20260916-015（v1）/ sched-20260918-004、sched-20260921-005（v2）：Christian Loehle 的 idle CPU 选择随机化系列——消除 slow-path idle 扫描「总是挑第一个满足条件的 CPU」带来的扫描顺序偏置，v2 起标题改为「Randomize equally shallow idle CPU picks」，并对 review 关心的「未发布 idle 状态」候选做了量化回应（占比仅 0.1-0.5%）。
- sched-20260924-013（今天，增量更新）：Muhammad Usama Anjum（ARM）用 Fastpath 在 AWS Graviton3 上对 v2 做回归验证并给出 `Tested-by`——mysql-workload 的 db transaction rate / new order rate 在单节点（m7g.metal）与多节点（m7g.metal + m7gd.12xlarge）上均无明显变化（-0.08% ~ +0.05%，未标记显著），即随机化未引入可测回退。

## 背景与问题
- sched-20260918-004：slow-path idle CPU 扫描总是挑选第一个满足条件的 CPU，存在扫描顺序偏置；系列通过随机化「同样浅（equally shallow）」的候选消除该偏置。
- 本日无新增背景。

## 技术方案
- 沿用 v2 方案（随机化同样浅的候选，见 sched-20260918-004）。本日无新代码，仅第三方回归验证。

## 版本演进与当前进展
- v1（09-16，`<20260916100116.701206-1-christian.loehle@arm.com>`）→ v2（09-17，`<20260917153915.1563875-1-christian.loehle@arm.com>`）。
- 本日（09-24）：Muhammad Usama Anjum 回复 v2 cover（`<20260916100116.701206-1-christian.loehle@arm.com>` 线程）附 Fastpath 数据并给 `Tested-by`。

## Maintainer 意见与讨论焦点
- **Muhammad Usama Anjum（ARM）**：给出 Fastpath 实测 `Tested-by`，结论为随机化在 mysql-workload 上无可测回退（未标记显著改善或回退）。注意他测试的分支名是 `v7.3-rc4-chr-idle-v2`。
- 无新增分歧；此前 Vincent Guittot 的 review 意见作者已在 09-21 回应。合入仍需维护者对 v2 的最终态度。

## 合入评估
*likelihood=medium*。方向获关注、作者已回应 review、今日又有第三方 Tested-by（无回退背书）；但仍属「公平性/延迟」类微优化，需维护者对 v2 的最终表态，且「消除扫描偏置」的收益仍缺正面 benchmark 数字。*blocking_issues*：无明确反对，待 Vincent/Peter 等维护者对 v2 的收取决定。*next_action*：维护者对 v2 给出最终态度并收取。

## 效果评估
- 本日 Fastpath（AWS m7g.metal，单节点）：mysql-workload db transaction rate -0.02%、new order rate -0.08%；多节点（m7g.metal + m7gd.12xlarge，非 placement group，注明网络可能瓶颈）：+0.03% / +0.05%。均未标记统计显著——即随机化未引入可测回退。
- 随机化本身带来的正面收益仍未见量化数字，收益定性为「消除扫描顺序偏置」。

## 我可以参与的点
- kind=testing：在更调度敏感的负载（短唤醒风暴、NUMA/异构）上测随机化的正面收益与尾部延迟，补充 v2 目前缺失的「收益」侧 benchmark。
- kind=review：评估随机化在「未发布 idle 状态」与 NUMA/异构平台上的边缘影响。

## 参考链接
- lore (v2 cover): https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/
- Fastpath Tested-by: https://lore.kernel.org/all/c918c068-bf55-492f-bb7c-fcf02b8c661b@arm.com/

---
id: sched-20260924-013
date: '2026-09-24'
subject: 'sched/fair: Randomize equally shallow idle CPU picks'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260916100116.701206-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved:
  - 'Vincent Guittot'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260917153915.1563875-1-christian.loehle@arm.com>'
    date: '2026-09-17'
    summary: '随机化同样浅的 idle CPU 候选，消除扫描顺序偏置'
    review_outcome: 'Vincent review 已回应；Muhammad 给 Tested-by（无回退）'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '维护者对 v2 给出最终态度并收取'
contribution_opportunities:
  - kind: testing
    description: '在调度敏感负载上测随机化正面收益与尾部延迟'
  - kind: review
    description: '评估未发布 idle 状态与 NUMA/异构平台边缘影响'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260921-005
  - sched-20260918-004
  - sched-20260916-015
tags:
  - cfs
  - idle
---