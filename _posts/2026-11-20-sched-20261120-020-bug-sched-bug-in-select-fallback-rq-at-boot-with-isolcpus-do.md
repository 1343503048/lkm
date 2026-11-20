---
id: sched-20261120-020
date: '2026-11-20'
subject: '[BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain
  on the boot CPU and CONFIG_CPUSETS=n'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com>
lore_url: https://lore.kernel.org/all/av8d79cn662slr_K@localhost.localdomain/
authors:
- Waiman Long
maintainers_involved:
- Frederic Weisbecker
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无补丁
  - 拒绝 boot CPU 隔离会牺牲现有可用配置需明确取舍
  next_action: Waiman/Mathieu 按拒绝+打印+继续启动发补丁
contribution_opportunities:
- kind: new_patch
  description: 实现拒绝 boot CPU 域隔离 + 打印信息 + 继续启动的修法
- kind: testing
  description: 含/不含 CONFIG_CPUSETS 的 VM 验证修复后启动且提示清晰
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261118-004
- sched-20261119-012
tags:
- cgroup
- topology
- crash
title: '[BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on
  the boot CPU and CONFIG_CPUSETS=n'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-004-bug-sched-bug-in-select-fallback-rq-at-boot-with-isolc.html">sched-20261118-004</a>：Waiman Long 报告 `isolcpus=domain` + boot CPU + `CONFIG_CPUSETS=n` 下 `select_fallback_rq()` 触发 BUG()；Frederic Weisbecker 与 Waiman 讨论 boot CPU 能否被隔离。
- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-012-bug-sched-bug-in-select-fallback-rq-at-boot-with-isolcpus-do.html">sched-20261119-012</a>：Mathieu Desnoyers 定性为回归（`bf5b0c27fad2`），支持 Waiman「拒绝把 boot CPU 域隔离」的修法，愿提供测试资源。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-020-bug-sched-bug-in-select-fallback-rq-at-boot-with-isolcpus-do.html">sched-20261120-020</a>（今天）：**Frederic 表态同意并堵上 ABI 顾虑**——「We should forbid that on all archs.」；同时指出该配置已受支持、不能直接移除（会破坏内核 ABI）。

## 背景与问题

（承接）`isolcpus=domain` 把指定 CPU 剥离成隔离域；boot CPU 被指定为该用法且 `CONFIG_CPUSETS=n` 时，启动早期 `select_fallback_rq()` 找不到合法 fallback CPU 触发 BUG()（日志无 isolcpus 线索）。回归责任在 `bf5b0c27fad2`（切到 `HK_TYPE_DOMAIN`）。

## 技术方案

今日推进：Frederic 明确同意 Waiman 的「拒绝 boot CPU 域隔离」方向，并补一句 ABI 现实——该配置当前已受支持，不能直接移除（破坏内核 ABI），因此修法应是「拒绝 + 打清晰信息 + 继续启动」，而非删除对 isolcpus=domain 的支持。这与 Mathieu 前日「拒绝时打印信息并继续启动」的要求一致。

## 版本演进与当前进展

*current_version: 无补丁（bug 报告阶段）*。今日无补丁；讨论在「回归责任 + 修法取舍 + ABI 约束」上进一步收敛。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker（NO_HZ/隔离方向维护者）**：同意「所有架构上都该拒绝 boot CPU 域隔离」，提示隔离支持不能移除（ABI）。
- **Waiman Long**（前情）：主张 cpuset 侧拒绝域隔离 boot CPU。
- **Mathieu Desnoyers**（前情）：定性回归、支持拒绝 + 打印 + 继续启动、愿测补丁。
- 无 NAK；方向一致，等补丁落定。

## 合入评估

*likelihood=unknown*。讨论方向（拒绝 + 打印 + 继续启动）已获涉及方一致，但尚无人发补丁。*blocking_issues*：无补丁；「拒绝」会牺牲一个现有可用配置（isolcpus=domain,0,1 + CONFIG_CPUSETS=y）需明确取舍。*next_action*：Waiman（或 Mathieu）按「拒绝 + 打印 + 继续启动」发补丁。

## 效果评估

无数据；问题表现为启动期 BUG()（崩溃类），修复后应可正常启动并给出可理解的提示。

## 我可以参与的点

- **new_patch**：实现「拒绝 boot CPU 域隔离 + 打印信息 + 继续启动」的修法（承接 Mathieu/Waiman 的讨论，补丁尚未有人发出）。
- **testing**：在含/不含 CONFIG_CPUSETS 的 VM 上验证修复后该命令行能启动且提示清晰。

## 参考链接

- lore thread（Frederic 回复）: https://lore.kernel.org/all/av8d79cn662slr_K@localhost.localdomain/
