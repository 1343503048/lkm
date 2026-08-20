---
id: sched-20260817-002
date: 2026-08-17
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <uid-43819@qq-imap>
lore_url: 未获取到
authors:
- Changwoo Min
- Gavin Guo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-43819@qq-imap>
  date: 2026-08-17
  summary: 把 sched-ext/scx 树中先落地的两处 compat.bpf.h 修复同步回内核树：peek 按内核版本门控、新增 reenqueue_from_anywhere
    helper。
  review_outcome: v1 刚发出，暂无 review 意见。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 纯工具头文件同步，无核心逻辑改动
  next_action: 等待 Tejun 自身 apply（维护者即作者侧）。
contribution_opportunities:
- kind: review
  description: 可核对 7.1.0 版本门控下限是否与上游 scx 树一致，避免旧内核仍走有 bug 的 peek 路径。
generated_at: '2026-08-18T00:10:00'
source_email_count: 1
related_articles:
- sched-20260815-010
- sched-20260815-011
tags:
- sched_ext
title: 'sched_ext: sync compat.bpf.h peek/reenqueue fixes from sched-ext/scx'
layout: article
---

## TL;DR
Changwoo Min 把 `sched-ext/scx` 参考树中先落地的两处 `compat.bpf.h` 修复同步回内核树 `tools/sched_ext/include/scx/compat.bpf.h`：① 把无锁 `scx_bpf_dsq_peek()` 门控在 kernel >= 7.1.0（其 stale task-pointer bug 已在 2f2ea7709266 / 71d7847cad44 修复，旧内核回退到 `bpf_iter_scx_dsq`）；② 新增 `scx_bpf_reenqueue_local_from_anywhere()` 并优先用通用 `scx_bpf_dsq_reenq()`，给任意上下文调用者一个受支持的入口（不可用返回 `-ENOTSUP`）。与 08-15 系列 010/011 同属 sched_ext kfunc/compat 一致性维护。

## 背景与问题
`compat.bpf.h` 是 BPF 调度器兼容不同内核版本 kfunc 的桥接头文件，参考实现以 `sched-ext/scx` 树为准。两处修复先在该树落地但未同步回内核树，导致内核树里的调度器在旧内核上仍可能走有 bug 的 `scx_bpf_dsq_peek()`（stale task-pointer）或缺少任意上下文 reenqueue 入口。

## 技术方案
- Patch 1（Gavin Guo）：用内核版本判断把 `scx_bpf_dsq_peek()` 限定 kernel >= 7.1.0，旧内核改用 `bpf_iter_scx_dsq` 遍历。
- Patch 2（Changwoo Min）：新增 `scx_bpf_reenqueue_local_from_anywhere()` compat helper，并优先调用通用 `scx_bpf_dsq_reenq()`；不可用时返回 `-ENOTSUP`，给任意上下文调用者合法入口。
- 仅改 `tools/sched_ext/include/scx/compat.bpf.h`（+37/-11），无运行时内核改动。base-commit e5a0a3d6b05a。

## 版本演进与当前进展
v1（43819，2 patch）于 2026-08-17 22:31 发出。暂无 review 意见。

## Maintainer 意见与讨论焦点
v1 刚发出，Tejun 尚未回复（属工具头同步，预期直接收）。

## 合入评估
合入可能性高。纯 compat 头同步，无功能风险；与 010/011 的 kfunc 兼容修复方向一致。

## 效果评估
消除旧内核上 `scx_bpf_dsq_peek()` stale 指针风险；给任意上下文 reenqueue 提供受支持入口。无性能数据（工具侧）。

## 我可以参与的点
- 核对 7.1.0 门控下限与上游 scx 树一致，避免旧内核走 bug 路径。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
