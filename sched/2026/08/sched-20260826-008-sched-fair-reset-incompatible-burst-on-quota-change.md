# sched/fair: Reset incompatible burst on quota change

## TL;DR

Zhe Liu (Kylinos) 提交了修复 CFS bandwidth 中 burst 与 quota 不兼容的问题。当 burst 值大于 quota 时，当前验证逻辑会在写入顺序不同时产生 `EINVAL`。Michal Koutný 建议在执行时 clamp 而非在验证时拒绝。作者同意并计划发 v2：保留配置的 burst 值，在 `__refill_cfs_bandwidth_runtime()` 中执行 clamp。

## 背景与问题

CFS bandwidth control 中，`burst_us` 和 `quota_us` 之间存在约束关系。当前验证逻辑在以下场景有问题：
1. 当 quota 减小到小于已配置的 burst 时，burst 不会被自动调整
2. 先写 burst 再写 quota 时，如果 burst > 旧 quota，会返回 `EINVAL`

这导致配置顺序依赖——先设 burst 还是先设 quota 会产生不同结果。

## 技术方案

v1 的方案是在 quota 变更时重置不兼容的 burst 值。

Michal Koutný 建议更好的方案：
- 移除验证中对 burst_us 与 quota_us 的耦合检查
- burst_us 只独立检查不超过 `max_bw_runtime_us`
- 在 `__refill_cfs_bandwidth_runtime()` 中执行 clamp：`min(cfs_b->runtime, cfs_b->quota + min(cfs_b->burst, cfs_b->quota))`

作者 Zhe Liu 同意该方案，计划发 v2 实现。

## 版本演进与当前进展

- v1：在 quota 变更时重置 burst
- v2（计划中）：改为在运行时 clamp，保留配置值

## Maintainer 意见与讨论焦点

Michal Koutný 的核心观点：用户配置的值不应丢失，clamp 应在执行时而非配置时进行。这保证了写入顺序无关性。

## 合入评估

- **likelihood**: medium（方向被认可，v2 方案更优雅，等待作者发 v2）
- **blocking_issues**: 需要 v2 实现新方案并更新 selftest
- **next_action**: 作者发 v2，包含新的 clamp 逻辑和 selftest 更新

## 效果评估

暂无性能数据。修复的是配置接口的正确性和一致性问题。

## 我可以参与的点

- 可以帮助编写 selftest 验证写入顺序无关性
- 可以在不同内核版本上测试 burst/quota 配置的行为一致性

## 参考链接

- lore thread: 未获取到

---
id: sched-20260826-008
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: unknown
lore_url: unknown
authors: [Zhe Liu]
maintainers_involved: [Michal Koutný]
current_version: v1
patch_series:
  - version: v1
    msgid: unknown
    date: 2026-08-26
    summary: "修复 burst/quota 不兼容时的配置顺序依赖问题"
    review_outcome: "Michal Koutný 建议运行时 clamp 替代验证时拒绝，作者同意"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要 v2 实现新方案"]
  next_action: "作者发 v2 实现运行时 clamp 并更新 selftest"
contribution_opportunities:
  - kind: testing
    description: "帮助编写 selftest 验证 burst/quota 写入顺序无关性"
generated_at: "2026-08-27T01:24:00"
source_email_count: 1
related_articles: []
tags: [cfs, cgroup]
---
