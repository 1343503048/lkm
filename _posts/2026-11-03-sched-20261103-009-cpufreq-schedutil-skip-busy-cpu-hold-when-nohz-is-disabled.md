---
id: sched-20261103-009
date: 2026-11-03
subject: 'cpufreq: schedutil: Skip busy-CPU hold when NOHZ is disabled'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261103061557.1235129-1-thnkslprpt@gmail.com>
lore_url: https://lore.kernel.org/all/20261103061557.1235129-1-thnkslprpt@gmail.com/
authors:
- Avi Weiss
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261103061557.1235129-1-thnkslprpt@gmail.com>
  date: 2026-11-03
  summary: sugov_hold_freq() 在 NOHZ 停用时跳过 busy-CPU hold。
  review_outcome: 评审一致建议改用 tick_nohz_is_active() 并 Cc stable。
upstream_commit: null
fixes_commit: b7eaf1aab9f8
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需改用 tick_nohz_is_active() 并补 Cc
  next_action: 作者改版：tick_nohz_enabled → tick_nohz_is_active，Cc stable 与调度维护者。
contribution_opportunities:
- kind: testing
  description: nohz=off 与 NOHZ 未激活两种配置下验证降频恢复。
- kind: review
  description: 确认 tick_nohz_is_active() 覆盖 idle=poll 等边界。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- cpufreq
- nohz
title: 'cpufreq: schedutil: Skip busy-CPU hold when NOHZ is disabled'
layout: article
---

## TL;DR

Avi Weiss 修 schedutil 的一个频率卡高问题：`nohz=off` 时 `tick_nohz_idle_stop_tick()` 会不递增 `idle_calls` 就返回，`sugov_hold_freq()` 把不变的计数器当成「CPU 持续忙」、阻止 CPU 空闲后降频。修复在 NOHZ 停用时跳过 busy-CPU hold 启发式。评审建议改用 `tick_nohz_is_active()` 并 Cc stable。

## 背景与问题

`sugov_hold_freq()` 依据 `sg_cpu->idle_calls` 是否变化判断「CPU 最近是否 idle」，从而决定是否暂缓降频（`b7eaf1aab9f8` 引入，避免过早降频）。但 `nohz=off` 时 `tick_nohz_idle_stop_tick()` 可能不递增 `idle_calls` 就返回，`sugov_hold_freq()` 于是把「不变」误读为「持续忙」，即便 CPU 已 idle 仍阻止降频。位于 `kernel/sched/cpufreq_schedutil.c`。

## 技术方案

在 `sugov_hold_freq()` 开头加 `if (!tick_nohz_enabled) return false;`（+3 行），NOHZ 停用时直接不启用 busy-CPU hold。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103061557.1235129-1-thnkslprpt@gmail.com）*。当日 Zhan Xusheng、Zhongqiu Han 回帖。

## Maintainer 意见与讨论焦点

Zhan Xusheng 指出 `tick_nohz_enabled` 不够——NOHZ 启用但从未激活（`tick_check_oneshot_change()` 未找到 oneshot 时钟事件/高精度 clocksource）时 `idle_calls` 同样不动，建议改用 `tick_nohz_is_active()`。Zhongqiu Han 同意，并要求 Cc stable 与用 `scripts/get_maintainer.pl` 补上调度维护者；同时提醒：nohz_full 的 timekeeping CPU 与 `idle=poll` 场景仍存在「用 tick-stop 计数器当 idle 信号」的更深问题，宜另作处理。

## 合入评估

*likelihood=high*。方向获评审一致认可，只需把 `!tick_nohz_enabled` 换成 `tick_nohz_is_active()` 并补 Cc，属小改可收。

## 效果评估

作者说明是行为修复（NOHZ 停用时频率无法降到期望值），未附量化数据；评审未质疑其机理。

## 我可以参与的点

- testing：在 `nohz=off` 与「NOHZ 启用但未激活」两种配置下验证降频恢复。
- review：确认 `tick_nohz_is_active()` 是否覆盖 `idle=poll`/nohz_full timekeeping CPU 之外的边界。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103061557.1235129-1-thnkslprpt@gmail.com/
