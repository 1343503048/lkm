---
id: sched-20260825-003
date: 2026-08-25
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260825053648.EF7D41F000E9@smtp.kernel.org>
lore_url: https://lore.kernel.org/r/20260825053648.EF7D41F000E9@smtp.kernel.org
authors:
- Andrea Righi
maintainers_involved:
- Tao Cui
current_version: v1
patch_series:
- version: v1
  msgid: <20260825053648.EF7D41F000E9@smtp.kernel.org>
  date: 2026-08-25
  summary: 引入 per-task_group knob_mutex 串行化 cgroup knob 更新，修复并发写入竞态
  review_outcome: Andrea 自维护的修复，等待 Tejun ack
upstream_commit: null
fixes_commit: '819513666966'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun Heo ack 并 apply 到 sched_ext/for-7.3-fixes
contribution_opportunities: []
generated_at: '2026-08-27T10:00:00'
source_email_count: 1
related_articles:
- sched-20260825-004
tags:
- sched_ext
- cgroup
title: 'sched_ext: Serialize cgroup knob updates'
layout: article
---

## TL;DR

Andrea Righi 发出 sched_ext/for-7.3-fixes 分支的修复 patch：为每个 task_group 引入 `knob_mutex`，串行化 cgroup 权重/空闲/带宽的更新操作，防止并发 cgroup knob 写入导致 sched_ext 通知与核心调度器状态不一致。由 Sashiko bot 报告的竞态问题触发。

## 背景与问题

sched_ext 的 cgroup 接口（`cpu.weight`、`cpu.idle`、`cpu.cfs_quota_us` 等）允许并发写入。当多个 cgroup knob 同时更新时，核心调度器的状态变更和对应的 `ops.cgroup_set_*()` BPF 回调可能以不同顺序完成，导致：
- BPF 调度器看到的 cgroup 状态与核心调度器不一致
- 竞态条件可能引发难以复现的 bug

Sashiko bot 检测到该竞态并报告。

## 技术方案

- 在 `struct scx_task_group` 中新增 `knob_mutex`（struct mutex）
- 在 `scx_tg_init()` 中初始化
- 所有 cgroup knob 写入路径（weight、idle、bandwidth）持锁串行化
- 修改 4 个文件：`include/linux/sched/ext.h`、`kernel/sched/core.c`、`kernel/sched/ext/ext.c`、`kernel/sched/ext/ext.h`

Fixes 标签指向三个 commit：cgroup 支持初始提交、cgroup_set_idle 实现、cgroup 带宽控制接口。

## 版本演进与当前进展

v1，直接发到 `sched_ext/for-7.3-fixes` 分支，表明 Andrea 认为这是 7.3 周期的修复。

## Maintainer 意见与讨论焦点

- Andrea Righi 是 sched_ext 的核心维护者之一，该 patch 直接针对 Sashiko bot 报告的问题
- Tao Cui 的 "Allow ops.cgroup_set_weight/idle() to be sleepable" patch 依赖此修复（Andrea 明确表示先解决竞态再推进 sleepable 回调）

## 合入评估

- **likelihood: merged** — 已发到 for-7.3-fixes 分支，Andrea 自己维护的 sched_ext 子系统
- **blocking_issues**: 无
- **next_action**: 等待 Tejun Heo ack/apply

## 效果评估

暂无效果数据。这是竞态修复，正确性修复而非性能优化。

## 我可以参与的点

当前阶段暂无明显参与空间。这是维护者直接修复的竞态问题，已经定向发出。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260825053648.EF7D41F000E9@smtp.kernel.org
- Sashiko report: https://lore.kernel.org/r/20260825053648.EF7D41F000E9@smtp.kernel.org
- tip-bot commit: 未获取到
