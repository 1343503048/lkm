---
id: sched-20261021-021
date: 2026-10-21
subject: '[GIT PULL] Scheduler updates for v7.4'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <179253782199.260052.5366596841657852673.pr-tracker-bot@kernel.org>
lore_url: https://lore.kernel.org/all/179253782199.260052.5366596841657852673.pr-tracker-bot@kernel.org/
authors:
- Ingo Molnar
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: cb95904b470d2d347012d5e360303cf478ca5362
fixes_commit: null
merged_branch: torvalds/linux.git
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 mainline，无需进一步动作
contribution_opportunities: []
generated_at: '2026-10-22T01:30:00'
source_email_count: 1
related_articles:
- sched-20261018-011
tags: []
title: '[GIT PULL] Scheduler updates for v7.4'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-011-git-pull-scheduler-updates-for-v7-4.html">sched-20261018-011</a>：Ingo Molnar 向 Linus 发 v7.4 合入窗口的主调度器 pull request（tip 树 `sched-core-2026-10-18`），涵盖 fair/DL/RT/EAS/负载均衡/cache-aware/NUMA/proxy execution/基础设施等方向；当日未见 pr-tracker-bot 合并确认。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-021-git-pull-scheduler-updates-for-v7-4.html">sched-20261021-021</a>（今天）：pr-tracker-bot 确认该 PR **已合入 torvalds/linux.git**，合并 commit 为 `cb95904b470d2d347012d5e360303cf478ca5362`。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-011-git-pull-scheduler-updates-for-v7-4.html">sched-20261018-011</a>）v7.4 合入窗口开启，Ingo 汇总 `sched/core` 分支提请 Linus 收取。今日为合并完成通知，标志 v7.4 的主调度器改动正式进入 mainline。

## 技术方案
（无新代码，为合并状态变更）PR 内容与 20261018-011 一致：fair（RUN_TO_PARITY 清理、augmented callback、hrtick 重播、短 slice 时延）、DL/RT、EAS steal_governor、负载均衡、cache-aware、NUMA、proxy execution（sleeping owner + sched_ext 兼容铺垫）等。

## 版本演进与当前进展
*status: merged_tip*。合并 commit：`cb95904b470d2d347012d5e360303cf478ca5362`（torvalds/linux.git）。

## Maintainer 意见与讨论焦点
pr-tracker-bot 自动确认合并，无人工意见。

## 合入评估
*likelihood=merged*。已合入 mainline。

## 效果评估
无（合并事件）。

## 我可以参与的点
无。

## 参考链接
- pr-tracker-bot 合并确认：https://lore.kernel.org/all/179253782199.260052.5366596841657852673.pr-tracker-bot@kernel.org/
- 合并 commit：https://git.kernel.org/torvalds/c/cb95904b470d2d347012d5e360303cf478ca5362
