---
id: sched-20260826-004
date: 2026-08-26
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: unknown
lore_url: unknown
authors:
- chenjinghuang
maintainers_involved:
- Aaron Lu
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 报告 userspace throttling + detach-into-dequeue 组合导致 KVM guest 启动挂起
  review_outcome: 讨论进行中，正在交换信息定位根因
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 根因未明
  next_action: 需要复现并定位具体 commit
contribution_opportunities:
- kind: testing
  description: 在 KVM + cfs_bandwidth 环境下尝试复现挂起问题
generated_at: '2026-08-27T01:16:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- cgroup
title: '[Question] Userspace throttling + "sched/fair: Combine detach into dequeue
  when migrating task" causes guest boot hang'
layout: article
---

## TL;DR

chenjinghuang (Huawei) 报告了一个问题：在启用 userspace throttling（`cpu.max` 配置）的环境下，`sched/fair: Combine detach into dequeue when migrating task` 补丁导致 guest 启动挂起。Aaron Lu (ByteDance) 参与了讨论。这是一个调试/问题报告，非补丁系列。

## 背景与问题

报告者在 KVM guest 中观察到启动挂起，条件组合了：
1. 启用了 userspace throttling（通过 cgroup `cpu.max` 配置 CPU 配额）
2. 应用了 `sched/fair: Combine detach into dequeue when migrating task` 补丁

该补丁将 task migration 时的 detach 操作合并到 dequeue 路径中，是一个已有的讨论中的优化。当两者结合时，guest 在启动阶段出现挂起。

## 技术方案

这不是一个补丁系列，而是一个问题报告。讨论中的关键信息：
- 问题仅在 userspace throttling + detach-into-dequeue 组合下出现
- 单独使用任一特性均不触发
- 需要进一步排查 throttling 逻辑与 detach/dequeue 合并后的交互

## 版本演进与当前进展

讨论进行中，Aaron Lu 和 chenjinghuang 正在交换信息以定位根因。

## Maintainer 意见与讨论焦点

Aaron Lu 参与了讨论，具体意见需查看邮件正文。问题可能涉及 cfs_bandwidth 与 task migration 路径的交互。

## 合入评估

- **likelihood**: unknown（问题报告阶段，需要先定位根因）
- **blocking_issues**: 根因未明
- **next_action**: 需要复现并定位具体是哪部分改动导致挂起

## 效果评估

暂无效果数据，仅有挂起现象报告。

## 我可以参与的点

- 如果有 KVM + cfs_bandwidth 的测试环境，可以尝试复现该问题
- 可以用 `git bisect` 确认具体是哪个 commit 引入了问题

## 参考链接

- lore thread: 未获取到
