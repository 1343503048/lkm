---
id: sched-20260821-007
date: 2026-08-21
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: 未获取到
lore_url: 未获取到
authors:
- unknown
maintainers_involved:
- Kumar Kartikeya Dwivedi
current_version: v1
patch_series:
- version: v1
  msgid: 未获取到
  date: 2026-08-21
  summary: 标记 sched_ext ops 容器指针字段为 trusted
  review_outcome: 已合入 bpf-next
upstream_commit: aed1bf1a352a
fixes_commit: null
merged_branch: bpf/bpf-next
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入
contribution_opportunities: []
generated_at: '2026-08-21T10:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- bpf
title: 'bpf: sched_ext: Mark ops argument container pointer fields as trusted'
layout: article
---

## TL;DR

sched_ext 的 ops 参数容器指针字段被标记为 trusted，允许 BPF 调度器安全地解引用这些指针。补丁已被 bpf/bpf-next.git 合入。

## 背景与问题

BPF 调度器通过 ops 回调接收参数，其中部分参数是容器指针（如 task group 结构体）。BPF verifier 需要知道这些指针是 trusted 的，才能允许调度器代码安全地解引用它们。之前这些字段未被标记为 trusted，限制了 BPF 调度器的能力。

## 技术方案

将 sched_ext ops 参数中容器指针字段标记为 `PTR_TRUSTED`，让 BPF verifier 允许直接解引用。由 Kumar Kartikeya Dwivedi 审核。

## 版本演进与当前进展

v1 已合入 bpf/bpf-next.git (master)。

## Maintainer 意见与讨论焦点

补丁已获合入，无争议。

## 合入评估

- **likelihood**: merged
- **blocking_issues**: 无
- 已合入 `bpf/bpf-next.git`，commit: `aed1bf1a352a`

## 效果评估

让 BPF 调度器能更安全高效地访问容器信息，无直接性能数据。

## 我可以参与的点

当前阶段暂无明显参与空间，补丁已合入。

## 参考链接

- lore thread: 未获取到
- bpf-next commit: https://git.kernel.org/bpf/bpf-next/c/aed1bf1a352a
- stable backport: 未获取到
