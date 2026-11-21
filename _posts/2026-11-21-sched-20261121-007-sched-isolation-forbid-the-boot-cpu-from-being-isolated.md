---
id: sched-20261121-007
date: '2026-11-21'
subject: 'sched/isolation: Forbid the boot CPU from being isolated'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261121031329.240177-3-longman@redhat.com>
lore_url: https://lore.kernel.org/all/20261121031329.240177-3-longman@redhat.com/
authors:
- Waiman Long
maintainers_involved:
- Frederic Weisbecker
current_version: v1
patch_series:
- version: v1
  msgid: <20261121031329.240177-3-longman@redhat.com>
  date: '2026-11-21'
  summary: PATCH-next 2/3：从 isolcpus 范围清除 boot CPU 并打印警告，更新文档
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 用户可见行为变更待确认
  - 同系列 1/3 的 lkp 构建警告
  next_action: 清 1/3 构建警告后连同 2/3、3/3 一起评审合入
contribution_opportunities:
- kind: testing
  description: 含/不含 CONFIG_CPUSETS、PPC 与非 PPC 验证 isolcpus=domain,0 启动不 panic、suspend
    无回归
- kind: review
  description: 核对 boot CPU 清除时机与 1/3 mask 一致化的配合正确性
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles:
- sched-20261120-020
tags:
- topology
- nohz
title: 'sched/isolation: Forbid the boot CPU from being isolated'
layout: article
---

## TL;DR

Waiman Long 发 PATCH-next 2/3，是 [BUG] select_fallback_rq 启动崩溃（isolcpus=domain 隔离 boot CPU）的正式修复：启动参数里若把 boot CPU 放进 isolcpus，就把它从隔离范围清除并打印警告，同时更新 kernel-parameters.txt。该改动属用户可见行为变更，需维护者确认取舍。

## 背景与问题

`CONFIG_CPUSETS=n` 的内核以 `isolcpus=domain,0` 启动时，boot 时 CPU 0 是唯一 online CPU，unbound kworker 无法在域隔离的 CPU 上运行，`select_fallback_rq()` 触发 BUG() 致 panic（承接 <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-020-bug-sched-bug-in-select-fallback-rq-at-boot-with-isolcpus-do.html">sched-20261120-020</a> 的回归定性，`bf5b0c27fad2`）。Sashiko 还报告域隔离 boot CPU 会破坏系统 suspend 并触发 BUG_ON()。多数子系统都不考虑 boot CPU 可被域隔离的情况。当前 housekeeping 规则要求 isolcpus 与 nohz_full 若同时给出须一致；既然 boot CPU 大概率被排除在 nohz_full 之外，也应禁止它在 isolcpus 中出现。

## 技术方案

把 boot CPU 从 isolcpus 范围中清除（当命令行指定它时），并打印一条警告；同步更新 kernel-parameters.txt 说明 boot CPU 不能被隔离。作者明言这是用户可见的行为变更。这是对 [BUG] 线程「拒绝 boot CPU 域隔离 + 打印信息 + 继续启动」方向（Frederic/Mathieu 前日达成一致）的落地，配合 1/3 的 mask 一致化、3/3（本日缓存未见）完成整套修复。

## 版本演进与当前进展

*current_version: v1（2026-11-21，`<20261121031329.240177-3-longman@redhat.com>`，PATCH-next 2/3）*。首版，当日无 review；同系列 1/3 已接 lkp 构建警告。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker / Mathieu Desnoyers**（前情，承接 <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-020-bug-sched-bug-in-select-fallback-rq-at-boot-with-isolcpus-do.html">sched-20261120-020</a>）：一致同意「所有架构上拒绝 boot CPU 域隔离 + 打印 + 继续启动」，并提示不能直接移除对 isolcpus=domain 的支持（破坏 ABI）。本日缓存未见其对 2/3 的新回复。
- 无 NAK；方向已获涉及方一致，下一步进入补丁层评审。

## 合入评估

*likelihood=medium*。方向获维护者一致同意、直接关闭一个启动崩溃，但属用户可见行为变更（牺牲 isolcpus=domain,0 配置）需明确取舍，且同系列 1/3 尚有构建警告待清。*blocking_issues*：行为变更需维护者确认；同系列 1/3 的 lkp 构建警告。*next_action*：清掉 1/3 的构建警告，连同 2/3、3/3 一起评审后合入。

## 效果评估

无性能数据；修复收益为使 `isolcpus=domain,0` + `CONFIG_CPUSETS=n` 的内核不再启动崩溃（改为警告 + 继续启动）。

## 我可以参与的点

- **testing**：在含/不含 CONFIG_CPUSETS、PPC 与非 PPC 上验证 `isolcpus=domain,0` 启动不再 panic、警告清晰、suspend 无回归。
- **review**：核对「清除 boot CPU」的处理时机（早于 housekeeping/nohz 初始化）是否与 1/3 的 mask 一致化正确配合。

## 参考链接

- lore thread（2/3）: https://lore.kernel.org/all/20261121031329.240177-3-longman@redhat.com/
- 前情 [BUG] 报告: https://lore.kernel.org/lkml/20261117144817.265109-1-mathieu.desnoyers@efficios.com/
