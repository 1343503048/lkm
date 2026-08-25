---
id: sched-20260821-006
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260821103519.535987-1-changwoo@igalia.com>
lore_url: https://lore.kernel.org/lkml/20260821103519.535987-1-changwoo@igalia.com/
authors:
- Changwoo Min
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260821103519.535987-1-changwoo@igalia.com>
  date: 2026-08-21
  summary: 引入 scx_cgroup_set_bw_mutex 串行化 SCX 侧 cpu.max 写入
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 review
contribution_opportunities:
- kind: testing
  description: 测试多线程并发写入 cpu.max 验证 SCX 修复
generated_at: '2026-08-21T10:00:00'
source_email_count: 1
related_articles:
- sched-20260821-001
tags:
- sched_ext
- cgroup
- race_condition
title: 并发写入同一 cgroup 的 cpu.max 会导致 SCX 侧的 `ops.cgroup_set_bandwidth()` 回调和 `tg->scx....
layout: article
---

## TL;DR

并发写入同一 cgroup 的 cpu.max 会导致 SCX 侧的 `ops.cgroup_set_bandwidth()` 回调和 `tg->scx.bw_*` 缓存值交错，Changwoo Min 引入 `scx_cgroup_set_bw_mutex` 串行化 SCX 侧更新，作为 CFS `cfs_constraints_mutex` 的 SCX 对等物。

## 背景与问题

cgroup 和 kernfs 层不对同一 cgroup 的 cpu.max 并发写入做串行化——`cgroup_file_write()` 调用 `cft->write` 时不持有 `cgroup_mutex`，kernfs 仅对同一打开文件串行化。`tg_set_cfs_bandwidth()` 在 CFS 侧用 `cfs_constraints_mutex` 串行化，但 `scx_group_set_bandwidth()` 之后仅持有 `scx_cgroup_ops_rwsem`（读锁），不串行化并发写入者。

这导致：
- `ops.cgroup_set_bandwidth()` 回调乱序执行
- 64 位 `bw_*` 存储在 32 位系统上可能撕裂
- 缓存状态与最后写入者不一致

该问题由 Sashiko bot 报告。

## 技术方案

引入 `scx_cgroup_set_bw_mutex`，在 `scx_group_set_bandwidth()` 中跨回调和存储持有，确保每个写入者原子地应用更新，顺序一致——作为 CFS `cfs_constraints_mutex` 的 SCX 对等物。

```c
static DEFINE_MUTEX(scx_cgroup_set_bw_mutex);
// 在 scx_group_set_bandwidth() 中：
percpu_down_read(&scx_cgroup_ops_rwsem);
mutex_lock(&scx_cgroup_set_bw_mutex);
// ... callback + stores ...
mutex_unlock(&scx_cgroup_set_bw_mutex);
```

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无 review 意见。

## 合入评估

- **likelihood**: high
- **blocking_issues**: 无
- **next_action**: 等待 review

该补丁与 sched-20260821-001（Lift cgroup update locking to core）互补：001 修复 CFS 侧锁提升，本补丁修复 SCX 侧串行化。

## 效果评估

修复并发竞态，无性能数据。

## 我可以参与的点

- 测试多线程并发写入 cpu.max 的场景，验证 SCX 调度器下的修复效果
- 检查是否还有其他 cgroup 写路径存在类似 SCX 侧串行化缺口

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821103519.535987-1-changwoo@igalia.com/
- Sashiko bot report: https://lore.kernel.org/sched-ext/20260817172131.BCDA51F000E9@smtp.kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
