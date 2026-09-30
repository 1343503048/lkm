---
id: sched-20260930-004
date: '2026-09-30'
subject: 'sched_ext: Sync tools headers from the scx repo'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260930000422.3350352-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20260930000422.3350352-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260930000422.3350352-1-tj@kernel.org>
  date: '2026-09-30'
  summary: 2 补丁：同步 common/compat 与 autogen enum 头，新增 const-defs.h/features.bpf.h，转写
    scx_qmap cmask 调用
  review_outcome: 无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚未见应用进 sched_ext/for-7.4 的通告
  next_action: Tejun 自行应用进 sched_ext/for-7.4
contribution_opportunities:
- kind: review
  description: 核对 fetching atomics 位助手在无 JIT 降低平台的回退路径语义
- kind: testing
  description: 在非 x86（如 arm64）构建 tools/sched_ext 与 selftest 确认无架构假设破坏
generated_at: '2026-10-01T01:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Sync tools headers from the scx repo'
layout: article
---

> **subject**：`sched_ext: Sync tools headers from the scx repo`

## TL;DR

Tejun Heo 为 sched_ext/for-7.4 发的工具头文件同步补丁集（2 补丁）：内核侧 `tools/sched_ext/include` 与 scx 仓库 `scheds/include` 的共享 BPF 头自上次同步后分叉（内核给 `scx_bpf_cid_topo()` 等加了 size 参数、加了 lazy preemption/proxy-exec 标志与 `SCX_OPS_OPEN_OPTS()`，scx 侧则累积了 cid-form 调度器用的 cmask helpers 与 kfunc compat 包装），本系列把合并结果拷回内核。1/2 同步四个共享头 + 新增 `const-defs.h`/`features.bpf.h` 并转写 `scx_qmap` 的三操作数 cmask 调用；2/2 同步四个 autogen enum 头。已通过构建与逐文件 diff 验证，属维护性质同步。

## 背景与问题

内核与 scx 仓库的共享 BPF 头（`common.bpf.h`、`cid.bpf.h`、`compat.bpf.h`、`compat.h` 及 autogen enum 头）分叉：内核侧新增了 `scx_bpf_cid_topo()`/`scx_bpf_cid_node()` 的 size 参数、lazy preemption 与 proxy-exec 标志、`SCX_OPS_OPEN_OPTS()`；scx 侧（PR #3856）累积了 cid-form 调度器使用的 cmask helpers 与已改原型 kfunc 的 compat 包装。`scx_bpf_kick_cid()`/`scx_bpf_cidperf_set()` 改返回值类型但未改名，`scx_qmap` 已用 cmask helpers，而三操作数 `cmask_and()`/`cmask_andnot()` 尚未进入其 cid.bpf.h 副本，导致 `tools/sched_ext` 无法再对 scx 的头构建。

## 技术方案

1. **1/2 `sched_ext: Sync common and compat headers from the scx repo`**：同步 `cid.bpf.h`（cmask helpers、`bpf_arena_for()` 字循环、按 loader 探测结论取 fetching atomics 的位助手）、`common.bpf.h`（prolog probe 默认让 `is_migration_disabled()` 过度报告、cid-form open 宏重定向 probe 到 `bpf_scx_reg_cid()`）、`compat.bpf.h`/`compat.h`（`scx_bpf_kick_cid()`/`scx_bpf_cidperf_set()` 双 flavor 声明），新增 `const-defs.h`（每架构 cacheline 大小）与 `features.bpf.h`（loader 载入前探测的内核 feature bits），并把 `scx_qmap` 的五个 cmask 调用转成三操作数形式。
2. **2/2 `sched_ext: Sync tools autogen enum headers from the scx repo`**：同步四个 autogen enum 头，其任务状态查找此前位于被移除的 enum 类型下。

验证：构建内核、`tools/sched_ext` 与 sched_ext selftests 通过，逐文件 diff 显示每个共享文件与 scx 树一致。

## 版本演进与当前进展

v1 刚发出（cover `<20260930000422.3350352-1-tj@kernel.org>`；2/2 未进入当日缓存）。当日无回帖。

## Maintainer 意见与讨论焦点

当日无回帖。作者即 sched_ext 维护者本人，系列自投 `sched_ext/for-7.4`（基于 c6fe97c34a1a），属例行的头文件同步维护。

## 合入评估

*likelihood=high*。作者是 sched_ext 维护者、系列为机械性头同步且已通过全量构建与逐文件 diff 校验、目标是自家 for-7.4 分支；风险低（若不及时同步，scx 侧新 header 无法反向进入内核，工具继续构建失败）。*blocking_issues*：尚未见应用通告。*next_action*：Tejun 自行应用进 sched_ext/for-7.4。

## 效果评估

无性能数据；效果是恢复 `tools/sched_ext` 对 scx 头构建、把 cid-form 调度器所需的 cmask helpers 与 kfunc compat 引入内核侧。diffstat：11 文件 +837/−127 行。

## 我可以参与的点

- `review`：核对同步后的 `cid.bpf.h` cmask 位助手「按 loader 探测结论取 fetching atomics」在无 JIT 降低平台上的回退路径是否与内核 KF 语义一致。
- `testing`：在非 x86（如 arm64）上构建 `tools/sched_ext` 与 selftest，确认头同步无架构假设破坏。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20260930000422.3350352-1-tj@kernel.org/
- lore（1/2）: https://lore.kernel.org/all/20260930000422.3350352-2-tj@kernel.org/
- scx 侧 PR: https://github.com/sched-ext/scx/pull/3856
