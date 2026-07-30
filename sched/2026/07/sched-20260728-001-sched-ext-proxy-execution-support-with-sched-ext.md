---
id: sched-20260728-001
date: 2026-07-28
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260728154425.1549660-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/r/20260728154425.1549660-1-arighi@nvidia.com"
authors: [Andrea Righi]
maintainers_involved: [Tejun Heo, John Stultz]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260728154425.1549660-1-arighi@nvidia.com>"
    date: 2026-07-28
    summary: "15-patch series enabling proxy execution with sched_ext: split curr/donor references, handle proxy-exec races in DSQ transfers, delegate blocked donor admission to BPF schedulers, add selftest and scx_qmap support"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要 Tejun Heo 等 sched_ext maintainer review", "涉及 sched core 与 sched_ext 的交互，需要 Peter Zijlstra 确认"]
  next_action: "等待 maintainer review 反馈"
contribution_opportunities:
  - kind: testing
    description: "在启用 SCHED_PROXY_EXEC + SCHED_CLASS_EXT 的配置下测试 proxy execution 场景（如 stress-ng --pipeherd），验证无 sleeping-while-atomic 警告"
  - kind: review
    description: "review patch 10/15 中 proxy-exec races in remote DSQ transfers 的竞态处理逻辑"
generated_at: "2026-07-30T10:00:00"
source_email_count: 10
related_articles: []
tags: [sched_ext]
---

## TL;DR

Andrea Righi (NVIDIA) 发出 15-patch 系列，目标是让 proxy execution（代理执行）与 sched_ext 共存。此前 SCHED_PROXY_EXEC 显式依赖 `!SCHED_CLASS_EXT`，本系列移除该限制，让 BPF 调度器能正确处理 blocked donor 的入队和 DSQ 转移竞态。v1 刚发出，暂无 review。

## 背景与问题

Proxy execution 是一种解决优先级反转的机制：当 mutex owner 被阻塞时，blocked donor 将自己的调度上下文（优先级、runtime budget）"借给" lock owner 执行。此前该特性与 sched_ext 互斥（Kconfig 中 `depends on !SCHED_CLASS_EXT`），原因是 sched_ext 的 DSQ 分发路径无法感知"调度上下文与执行上下文分离"的情况。

随着 sched_ext 在 Android/ChromeOS 等场景的普及，proxy execution 需要能在 BPF 调度器下工作。

## 技术方案

系列分三层：

1. **sched core 准备**（patch 01-06）：
   - 排除 blocked proxy donor 的 false migration warning（`set_task_cpu()` 中对 `is_migration_disabled` 的 WARN 不再对 proxy-migrated 的 blocked task 触发）
   - 新增 `prepare_switch()` class callback，让 incoming class 在 dequeue 前做准备
   - 在 `sched_change_begin()` 中传入 incoming class

2. **sched_ext 核心适配**（patch 09-12）：
   - 泛化 reject DSQ reenqueue 路径（不再限于 sub-scheduler cap 失败）
   - 处理 proxy-exec 在 remote DSQ transfer 中的竞态：task 可能在 holding_cpu 未清除时就开始物理执行，需要在获取 source rq lock 后重新检查状态
   - 正确拆分 curr（执行上下文）与 donor（调度上下文）引用
   - 定义 `SCX_OPS_ENQ_BLOCKED` flag，让 BPF 调度器选择是否接管 blocked donor

3. **验证与使能**（patch 13-15）：
   - 添加 selftest 验证 blocked donor admission
   - scx_qmap 示例调度器添加 proxy execution 支持
   - 移除 Kconfig 中 `!SCHED_CLASS_EXT` 依赖

关键设计取舍：blocked donor 的入队通过 `SCX_ENQ_BLOCKED` flag 走 `ops.enqueue()`，让 BPF 调度器决定 DSQ/CPU/排序，而非内核硬编码路径。这保持了 sched_ext 的"BPF 策略优先"哲学。

## 版本演进与当前进展

v1（2026-07-28）：首次发出完整 15-patch 系列。此前 proxy execution 由 John Stultz 主导开发，本系列是在其基础上做 sched_ext 适配。多个 patch 带有 `Acked-by: John Stultz` 和 `Suggested-by: Tejun Heo`，说明方向已获核心开发者认可。

## Maintainer 意见与讨论焦点

v1 刚发出，暂无公开 review 意见。但从 patch 中的 Signed-off/Acked-by/Suggested-by 链可推断：
- John Stultz（proxy execution 原作者）已 Ack 多个 patch
- Tejun Heo（sched_ext maintainer）建议了 prepare_switch() 和 proxy_resolved() 的设计方向
- 最终合入需要 Peter Zijlstra 对 sched core 改动的确认

## 合入评估

可能性中等。方向已获核心人员认可（Acked-by + Suggested-by），但 15 个 patch 涉及 sched core 与 sched_ext 的深度交互，review 周期可能较长。主要风险点：
- patch 10 的竞态处理逻辑复杂，可能需要多轮迭代
- sched core 改动（prepare_switch 等）需要 PeterZ 确认不影响其他调度类

## 效果评估

暂无 benchmark 数据。patch 10 提到 stress-ng --pipeherd 可触发竞态（无本 patch 时出现 sleeping-while-atomic + lockdep corruption），但未给出修复后的性能数据。

## 我可以参与的点

- **测试**：在启用 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_SCHED_CLASS_EXT=y` 的内核上跑 stress-ng --pipeherd 和 rt-mutex 压力测试，验证无警告/无 lockdep 报错，结果回帖到邮件列表
- **Review**：patch 10（remote DSQ transfer 竞态）和 patch 12（SCX_OPS_ENQ_BLOCKED admission contract）逻辑较复杂，可以帮忙 review 边界条件

## 参考链接

- lore thread: https://lore.kernel.org/r/20260728154425.1549660-1-arighi@nvidia.com
- tip-bot commit: 未获取到
- stable backport: 未获取到
