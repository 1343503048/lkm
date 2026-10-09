---
id: sched-20261001-013
date: '2026-10-01'
subject: 'sched_ext: Sync tools headers from the scx repo'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260930000422.3350352-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/38cd218666e72139f06ea0155b988722@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260930000422.3350352-1-tj@kernel.org>
  date: '2026-09-30'
  summary: 同步共享 BPF 头与 autogen enum 头回内核，恢复 tools/sched_ext 构建
  review_outcome: 10-01 Tejun 应用到 sched_ext/for-7.4
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪 for-7.4 进 v7.4 合入窗口
contribution_opportunities: []
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260930-004
tags:
- sched_ext
title: 'sched_ext: Sync tools headers from the scx repo'
layout: article
---

> **subject**：`sched_ext: Sync tools headers from the scx repo`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-004-sched-ext-sync-tools-headers-from-the-scx-repo.html">sched-20260930-004</a>：Tejun Heo 为 sched_ext/for-7.4 发的工具头文件同步补丁集（2 补丁）——把内核 `tools/sched_ext/include` 与 scx 仓库 `scheds/include` 分叉的共享 BPF 头合并结果拷回内核（内核侧 size 参数/新标志 vs scx 侧 cmask helpers/compat 包装），恢复 `tools/sched_ext` 对 scx 头的构建能力；已通过构建与逐文件 diff 验证。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-013-sched-ext-sync-tools-headers-from-the-scx-repo.html">sched-20261001-013</a>（今天）：Tejun 回帖「Applied to sched_ext/for-7.4.」——系列收取完成，同步落地。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-004-sched-ext-sync-tools-headers-from-the-scx-repo.html">sched-20260930-004</a>）内核与 scx 仓库的共享 BPF 头（`common.bpf.h`、`cid.bpf.h`、`compat.bpf.h`、`compat.h` 及 autogen enum 头）分叉：内核侧新增 `scx_bpf_cid_topo()`/`scx_bpf_cid_node()` 的 size 参数、lazy preemption 与 proxy-exec 标志、`SCX_OPS_OPEN_OPTS()`；scx 侧（PR #3856）累积 cid-form 调度器的 cmask helpers 与已改原型 kfunc 的 compat 包装。`scx_bpf_kick_cid()`/`scx_bpf_cidperf_set()` 改返回值类型但未改名、`scx_qmap` 已用 cmask helpers 而三操作数版本未进内核副本，导致 `tools/sched_ext` 无法再对 scx 头构建。今天无新背景，事件是收取落地。

## 技术方案

（承接）1/2 同步四个共享头并新增 `const-defs.h`/`features.bpf.h`、转写 `scx_qmap` 的三操作数 cmask 调用；2/2 同步四个 autogen enum 头。构建内核、`tools/sched_ext` 与 sched_ext selftests 通过，逐文件 diff 确认与 scx 树一致。今天无代码变更。

## 版本演进与当前进展

- v1（09-30，`<20260930000422.3350352-1-tj@kernel.org>`）：2 补丁，当日无回帖。
- 10-01：Tejun 应用到 `sched_ext/for-7.4`（`<38cd218666e72139f06ea0155b988722@kernel.org>`）。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者，作者本人）：「Applied to sched_ext/for-7.4. Thanks.」——例行维护性同步的收取完成，无附加意见。
- 无 NAK、无未决争议。

## 合入评估

*likelihood=merged*。维护者把自家机械性头同步收进 `sched_ext/for-7.4`，流程闭环；将随 for-7.4 进入 v7.4 合入窗口。*blocking_issues*：无。*next_action*：跟踪 for-7.4 进主线即可，无需参与。

## 效果评估

本日无新数据。既有信息（09-30）：效果为恢复 `tools/sched_ext` 对 scx 头的构建、把 cmask helpers 与 kfunc compat 引入内核侧；diffstat 11 文件 +837/−127。

## 我可以参与的点

无实质参与空间（维护者自维护例程，已收取）。

## 参考链接

- Tejun 的收取通告: https://lore.kernel.org/all/38cd218666e72139f06ea0155b988722@kernel.org/
- v1 cover: https://lore.kernel.org/all/20260930000422.3350352-1-tj@kernel.org/
