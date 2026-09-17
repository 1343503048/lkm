# sched/fair: Randomize equally shallow slow-path candidates

## TL;DR
增量更新：Christian Loehle 的慢路径 idle CPU 选择系列推出 v2（1/2 删除 idle-recency tie-break，获 Vincent Guittot Reviewed-by；2/2 用 reservoir sampling 随机化等 exit-latency 候选）。本日讨论集中在 2/2 的 !idle CPU 处理与候选计数复位：Vincent 提出无 cpuidle 驱动时须保留 !idle CPU、Shubhang 建议把采样限定在 exit_latency==min 的候选中，作者倾向沿用 v1 的 !idle 优先级并改用 U64_MAX reservoir，Kayra 主动请缨另发 idle helper 补丁。

## 背景与问题
背景见 sched-20260916-015：并发慢路径选择器会收敛到同一 idle CPU，且 idle-recency 时间戳偏好可能选中唤醒成本最高的 CPU。v2 将原方案拆为两枚补丁单独成文。

## 技术方案
- 1/2（Drop idle recency from slow-path CPU selection）：删除 idle_stamp tie-break，除遇到更低 exit latency 外保留首个候选，15 行缩减为 1 行。
- 2/2（Randomize equally shallow slow-path candidates）：用 per-CPU PRNG + `reciprocal_scale()` 对等 exit-latency 候选做 reservoir sampling；用 u64 latency key、U64_MAX 表示未发布状态；发布状态优先，无发布状态时在无状态 idle CPU 间采样。

## 版本演进与当前进展
- v1（09-16，`<20260916100116.701206-1-christian.loehle@arm.com>`）：首版。
- v2（09-17，`<20260917153915.1563875-1-christian.loehle@arm.com>`）：拆为 1/2、2/2；1/2 获 Vincent Reviewed-by；2/2 用 U64_MAX reservoir 替代原实现，仍在评审。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**：对 1/2 给出 Reviewed-by。对 2/2 提出：有 cpuidle 驱动时 !idle 表示 CPU 正在进出 idle（进入者是好候选、退出者不应选），现有 idle_stamp 比较并不健壮，随机选"也许不会更糟"；又指出"找到更低 exit_latency 时就清空候选数，但已被检查过的 !idle CPU 会被清掉"的不一致，并强调无 cpuidle 驱动时必须保留 !idle CPU。
- **Shubhang Kaushik**：质疑 !idle 候选在已选中最优 CPU 后仍以等权进入随机池是否是有意设计，建议把采样限定在 `idle->exit_latency == min_exit_latency` 的候选中、!idle 仅作 fallback。
- **Christian Loehle（作者）**：承认 !idle 处理是取舍；倾向沿用 v1 行为（!idle 优先级高于已见 CPU、保留 min_exit_latency），并将候选池改为 U64_MAX reservoir；希望把 NULL 状态排名等策略放到独立的 idle helper 补丁处理，不在本补丁嵌入假设。
- **Kayra Cizmeci**：主动提出可为 idle helper 出补丁。
- 分歧点：!idle CPU 的采样资格与候选计数复位语义仍未最终闭合，作者倾向与当前上游行为保持一致。

## 合入评估
likelihood=medium。1/2 已获 Reviewed-by、2/2 方向获 Vincent 认可但仍有 !idle 处理与计数复位两个设计点待收敛；作者承诺出 v3（U64_MAX reservoir + 独立的 idle helper）。blocking_issues：2/2 的 !idle 候选语义与候选计数复位待定；v3 未发出。next_action：作者发 v3 落实 U64_MAX reservoir 与 idle helper 拆解，回应 Vincent/Shubhang 剩余意见。

## 效果评估
本日 v2 未附新的 benchmark；v1 数据（160 核 Altra stress-ng fork 中位数吞吐最高 +4.13%、stale-pick 率近乎减半）见 sched-20260916-015。

## 我可以参与的点
- kind=testing：在 8~32 核小系统复测 v2，验证 !idle CPU 处理在小域下的行为。
- kind=new_patch：按 Kayra 提议，把 NULL 状态/!idle 排名策略打包为独立的 idle/cpuidle helper 补丁（作者已明确希望拆出）。
- kind=discussion：就"!idle 是否应与 min_exit_latency 候选等权进入采样池"给出小核数/无 cpuidle 驱动的论据。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260917153915.1563875-1-christian.loehle@arm.com/
- v1 参考: https://lore.kernel.org/all/20260916100116.701206-1-christian.loehle@arm.com/

---
id: sched-20260917-007
date: '2026-09-17'
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
  - version: v1
    msgid: '<20260916100116.701206-1-christian.loehle@arm.com>'
    date: '2026-09-16'
    summary: '删除 idle-recency tie-break + reservoir sampling 随机化等 latency 候选'
    review_outcome: 'Kayra/Sashiko 关切小核数与随机不可预测性'
  - version: v2
    msgid: '<20260917153915.1563875-1-christian.loehle@arm.com>'
    date: '2026-09-17'
    summary: '拆为 1/2（drop idle recency，获 Reviewed-by）与 2/2（U64_MAX reservoir）'
    review_outcome: 'Vincent/Shubhang 聚焦 2/2 的 !idle 处理与计数复位；作者准备 v3'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '2/2 的 !idle 候选语义与候选计数复位待收敛'
    - 'v3 未发出'
  next_action: '作者发 v3 落实 U64_MAX reservoir 与 idle helper 拆解'
contribution_opportunities:
  - kind: testing
    description: '在 8~32 核小系统复测 v2 的 !idle CPU 处理'
  - kind: new_patch
    description: '把 NULL 状态/!idle 排名策略打包为独立 idle helper 补丁'
  - kind: discussion
    description: '论证 !idle 是否应与 min_exit_latency 候选等权进入采样池'
generated_at: '2026-09-18T09:00:00'
source_email_count: 12
related_articles:
  - sched-20260916-015
tags:
  - cfs
  - idle
---