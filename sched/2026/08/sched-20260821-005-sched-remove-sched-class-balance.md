## TL;DR

PeterZ 提议移除 `sched_class::balance()` 回调，这是 core_sched 重构的一部分。ByteDance 的 Xuewen Yan 提供了带宽测试脚本帮助验证，讨论仍在进行中。

## 背景与问题

`sched_class::balance()` 是调度类用于负载均衡的回调。随着调度器架构演进（特别是 core scheduling 和 single runqueue 的引入），这个回调的必要性受到质疑。PeterZ 提议将其移除，简化调度类接口。

## 技术方案

移除 `sched_class::balance()` 回调，将相关功能整合到调度核心或其他机制中。这是结构性重构，不改变外部行为。

## 版本演进与当前进展

v1 讨论中。Xuewen Yan (ByteDance) 分享了自建的带宽测试脚本，用于验证移除 balance 回调后的性能影响。测试使用 quota 设置，问题可以在有无 quota 的情况下触发。测试中使用 `nop`（用户态 CPU 消耗器：`while (1) { cpu_relax(); }`）作为负载。

## Maintainer 意见与讨论焦点

PeterZ 对 Xuewen Yan 提供的测试脚本表示感谢。讨论主要围绕测试验证方法和 core_sched 工具使用。PeterZ 提到使用 `util-linux/coresched` 工具进行测试。

## 合入评估

- **likelihood**: medium
- **blocking_issues**: 需要充分的测试验证确保不引入回退
- **next_action**: 继续收集测试反馈

## 效果评估

Xuewen Yan 提供了带宽测试脚本但具体数字未在邮件中完整披露。测试关注 quota 设置下的调度行为。

## 我可以参与的点

- 使用提供的测试脚本在自己的硬件上验证 balance 回调移除的影响
- 关注 core_sched 场景下的行为变化

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260820154052.GB4120091@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260821-005
date: 2026-08-21
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20260820154052.GB4120091@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/lkml/20260820154052.GB4120091@noisy.programming.kicks-ass.net/"
authors: ["Peter Zijlstra"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260820154052.GB4120091@noisy.programming.kicks-ass.net>"
    date: 2026-08-20
    summary: "提议移除 sched_class::balance() 回调"
    review_outcome: "Xuewen Yan 提供带宽测试脚本，讨论进行中"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "需要充分测试验证"
  next_action: "继续收集测试反馈"
contribution_opportunities:
  - kind: testing
    description: "使用测试脚本验证 balance 回调移除的影响"
generated_at: "2026-08-21T10:00:00"
source_email_count: 3
related_articles: []
tags: ["sched/core", "core_sched"]
---
