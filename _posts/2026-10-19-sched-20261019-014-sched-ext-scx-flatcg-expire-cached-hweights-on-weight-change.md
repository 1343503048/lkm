---
id: sched-20261019-014
subject: 'sched_ext/scx_flatcg: expire cached hweights on weight changes'
date: 2026-10-19
subsystem: sched
type: fix
status: merged_stable
severity: medium
thread_root_msgid: <20261019135441.1420968-24-sashal@kernel.org>
lore_url: https://lore.kernel.org/all/20261019135441.1420968-24-sashal@kernel.org/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
- Sasha Levin
current_version: v1
patch_series:
- version: v1
  msgid: <20261019135441.1420968-24-sashal@kernel.org>
  date: 2026-10-19
  summary: AUTOSEL 回补 94c20e1fb334：weight 变化时 bump hweight_gen 使缓存失效
  review_outcome: 已上游合入，走 stable 自动回补
upstream_commit: 94c20e1fb334c2082b443c4470a86ad982f67282
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 等待 AUTOSEL 回补 6.18–6.12 落地
contribution_opportunities: []
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext/scx_flatcg: expire cached hweights on weight changes'
layout: article
---

## TL;DR

Sasha Levin 的 AUTOSEL（stable 自动选收）把上游 commit `94c20e1fb334`（`sched_ext/scx_flatcg` 的 hweight 缓存失效修复）提为 6.18–6.12 各 stable 分支的候选回补。修复内容：`fcg_cgroup_set_weight()` 更新 `cgc->weight` 却未 bump `hweight_gen`，导致忙碌 cgroup 的 `cpu.weight` 修改不生效。

## 背景与问题

`fcg_cgroup_set_weight()` 更新 `cgc->weight` 与父级 `child_weight_sum`，但不 bump `hweight_gen`，于是 `cgrp_refresh_hweight()` 缓存的 hweight 一直陈旧，直到有任务 0→n runnable 迁移才 bump generation。对任务从不经历 0→n 迁移的持续忙碌 cgroup，`cpu.weight` 修改根本不会传播到调度。上游已在 mainline 修复（`94c20e1fb334`），本次为 AUTOSEL 回补 6.18–6.12。

## 技术方案

修复（已在上游）：weight 变化时 bump `hweight_gen`，使下次 refresh 用新权重重算。作者（Tao Cui）在 flatcg VM 验证：忙碌 cgroup 上 `cpu.weight` 100→800 实改，改前 HWT 更新保持 0、分布不变；改后 `hweight_gen` 递增、refresh 重算。已带 Tejun Heo、Sasha Levin 的 Signed-off-by。

## 版本演进与当前进展

*current_version: 已合入上游*。AUTOSEL 邮件（`<20261019135441.1420968-24-sashal@kernel.org>`）为该 commit 的 stable 回补候选通知，覆盖 6.18、6.17、6.16、6.15、6.14、6.13、6.12。

## Maintainer 意见与讨论焦点

AUTOSEL 为 Sasha Levin 的自动选收（带作者 Tao Cui 与维护者 Tejun Heo 的 Signed-off-by），如无异议将自动回补；无其它讨论。

## 合入评估

*likelihood=merged*（上游 commit `94c20e1fb334` 已合入 mainline，正走 stable 回补流程）。*blocking_issues*：无。*next_action*：等待 AUTOSEL 回补落地（如相关方无反对）。

## 效果评估

作者验证：忙碌 cgroup 上实改 `cpu.weight` 100→800，改前 HWT 更新保持 0、分布不变，改后重算生效。属正确性修复，无性能数字。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察（AUTOSEL 回补为自动流程，上游已修复）。

## 参考链接

- AUTOSEL 邮件：https://lore.kernel.org/all/20261019135441.1420968-24-sashal@kernel.org/
