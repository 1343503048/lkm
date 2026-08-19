# sched/fair: Prefer fully idle cores for NOHZ balancing

## TL;DR

Andrea Righi 的 v2 补丁优化 NOHZ idle load balancer 的 CPU 选择：优先选择整个 SMT core 都 idle 的 CPU，避免唤醒部分空闲 core 的 sibling。在 NVIDIA Vera 的 GEMM 测试中从 6.2 TFLOP/s 提升到 9.4 TFLOP/s（+51%）。本文为增量更新，完整背景见 sched-20260729-001。

## 背景与问题

`find_new_ilb()` 选择第一个 idle 的 housekeeping CPU，不考虑是否另一个 thread 在同一物理 core 上运行。在 SMT 系统上，idle load balancer 可能激活两个 sibling，即使另一个 housekeeping CPU 有完全空闲的 core。

在 NVIDIA Olympus core（Vera 系统）上，短暂激活 otherwise idle 的 sibling 会降低另一 sibling 的性能，且这种影响在 sibling 进入 WFI 后不会立即消失——需要 10K cycles 的 qualification interval 才能恢复全单线程性能。反复短暂唤醒 sibling 会持续造成干扰。

## 技术方案

v2 方案：
- 优先选择 idle housekeeping CPU 且其整个 SMT core 都 idle
- 保留 first idle CPU 作为 fallback，确保 NOHZ balancing 能继续推进
- 一旦检查过部分繁忙的 core，跳过其剩余 SMT sibling，避免在宽 SMT 系统上重复检查

## 版本演进与当前进展

- v1 (2026-07-29): 初始提案，已在 20260729 分析
- v2 (2026-07-30): 优化 SMT sibling 跳过逻辑

## Maintainer 意见与讨论焦点

暂无新的 review 意见。

## 合入评估

- **likelihood**: medium
- 性能提升显著（+51%），但针对特定硬件
- 需要更多平台验证

## 效果评估

- GEMM benchmark（1 CPU-intensive task per SMT core）：
  - Before: ~6.2 TFLOP/s
  - After: ~9.4 TFLOP/s
  - **提升约 51%**

注意：此偏好可能唤醒完全空闲的物理 core 而非使用活跃 core 的 idle sibling，可能增加 ILB wakeup latency 或某些架构的能耗。

## 我可以参与的点

- **多平台测试**：在不同 SMT 系统（x86 SMT-2, Power SMT-4/8）上测试 ILB 选择行为和性能影响
- **能耗评估**：测量唤醒全空闲 core vs 使用活跃 core sibling 的能耗差异

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
- related: sched-20260729-001

---
subject: "sched/fair: Prefer fully idle cores for NOHZ balancing"
id: sched-20260730-008
date: 2026-07-30
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<sched-fair-nohz-idle-cores-v2...@nvidia.com>"
lore_url: "https://lore.kernel.org/lkml/sched-fair-nohz-idle-cores-v2"
authors: [Andrea Righi]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<sched-fair-nohz-idle-cores-v1...>"
    date: 2026-07-29
    summary: "Initial proposal to prefer fully idle cores for NOHZ balancing"
    review_outcome: "v1 covered on 20260729"
  - version: v2
    msgid: "<sched-fair-nohz-idle-cores-v2...@nvidia.com>"
    date: 2026-07-30
    summary: "v2 with refinements for SMT sibling skipping"
    review_outcome: "Pending review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Need review/benchmark data on NVIDIA Vera"]
  next_action: "Get review from sched maintainers"
contribution_opportunities:
  - kind: testing
    description: "Test on SMT systems to validate ILB core selection behavior"
generated_at: "2026-07-31T00:10:00"
source_email_count: 1
related_articles: [sched-20260729-001]
tags: [cfs, load_balance, nohz, perf, hyperthreading]
---
