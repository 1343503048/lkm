---
id: sched-20261105-020
date: 2026-11-05
subject: 'cpufreq: CPPC: Add ospm_nominal_freq attribute'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261030172745.2045743-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/20261030172745.2045743-1-sumitg@nvidia.com/
authors:
- Sumit Gupta
maintainers_involved: []
current_version: v8
patch_series:
- version: v8
  msgid: <20261030172745.2045743-1-sumitg@nvidia.com>
  date: 2026-10-30
  summary: 3 补丁：新增 ospm_nominal_freq 属性（patch 2/3）。
  review_outcome: Loehle 对 2/3 Reviewed-by。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等其余补丁评审与维护者收取
contribution_opportunities:
- kind: review
  description: 核对 ospm_nominal_freq 与 scaling_max_freq/boost 语义边界
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
title: 'cpufreq: CPPC: Add ospm_nominal_freq attribute'
layout: article
---

## TL;DR

Sumit Gupta 的 v8 系列为 CPPC cpufreq 新增 `ospm_nominal_freq` 属性（patch 2/3），把平台 OSPM nominal 频率作为 cpufreq 属性暴露。已迭代到第 8 版，今日 Christian Loehle 对 2/3 给出 `Reviewed-by`，进入收尾评审阶段。

## 背景与问题

CPPC 平台有 OSPM nominal frequency（nominal performance 对应的频率）这一平台语义值，调度器/上层需要读取时目前没有统一的 cpufreq 属性出口。该系列把它作为一个频率属性暴露出来，便于基于该值做决策。

## 技术方案

在 CPPC cpufreq 驱动中新增 `ospm_nominal_freq` 属性并接入 sysfs 暴露路径。本窗口仅获得 patch 2/3 的评审回复，具体实现细节未获取到更多邮件正文。

## 版本演进与当前进展

*current_version: v8（2026-10-30 发出，msgid 20261030172745.2045743-1）*。已迭代 8 版，今日 Loehle 对 patch 2/3 给 Reviewed-by；系列共 3 补丁（本窗口仅 2/3 的评审回复）。

## Maintainer 意见与讨论焦点

无 cpufreq 维护者（Rafael）直接回本线程；Christian Loehle（ARM）给 patch 2/3 `Reviewed-by`。无公开分歧记录。

## 合入评估

*likelihood=medium*。多轮迭代 + 获关键 reviewer 的 Reviewed-by，方向趋于收敛；但未见维护者态度与全系列最终状态。*blocking_issues*：暂无明确阻塞。*next_action*：等其余补丁与维护者收取确认。

## 效果评估

无性能数据；这是属性暴露接口，未涉及效果测量。

## 我可以参与的点

- review：核对 `ospm_nominal_freq` 与既有 `scaling_max_freq`/boost 语义的边界，避免新属性与现有接口重复或冲突。

## 参考链接

- lore thread（v8 cover）: https://lore.kernel.org/all/20261030172745.2045743-1-sumitg@nvidia.com/
- Loehle 的 Reviewed-by: https://lore.kernel.org/all/8be9a4f7-1b9a-4372-9751-6e5074305a5c@arm.com/
