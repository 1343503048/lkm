# sched/core: Avoid false migration warning for proxy donors

## TL;DR
Andrea Righi 从 proxy-execution 兼容 sched_ext 系列里抽出的一枚独立修复：proxy execution 会把一个 migration-disabled 的 blocked donor 的调度上下文挪到锁 owner 的 CPU 上，`set_task_cpu()` 对此无条件 `WARN_ON_ONCE(is_migration_disabled(p))`，造成误报。修复把「被 proxy 迁移的 blocked donor」从告警中排除，带 `Fixes:` 与 John Stultz 的 Acked-by，Peter 已认可单发。合入概率高。

## 背景与问题
proxy execution 允许把 blocked donor 的调度上下文（scheduling context）移到锁 owner 的 CPU，即使该 donor 处于 migration-disabled 状态——donor 并不在那里执行，其原始执行 CPU 仍记录在 `wake_cpu`。但 `set_task_cpu()` 对 migration-disabled 任务无条件 `WARN_ON_ONCE`，于是后续的 proxy 迁移或 wakeup 路径把 donor 送回原 CPU 时触发误报。Andrea 在 tip/master 上复现（`kernel/sched/core.c:3389` 的 `set_task_cpu`），复现器在 CPU1 建一个 mutex owner、在 CPU0 建一个 migration-disabled waiter，owner 释放锁时 `try_to_wake_up()` 通过 `set_task_cpu()` 把 waiter 送回 pinned 的 CPU0 即告警。该问题对上游主线同样存在，不依赖 sched_ext。

## 技术方案
在 `set_task_cpu()` 中新增 `proxy_migrated = sched_proxy_exec() && p->is_blocked && task_cpu(p) != p->wake_cpu`，把告警条件从 `WARN_ON_ONCE(is_migration_disabled(p))` 改为 `WARN_ON_ONCE(is_migration_disabled(p) && !proxy_migrated)`。proxy wakeup 路径会在清除 blocked 状态前恢复可执行放置，因此移动 blocked 调度上下文不违反 migration-disabled 执行上下文的约束。改动集中在 `kernel/sched/core.c`（8 insertions / 1 deletion）。

## 版本演进与当前进展
- **v1**（本日 105218，`<20260915184101.2621252-1-arighi@nvidia.com>`）：单枚独立补丁，携带 `Fixes: b049b81bdff6 ("sched: Handle blocked-waiter migration (and return migration)")` 与 `Acked-by: John Stultz`。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：认可把该修复独立成篇，表示「Right, or at the head with a Fixes tag on will do too. Thanks for checking!」——即同意用带 Fixes 标签的单发补丁落地。
- **John Stultz**：给出 `Acked-by`。
- 无遗留争议。

## 合入评估
likelihood=high。这是一个明确的误报修复，带 `Fixes:` 标签指向具体引入 commit，已获 sched 维护者 Peter Zijlstra 认可单发、John Stultz Acked-by，且在最新 tip/master 上复现确认。blocking_issues：无。next_action：待 Peter 收取进入 tip/sched/core（或 urgent）。

## 效果评估
复现器在未修复内核上稳定触发 `WARNING: kernel/sched/core.c:3389 at set_task_cpu+0x1d3/0x280`，调用栈为 `try_to_wake_up -> __mutex_unlock_slowpath -> owner_fn`；修复后该路径不再误报。属正确性修复，无性能量化数据。

## 我可以参与的点
- kind=testing：在带 proxy execution 的内核上运行复现器（mutex owner + migration-disabled waiter 场景），确认修复前告警、修复后消失。
- kind=review：核对 `proxy_migrated` 判定中 `task_cpu(p) != p->wake_cpu` 是否遗漏其它 blocked donor 迁移路径。

## 参考链接
- patch：https://lore.kernel.org/all/20260915184101.2621252-1-arighi@nvidia.com/
- 讨论起点（04/18 评审）：https://lore.kernel.org/all/20260915172417.GA2835410@noisy.programming.kicks-ass.net/

---
id: sched-20260916-001
date: '2026-09-16'
subject: 'sched/core: Avoid false migration warning for proxy donors'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260915184101.2621252-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260915184101.2621252-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260915184101.2621252-1-arighi@nvidia.com>'
    date: '2026-09-15'
    summary: '在 set_task_cpu() 中把被 proxy 迁移的 blocked donor 从 migration-disabled 告警中排除'
    review_outcome: 'Peter Zijlstra 认可单发，John Stultz Acked-by'
upstream_commit: null
fixes_commit: 'b049b81bdff6'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '待 Peter 收取进入 tip/sched/core'
contribution_opportunities:
  - kind: testing
    description: '运行 mutex owner + migration-disabled waiter 复现器，验证修复前后告警行为'
  - kind: review
    description: '核对 proxy_migrated 判定是否覆盖所有 blocked donor 迁移路径'
generated_at: '2026-09-17T09:00:00'
source_email_count: 4
related_articles: []
tags:
  - proxy_execution
---
