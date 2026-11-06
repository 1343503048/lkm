---
id: sched-20261106-019
date: 2026-11-06
subject: '[linus:master] [sched/fair]  fb1050ac8e: stress-ng.sleep.ops_per_sec 29.9%
  regression'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <202611060925.fb5500b1-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202611060925.fb5500b1-lkp@intel.com/
authors: []
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: fb1050ac8e40aaa014291b5b53612d27890c2b09
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - cgroup_mode 默认值变更的根因与影响面未在 master 上重新评估
  - 是否回退默认值需维护者决策
  next_action: sched 维护者确认回归根因并决定回退默认值或修复 concur 实现
contribution_opportunities:
- kind: discussion
  description: 定位 concur 模式下回退的具体任务/行为（如 ksoftirqd 抢占假设）
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20260730-002
tags:
- cfs
- cgroup
- regression
title: '[linus:master] [sched/fair]  fb1050ac8e: stress-ng.sleep.ops_per_sec 29.9%
  regression'
layout: article
---

## TL;DR

kernel test robot（0-Day）在 **linus:master** 上复现 commit `fb1050ac8e`（"sched/fair: Change the default cgroup_mode to concur"）的显著回归：stress-ng.sleep.ops_per_sec 下降 **29.9%**（Sapphire Rapids 224 线程），netperf TCP_STREAM 吞吐下降 **15.9%**（Sierra Forest 192 线程），伴随 involuntary/voluntary context switch 大幅下降（-29.1%/-30.6%）。这是继 7 月 linux-next 上 netperf -14.6% 报告之后，该 commit 进入 linus:master 后的新一轮、更严重的回归信号——cgroup_mode 从 smp 改为 concur 的默认值变更再次成为性能回退嫌疑对象。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html">sched-20260730-002</a>）`fb1050ac8e` 把 `CONFIG_FAIR_GROUP_SCHED` 下 cgroup-weight 计算的默认模式从 `smp`（flat per-taskgroup share）切换为 `concur`（share 按 min(runnable tasks, cpus) 缩放），父提交为 `507f910a4e`（"Add cgroup_mode: tasks"）。7 月 0-Day 已在 linux-next 上报告 netperf TCP_MAERTS -14.6%，Peter Zijlstra 当时怀疑是 ksoftirqd 抢占行为变化。现在该 commit 已进 linus:master，0-Day 在 master 上复现出更大的回归（stress-ng -29.9%、netperf -15.9%）。

## 技术方案

本邮件为回归报告，非修复。0-Day 提供了完整复现材料（config `x86_64-rhel-9.4`、gcc-14、Sapphire Rapids 224 线程 / Sierra Forest 192 线程、cpufreq_governor=performance），并在报告头部提示修复者补上 `Reported-by: kernel test robot` 与 `Closes:` 标签。测试对比点：`507f910a4e`（cgroup_mode: tasks，基线）vs `fb1050ac8e`（默认改 concur）。

## 版本演进与当前进展

*current_version: 无（回归报告）*。7 月 linux-next 报告（netperf -14.6%）后，该 commit 仍进入了 linus:master；今日 master 上报告升级为 stress-ng -29.9% + netperf -15.9%。作者（commit 提交者）尚未回应。

## Maintainer 意见与讨论焦点

今日报告无维护者回复。此前（7 月）Peter Zijlstra 曾分析为 ksoftirqd 抢占行为变化、建议通过 slice 调优或回退 debugfs knob 缓解，但当时信息不足以定根因。回归在 master 上扩大，需要维护者正视是否回退默认值。

## 合入评估

*likelihood=unknown*（针对「commit 是否会被回退/修复」）。回归数据显著且来自 master，但根因未定论、维护者未表态。*blocking_issues*：① cgroup_mode 默认值变更的根因与影响面尚未在 master 上重新评估；② 是否回退默认值需维护者决策。*next_action*：sched 维护者确认回归根因，决定回退默认值或修复 concur 模式的实现。

## 效果评估

0-Day 数据（对比 507f910a4e → fb1050ac8e）：

- stress-ng.sleep：ops_per_sec -29.9%（96108453→67358809），ops -29.9%；involuntary_context_switches -29.1%、voluntary_context_switches -30.6%。
- netperf TCP_STREAM：Throughput_Mbps -15.9%（3415→2871），involuntary_context_switches -63.2%。

两处机器分别为 Sapphire Rapids（224 线程）与 Sierra Forest（192 线程），均为性能型多核平台。

## 我可以参与的点

- **discussion**：帮忙定位 `concur` 模式下具体哪个任务/行为导致的回退（例如复现 ksoftirqd 抢占假设、或对比 cgroup_mode=smp/concur 的调度轨迹）——7 月根因未定，master 上放大后更需要这类分析。

## 参考链接

- lore thread: https://lore.kernel.org/all/202611060925.fb5500b1-lkp@intel.com/
- 复现材料: https://download.01.org/0day-ci/archive/20261106/202611060925.fb5500b1-lkp@intel.com
- 历史 linux-next 报告文章: <a class="article-ref" href="/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html">sched-20260730-002</a>（见 sched/2026/07/ 归档）
