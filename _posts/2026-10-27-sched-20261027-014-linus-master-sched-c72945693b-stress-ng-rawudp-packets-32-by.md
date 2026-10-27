---
id: sched-20261027-014
date: 2026-10-27
subject: '[linus:master] [sched]  c72945693b: stress-ng.rawudp.packets_32_bytes_received_per_sec
  34.2% improvement'
subsystem: sched
type: discussion
status: merged_tip
severity: none
thread_root_msgid: <202610271134.d6bf1e10-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202610271134.d6bf1e10-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: c72945693b90423f1b46ac2dbc8749c2b7804fc8
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 无须动作，已合入修复的收益确认
contribution_opportunities: []
generated_at: '2026-10-28T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
title: '[linus:master] [sched]  c72945693b: stress-ng.rawudp.packets_32_bytes_received_per_sec
  34.2% improvement'
layout: article
---

## TL;DR
kernel test robot 报告：mainline commit `c72945693b`（"sched: Restart fair hrtick after same-task repicks"，即 Shubhang Kaushik 的 same-task repick 后重启 fair hrtick 修复，9 月已合入）在 stress-ng rawudp 小包场景带来 **34.2% 提升**，是一项已合入修复的正面性能确认。

## 背景与问题
该 lkp 报告是对已合入主线（`torvalds/linux master`）的 commit `c72945693b90423f1b46ac2dbc8749c2b7804fc8` 的一次性能回归扫描发现——并非新问题，而是确认该修复带来了显著收益。被测 commit 修的是 fair hrtick 在「同任务重新选中（same-task repick）」后未被重新武装、导致 fair 任务抢占时点静默丢失的正确性缺口。

## 技术方案
无补丁。lkp 自动 benchmark 通知，附带可复现配置（下载链接）与逐项对比数据。

## 版本演进与当前进展
*current_version: 无*（基准测试报告）。commit 于 09-25 已合入 tip/sched/core 并进 linus master。

## Maintainer 意见与讨论焦点
无。属 lkp 日报类通知。

## 合入评估
*likelihood=merged*。所涉 commit 已在 linus master。

## 效果评估
stress-ng.rawudp `packets_32_bytes_received_per_sec` **34.2% 提升**；测试机 192 线程 2 插槽 Intel Xeon 6740E（Sierra Forest）、256G 内存，`gcc-14`，`cpufreq_governor=performance`，`testtime=60s`、`nr_threads=100%`、`test=rawudp`。属真实 benchmark 数据。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入修复的收益确认）。可关注同测试在其它负载/平台上是否也有类似提升。

## 参考链接
- lkp 报告邮件: https://lore.kernel.org/all/202610271134.d6bf1e10-lkp@intel.com/
- 复现材料: https://download.01.org/0day-ci/archive/20261027/202610271134.d6bf1e10-lkp@intel.com
