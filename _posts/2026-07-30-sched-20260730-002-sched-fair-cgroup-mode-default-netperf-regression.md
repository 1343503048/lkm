---
subject: '[linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6%
  regression'
id: sched-20260730-002
date: 2026-07-30
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <202607151644.d59b94e9-lkp@intel.com>
lore_url: https://lore.kernel.org/lkml/202607151644.d59b94e9-lkp@intel.com
authors:
- Oliver Sang
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <202607151644.d59b94e9-lkp@intel.com>
  date: 2026-07-15
  summary: 0-Day robot reports 14.6% netperf TCP_MAERTS regression from sched/fair
    cgroup_mode default change (fb1050ac8e)
  review_outcome: PeterZ suspects ksoftirqd preemption behavior change, suggests mitigation
    via slice tuning
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Need to confirm root cause (ksoftirqd preemption change?)
  - Need mitigation evaluation
  next_action: Test PeterZ suggested mitigations (ksoftirqd slice tuning, renice)
contribution_opportunities:
- kind: testing
  description: Test PeterZ suggested mitigations (ksoftirqd slice tuning) and report
    results
generated_at: '2026-07-31T00:10:00'
source_email_count: 3
related_articles: []
tags:
- cfs
- cgroup
- load_balance
- regression
- perf
title: '[linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6%
  regression'
layout: article
---

## TL;DR

0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。

## 背景与问题

commit `fb1050ac8e` 将 `CONFIG_FAIR_GROUP_SCHED` 下 cgroup-weight 计算的默认模式从 `smp`（mode 1，flat per-taskgroup share）切换为 `concur`（mode 2，share scaled by min(runnable tasks, cpus)）。只改了两行代码：
- `kernel/sched/debug.c`: `cgroup_mode` 默认值从 1 改为 2
- `kernel/sched/fair.c`: `calc_group_shares` static_call 默认从 `calc_smp_shares` 改为 concur 模式

0-Day 测试结果显示 netperf TCP_MAERTS throughput 下降 14.6%。

## 技术方案

PeterZ 分析认为问题可能出在 ksoftirqd 的抢占行为变化：
- concur 模式下 group share 随并发任务数变化，可能改变了 ksoftirqd 对 netperf 任务的抢占频率
- 建议的缓解措施：
  1. 给 ksoftirqd 设置更短的 slice：`chrt -o -T $((base_slice_ns/10)) $pid`
  2. 给 netperf 任务更大的 slice，让 ksoftirq 更容易抢占它
  3. 通过 renice 调整优先级

PeterZ 同时指出 0-Day 的 AI 辅助分析报告"极其难读"，但核心分析方向基本正确。

## 版本演进与当前进展

- 2026-07-15: 0-Day 报告回归
- 2026-07-30: PeterZ 回复分析，指出可能的 root cause 和缓解方向
- Oliver Sang 确认正在试点 AI 辅助分析集成

## Maintainer 意见与讨论焦点

PeterZ 认为需要：
1. 确认具体是哪个 task 现在抢占变少（他猜测是 ksoftirqd）
2. 评估现有配置选项能否缓解（debugfs knob 回退旧行为、slice 调优）
3. 目前尚无定论，需要更多数据

## 合入评估

- **likelihood**: unknown
- 回归已确认，但 root cause 尚未完全定位
- 需要测试缓解措施的效果
- 可能需要 revert 或进一步 patch

## 效果评估

- netperf TCP_MAERTS throughput: **-14.6%**（0-Day 测试数据）
- PeterZ 指出需要确认具体抢占行为变化的 task

## 我可以参与的点

- **测试缓解措施**：可以在类似环境测试 PeterZ 建议的 ksoftirqd slice 调优方案，将结果回帖到邮件列表
- 如果有网络负载场景的 benchmark 数据，可以帮助评估 concur vs smp 模式的实际影响

## 参考链接

- lore thread: https://lore.kernel.org/lkml/202607151644.d59b94e9-lkp@intel.com
- tip-bot commit: 未获取到
- stable backport: 未获取到
