---
subject: 'selftests/sched_ext: Make allowed_cpus idle validation race-free'
id: sched-20260731-001
date: 2026-07-31
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260731090334.2911948-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/lkml/20260731090334.2911948-1-arighi@nvidia.com
authors:
- Andrea Righi
maintainers_involved:
- Kuba Piecuch
current_version: v2
patch_series:
- version: v2
  msgid: <20260731090334.2911948-1-arighi@nvidia.com>
  date: 2026-07-31
  summary: 'sched_ext: 在 ops.init() 之前启用 idle 跟踪并刷新在线 CPU 的 idle 掩码；selftest 增加竞态保护'
  review_outcome: Kuba 建议复用 scx_builtin_idle_enabled 静态键而非新增独立键；selftest 中建议在 enqueue
    回调也检查 idle 不变量
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需要复用现有静态键而非新增独立键（Kuba 建议）
  next_action: Andrea 已确认在 v3 中采纳 Kuba 的建议，合并静态键并在 enqueue 回调增加检查
contribution_opportunities: []
generated_at: '2026-07-31T16:30:00'
source_email_count: 6
related_articles: []
tags:
- sched_ext
title: 'selftests/sched_ext: Make allowed_cpus idle validation race-free'
layout: article
---

## TL;DR

sched_ext v2 修复：在 BPF 调度器的 ops.init() 回调执行前，内置 idle 掩码未正确初始化，导致 ops.init() 可能观察到错误的 idle CPU 状态。Andrea Righi (NVIDIA) 发出 v2 补丁系列，包含核心修复和 selftest 竞态修复。Kuba Piecuch (Google) 已 review 并建议在 v3 中合并静态键，Andrea 已确认采纳。合入可能性高。

## 背景与问题

sched_ext 的内置 idle 跟踪机制在初始化时存在时序问题：idle 掩码在重置时将所有在线 CPU 标记为 idle，但 idle 状态跟踪要到调度器完全启用后才开始。这导致 ops.init() 回调执行时可能将忙碌的 CPU 误判为 idle，这些 CPU 会持续被错误地广播为 idle 状态，直到下一次 idle 转换发生。

此外，selftest 中的 allowed_cpus idle 验证存在竞态条件，需要在测试中增加保护。

## 技术方案

**Patch 1/2 — sched_ext: Initialize idle masks before ops.init()**

- 新增 `scx_idle_tracking_enabled` 静态键，在 ops.init() 之前启用 idle 跟踪
- 在启用时对每个在线 CPU 在其 rq lock 下执行刷新，确保 CPU idle 状态准确
- 保持 ops.update_idle() 通知在调度器完全启用前禁用
- 修改 `scx_update_idle()` 内联函数使用 `static_branch_unlikely(&scx_idle_tracking_enabled)` 替代 `scx_enabled()` 检查

**Patch 2/2 — selftests/sched_ext: Make allowed_cpus idle validation race-free**

- 在 selftest 中增加竞态保护，确保 idle 验证测试的可靠性

## 版本演进与当前进展

- **v2**（2026-07-31）：当前版本。引入独立静态键 `scx_idle_tracking_enabled` 控制早期 idle 跟踪，selftest 增加竞态保护
- v2 已收到 Kuba Piecuch 的 review 反馈

## Maintainer 意见与讨论焦点

**Kuba Piecuch (Google)** 提出两个关键建议：

1. **静态键复用**：质疑为何不复用现有的 `scx_builtin_idle_enabled` 而非要新增独立静态键。Kuba 认为如果用户自己做 idle CPU 跟踪（此时 scx_builtin_idle_enabled 关闭），SCX 跟踪 idle CPU 就没有意义。Andrea 回应称 `__scx_update_idle()` 还会传递 ops.update_idle() 回调，但同意可以保留现有 `scx_enabled()` 检查用于该场景，在 v3 中合并。

2. **selftest 增强**：建议在 ops.enqueue() 中也检查 idle 不变量（CPU 不应被广播为 idle），并建议使用 `scx_bpf_get_idle_cpumask()` + `bpf_cpumask_test_cpu()` 做不修改掩码的检查。Andrea 同意在 v3 中添加。

## 合入评估

- **likelihood: high** — 问题明确，修复方向得到认可，作者已承诺在 v3 中采纳所有 review 意见
- **blocking_issues**: 需要合并静态键（v3 解决）
- **next_action**: 等待 Andrea 发出 v3

## 效果评估

暂无效果数据。此修复主要解决正确性问题，非性能优化。

## 我可以参与的点

当前阶段暂无明显参与空间。v3 预计很快发出，修复逻辑清晰且 review 进展顺利。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260731090334.2911948-1-arighi@nvidia.com
