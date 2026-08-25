# sched: Flatten the pick

## TL;DR
Szabina 在 s390 LPAR（32 vCPU）上对 "Flatten the pick" v3 系列做了详细 benchmark（schbench、sysbench、hackbench），含 stress-ng 并行负载。关键发现：无并行负载时结果普遍正面（高线程数最高 -9.55%），但 stress-ng 并行时低线程数场景出现回退（最高 +2.36%），且 stress-ng 自身也回退。K Prateek Nayak 询问测试基线 commit。

## 背景与问题
该系列将 CFS 从多层 cgroup rq 结构迁移到单 rq 模型（"flat hierarchy"），目标是简化 pick 路径、减少锁竞争。前几版已在 x86 上展示正面结果，本日新增 s390 平台数据。

## 技术方案
将 cgroup 层级的多层 `cfs_rq` 统一为单个 runqueue，消除 pick 路径上的层级遍历开销。涉及 `account_cfs_rq_runtime()` 统一、vruntime 更新修正、抢占位优化等。

## 版本演进与当前进展
- v3 当前。本日（08-18）Szabina 发出 s390 平台完整 benchmark 数据。
- K Prateek Nayak 询问测试基线：是否使用 tip:sched/core at `68e3748781`（"sched/fair: Fix flat hierarchy"）还是 `85570f10a4c6`（"sched/eevdf: Move to a single runqueue"），指出 vruntime 更新修正和 Vincent 的抢占位优化可能影响结果。

## Maintainer 意见与讨论焦点
- K Prateek Nayak：询问测试基线 commit，暗示基线选择可能影响结论。
- 作者报告了 stress-ng 并行场景下的性能权衡——单 rq 在高负载时优势更大，但低负载时有回退。

## 合入评估
s390 数据整体正面但有条件：无并行负载时好，有并行负载时低线程数回退。需要更多平台数据确认是否为 s390 特有问题。maintainer 关注基线 commit 选择。

## 效果评估
s390 LPAR 32 vCPU，fedora 43，hackbench（phoronix-test-suite）：

**无并行负载（concur 模式）**：
- 高线程数（8-16 thread）：-6% ~ -9.5%
- 低线程数（1-2 thread）：基本持平或微幅回退（+0.4% ~ +1.4%）

**stress-ng 50% 并行**：
- 高线程数仍改善（-6% ~ -8%）
- 低线程数回退加剧（+0.8% ~ +2.4%）
- stress-ng 自身也回退

数据 CV < 2.5%（大部分情况），作者标注了 CV 较高的情况。

## 我可以参与的点
- 在其他平台（x86、ARM64）复跑相同 benchmark 验证是否为 s390 特性。
- 分析低线程数回退的根因——可能与单 rq 锁竞争模式变化有关。

## 参考链接
- lore thread: https://lore.kernel.org/r/fecf5eb215b4b86bec11ca47eb6b5b17f5e0fea5.camel@amd.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260818-005
subject: "sched: Flatten the pick — v3 s390 benchmark results"
date: 2026-08-18
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: "<fecf5eb215b4b86bec11ca47eb6b5b17f5e0fea5.cam>"
lore_url: "https://lore.kernel.org/r/fecf5eb215b4b86bec11ca47eb6b5b17f5e0fea5.cam"
authors: [Szabina]
maintainers_involved: [Peter Zijlstra, K Prateek Nayak]
current_version: v3
patch_series:
  - version: v3
    msgid: "<fecf5eb215b4b86bec11ca47eb6b5b17f5e0fea5.cam>"
    date: 2026-08-18
    summary: "s390 平台 benchmark 数据：无并行负载正面，stress-ng 并行时低线程数回退。"
    review_outcome: "K Prateek 询问测试基线 commit。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: [s390 数据有条件性回退需解释；需更多平台数据确认通用性]
  next_action: "作者回应基线 commit 选择；更多平台 benchmark 数据。"
contribution_opportunities:
  - kind: testing
    description: "在 x86/ARM64 平台复跑相同 benchmark 验证是否为 s390 特性。"
  - kind: discussion
    description: "分析低线程数回退根因——可能与单 rq 锁竞争模式变化有关。"
generated_at: "2026-08-19T00:10:00"
source_email_count: 2
related_articles: []
tags: [sched/fair, cgroup, load_balance]
---
