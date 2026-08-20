---
id: sched-20260818-004
subject: 'sched_ext: allow ops.cgroup_set_bandwidth() to be sleepable'
date: 2026-08-18
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: <20260817170941.668571-1-changwoo@igalia.com>
lore_url: https://lore.kernel.org/r/20260817170941.668571-1-changwoo@igalia.com
authors:
- Changwoo Min
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260817170941.668571-1-changwoo@igalia.com>
  date: 2026-08-17
  summary: 将 cgroup_set_bandwidth() 加入 sleepable 白名单，新增 BTF marker 供 userspace 探测。
  review_outcome: Tejun 要求加 __retain、统一 marker 前缀并集中放置。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 仅差作者按 Tejun 建议调整 marker 格式
  next_action: 作者出 v2 加 __retain、统一 marker 前缀。
contribution_opportunities: []
generated_at: '2026-08-19T00:10:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
- cgroup
- bandwidth
title: 'sched_ext: allow ops.cgroup_set_bandwidth() to be sleepable'
layout: article
---

## TL;DR
Changwoo Min 提交单 patch 将 `ops.cgroup_set_bandwidth()` 加入 sched_ext cgroup 操作的 sleepable 白名单，使 BPF 调度器在 cgroup 获得 cpu.max 限制时可按需分配内存，而非预保留。Tejun Heo review 要求加 `__retain`、统一 marker 前缀并集中放置。

## 背景与问题
`ops.cgroup_set_bandwidth()` 从 `scx_group_set_bandwidth()` 调用，运行在 `cpu.max` cgroup 接口写入路径（`tg_set_bandwidth()`）的进程上下文中。此时 `tg_set_cfs_bandwidth()` 已返回，仅持有 `percpu_down_read(&scx_cgroup_ops_rwsem)`（读侧可睡眠）。调用点本身可睡眠，类似 `ops.cgroup_init()`。

但 `bpf_scx_check_member()` 拒绝不在白名单上的 sleepable program，导致 BPF 调度器无法在 cgroup 获得 cpu.max 限制时动态分配——必须预保留内存给不能分配的回调。

## 技术方案
- 将 `cgroup_set_bandwidth()` 加入 sleepable 白名单。
- 新增 `scx_cgroup_set_bandwidth_may_sleep()` marker 函数：无调用者、无功能，但其 BTF 符号可供 userspace 探测内核是否支持此特性。
- 改动：`kernel/sched/ext/ext.c`（+10）、`ext.h`（+1）、`internal.h`（1 行修改），共 3 文件 +12/-1。

## 版本演进与当前进展
- v1（2026-08-17 发出），本日收到 Tejun review。
- Tejun 要求：
  - 加 `__retain`（`CONFIG_LD_DEAD_CODE_DATA_ELIMINATION` 下 linker 仍会 GC 掉 `__used`  alone 不够的 section）。
  - marker 函数统一前缀（如 `scx_compat_marker_`）并集中放在 ext.c 末尾靠近 module init 的位置。

## Maintainer 意见与讨论焦点
- Tejun Heo：
  - 要求加 `__retain` 确保 marker 不被 linker 丢弃。
  - 建议给 marker 统一前缀 `scx_compat_marker_` 并集中放置，因为"we'll likely accumulate more of these markers over time"。
  - 方向认可，无实质反对。

## 合入评估
合入可能性高。改动小（+12/-1）、方向明确、maintainer 仅有格式调整建议。作者回应后预计可快速合入。

## 效果评估
无性能数据。功能改进：BPF 调度器不再需要为 cgroup_set_bandwidth 回调预保留内存。

## 我可以参与的点
- 当前阶段改动明确，参与空间有限。可关注 v2 是否按 Tejun 建议统一 marker 前缀。

## 参考链接
- lore thread: https://lore.kernel.org/r/20260817170941.668571-1-changwoo@igalia.com
- tip-bot commit: 未获取到
- stable backport: 未获取到
