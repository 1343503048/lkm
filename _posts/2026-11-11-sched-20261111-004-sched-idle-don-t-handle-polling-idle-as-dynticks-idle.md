---
id: sched-20261111-004
date: '2026-11-11'
subject: 'sched/idle: Don''t handle polling idle as dynticks idle'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261111114406.346953-1-marco.crivellari@suse.com>
lore_url: https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/
authors:
- Marco Crivellari
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261111114406.346953-1-marco.crivellari@suse.com>
  date: '2026-11-11'
  summary: 进入 dynticks idle 限定在 cpuidle 路径，polling 前退出，tick 由 IRQ 出口管理
  review_outcome: 暂无回复（Frederic Weisbecker 为方案建议人）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待 sched 与 time 双方维护者评审
contribution_opportunities:
- kind: testing
  description: 在 nohz_full 上用 idle=poll 复现并验证唤醒后 tick 是否保持停止
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- nohz
- idle
title: 'sched/idle: Don''t handle polling idle as dynticks idle'
layout: article
---

## TL;DR

Marco Crivellari（SUSE）发 v2 系列（4 补丁，当日仅收到 patch 2/4），修 `idle=poll` 与 nohz_full 的交互缺陷：`TS_FLAG_INIDLE` 让 nohz 误以为 idle=poll 时的 tick 仍由 idle 循环管理，但 `cpu_idle_poll()` 在中断后不会重跑 idle 循环，导致 nohz_full CPU 上被停止的 tick 在 polling 前被重启、唤醒后持续打断用户态。修复把「进入 dynticks idle」限定在 cpuidle 路径（`cpuidle_idle_call()`），进入 polling 前退出，让 polling 期间的 tick 按「运行中任务」的方式在 IRQ 出口管理。刚发出，暂无回复。

## 背景与问题

`TS_FLAG_INIDLE` 告诉 nohz 框架「当前 CPU 的 tick 由 idle 循环管理还是由 IRQ 出口管理」。`idle=poll` 时该标志在 polling 期间被置起，但 `cpu_idle_poll()` 并不像正常 idle 循环那样在每次中断后重新评估 nohz 状态：nohz_full 的 kick 或「被停止 tick 的到期」都要等到有人置 `TIF_NEED_RESCHED` 才会被重新评估。结果是 tick 在进入 polling 前就被重启，且在 nohz_full CPU 上唤醒后继续运行、周期性打断用户态（对 RT/延迟敏感负载有害）。

## 技术方案

patch 2/4（`sched/idle: Don't handle polling idle as dynticks idle`）：

- 只在 cpuidle 路径 `cpuidle_idle_call()` 里调 `tick_nohz_idle_enter()`（原来在 `do_idle()` 的 `__current_set_polling()` 之后统一进入），并把它从 `do_idle()` 移除。
- 在 `do_idle()` 的 polling 分支里，`tick_nohz_idle_restart_tick()` 换成 `tick_nohz_idle_exit()`——即进入 polling 前退出 dynticks idle，让 polling 期间 tick 按「运行中任务」的方式在 IRQ 出口管理：nohz_full CPU 上尽可能保持停止、唤醒时无事可做，任务不再为「唤醒后再停一次 tick」付代价；其它 CPU 上退出 dynticks idle 会照旧重启 tick。
- `tick_nohz_idle_enter()` 改为在每次 idle 循环迭代、关中断下调用（只有第一次真正进入 dynticks idle）；`tick_nohz_idle_exit()` 允许在 dynticks idle 之外、关中断下调用。

改动 `kernel/sched/idle.c` +13/-2、`kernel/time/tick-sched.c` +27/-13。方案由 Frederic Weisbecker 建议（`Suggested-by`），并 Cc 了 Peter Zijlstra、Thomas Gleixner、Anna-Maria Behnsen 等 sched/time 维护者。

## 版本演进与当前进展

*current_version: v2（2026-11-11，cover `<20261111114406.346953-1-marco.crivellari@suse.com>`）*。当日仅收到 patch 2/4，cover 与其余三封不在缓存；v1 亦不在近期缓存，无法核对 v1→v2 的具体改动。

## Maintainer 意见与讨论焦点

当日无维护者回复。方案来自 nohz 维护者 Frederic Weisbecker 的建议，方向已获其背书（作为 Suggested-by 署名），尚未见 Peter/tglx 的表态。

## 合入评估

*likelihood=unknown*。v2 刚发出、当日无回复；但方向有 Frederic 建议背书，且同时改动 sched 与 time 两个子系统，需双方维护者都看过。*blocking_issues*：无。*next_action*：等待 Peter Zijlstra（sched）与 Thomas Gleixner/Anna-Maria（time）评审。

## 效果评估

暂无量化数据。作者描述的是行为正确性收益：消除 nohz_full + idle=poll 下「唤醒后 tick 持续打断用户态」的延迟问题。

## 我可以参与的点

- **testing**：在 nohz_full 系统上用 `idle=poll` 复现并验证——观测唤醒后 tick 是否保持停止、`/proc/interrupts` 的 local timer 中断计数是否回落。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/
- patch 2/4: https://lore.kernel.org/all/20261111114406.346953-3-marco.crivellari@suse.com/
