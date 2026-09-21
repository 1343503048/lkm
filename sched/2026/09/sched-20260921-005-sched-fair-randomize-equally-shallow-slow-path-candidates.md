# sched/fair: Randomize equally shallow slow-path candidates

## TL;DR
增量更新：Christian Loehle 回复 Vincent Guittot 的 review，补充了 idle CPU 选择随机化方案中"未发布 idle 状态"（unpublished idle state）CPU 的处理思路——实测这类候选只占约 0.1-0.5%，把它们按 `U64_MAX` 退出延迟对待后极少成为最优候选，因此随机化引入的偏置风险可控。这是对既有 v2 的补充论证，无新代码。

## 背景与问题
背景见 sched-20260918-004：slow-path idle CPU 扫描总是挑选第一个满足条件的 CPU，存在扫描顺序偏置。系列（v2）通过随机化"同样浅（equally shallow）"的候选消除该偏置。

## 技术方案
本日无新代码。作者针对 review 中关心的"未发布 idle 状态"CPU（即已进入 idle 但 idle 状态尚未对外发布、处于窗口期的 CPU）给出两个处理思路与实测依据：
- 若未发布状态最终造成回归，可按 `rq->idle_stamp` 阈值把候选分桶为"进入 idle"/"退出 idle"两类区别对待。
- 作者实验发现：无论把未发布状态当"理想候选"还是"最差 idle 候选"，结果差异都不大——因为这类候选在各类 benchmark 中只占 CPU 候选的 0.1-0.5%，且把它们当作 `U64_MAX` 退出延迟后，它们极少数情况下才会成为扫描中的最佳候选（两个未发布状态 CPU 之间打平的情况更罕见）。

## 版本演进与当前进展
- v1（09-16）→ v2（09-17，thread root `<20260917153915.1563875-1-christian.loehle@arm.com>`）。
- 09-21：作者回复 Vincent 的 review 意见，补充上述论证，未发新版本。

## Maintainer 意见与讨论焦点
- **Vincent Guittot（sched 维护者）**：此前在 v2 上提出 review 意见（原邮件不在本日缓存，作者回复引用了其关注点），作者本日针对"未发布 idle 状态处理"做了量化回应。
- 讨论焦点收敛于随机化在 idle 状态过渡窗口的鲁棒性，作者以实测数据说明风险极低，当前无明显分歧或 NAK。

## 合入评估
likelihood=medium。方向获维护者关注且作者持续回应，随机化对扫描偏置的消除收益明确；但仍是"公平性/延迟"类微优化，需等维护者对 v2 的最终态度，且尚未见性能数据支撑收益大小。

## 效果评估
作者给出的是"未发布 idle 状态候选占比 0.1-0.5%"这一机制层面的量化数据，属复现观察；随机化本身带来的调度改善未见 benchmark 数字，收益定性为"消除扫描顺序偏置"。

## 我可以参与的点
- **testing**：在调度敏感负载（如短唤醒风暴）上对比随机化前后 idle CPU 选择分布与延迟，提供收益数据。
- **review**：评估"未发布 idle 状态按 U64_MAX 退出延迟处理"在 NUMA/异构平台的边缘影响。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/

---
id: sched-20260921-005
date: '2026-09-21'
subject: 'sched/fair: Randomize equally shallow slow-path candidates'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260917153915.1563875-1-christian.loehle@arm.com>'
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
    review_outcome: 'Vincent Guittot review；作者以未发布 idle 状态占比数据回应，无新版本'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '等维护者对 v2 的最终态度，可补充性能收益数据'
contribution_opportunities:
  - kind: testing
    description: '在短唤醒风暴等负载上对比随机化前后的 idle 选择分布与延迟，提供收益数据'
  - kind: review
    description: '评估未发布 idle 状态按 U64_MAX 退出延迟处理在 NUMA/异构平台的边缘影响'
generated_at: '2026-09-22T01:10:00'
source_email_count: 1
related_articles:
  - sched-20260918-004
tags:
  - cfs
  - idle
---