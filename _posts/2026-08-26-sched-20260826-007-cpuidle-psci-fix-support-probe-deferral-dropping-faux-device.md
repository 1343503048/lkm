---
id: sched-20260826-007
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: unknown
lore_url: unknown
authors:
- Ulf Hansson
maintainers_involved:
- Abel Vesa
- Bartosz Golaszewski
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 修复 cpuidle-psci probe deferral 支持，丢弃 faux device
  review_outcome: Abel Vesa 给出 Reviewed-by
upstream_commit: null
fixes_commit: 39cdf87a97fd
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待维护者合入
contribution_opportunities: []
generated_at: '2026-08-27T01:22:00'
source_email_count: 3
related_articles: []
tags:
- idle
title: 'cpuidle: psci: Fix support for probe deferral by dropping the faux device'
layout: article
---

## TL;DR

Ulf Hansson (Qualcomm) 提交补丁修复 cpuidle-psci 驱动的 probe deferral 支持问题。当前实现使用 faux device，但在 probe deferral 场景下无法正确处理。方案改为直接丢弃 faux device 并在 DT 匹配时处理 deferral。Abel Vesa (Qualcomm) 已给出 Reviewed-by。与 PSCI MFD 驱动的讨论有关联。

## 背景与问题

cpuidle-psci 驱动在引入 faux device 后，probe deferral 场景出现问题。当 PSCI 驱动尚未就绪时，cpuidle-psci 的 probe 应该返回 `-EPROBE_DEFER`，但 faux device 的存在导致 deferral 机制无法正常工作。

该补丁与 `mfd: psci-mfd: Add PSCI MFD driver for cpuidle-psci-domain cell` 的讨论有关联——Bartosz Golaszewski 和 Ulf Hansson 正在讨论 PSCI 应该建模为 MFD 还是使用 auxiliary bus。

## 技术方案

补丁修改 cpuidle-psci 的 probe 逻辑，在检测到 probe deferral 条件时直接返回错误，不再依赖 faux device 的生命周期管理。标记了 `Fixes: 39cdf87a97fd` 和 `Cc: stable@vger.kernel.org`。

## 版本演进与当前进展

v1 已发出，Abel Vesa 给出了 `Reviewed-by`。

## Maintainer 意见与讨论焦点

Abel Vesa 快速 review 并给出 `LGTM` + `Reviewed-by`。Bartosz Golaszewski 在相关的 MFD 讨论中建议保留 MFD 方案而非 auxiliary bus。

## 合入评估

- **likelihood**: high（已有 Reviewed-by，标记了 Fixes 和 stable）
- **blocking_issues**: 无
- **next_action**: 等待维护者合入

## 效果评估

暂无性能数据，修复 probe deferral 的功能正确性问题。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
