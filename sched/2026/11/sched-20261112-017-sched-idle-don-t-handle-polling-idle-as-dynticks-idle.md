# sched/idle: Don't handle polling idle as dynticks idle

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261111-004：Marco Crivellari（SUSE）发 v2 四补丁（当日仅收到 patch 2/4），修 `idle=poll` 与 nohz_full 的交互缺陷——polling 期间 `TS_FLAG_INIDLE` 被误置导致 tick 在 nohz_full CPU 上被重启、唤醒后持续打断用户态。方案由 Frederic Weisbecker 建议。
- sched-20261112-017（今天）：**Frederic Weisbecker 给 Reviewed-by**；K Prateek Nayak 提一处 nit（用 `guard(irqsave)()` 简化）；**Peter Zijlstra 表示「只收到四封里的一封，所以一直没看」**，Marco 道歉并承诺下一版把整个系列 CC 给 Peter、同时采纳 guard() 简化。系列即将补齐评审闭环。

## 背景与问题

（承接 sched-20261111-004）`TS_FLAG_INIDLE` 告诉 nohz 框架「当前 CPU 的 tick 由 idle 循环还是 IRQ 出口管理」。`idle=poll` 时该标志在 polling 期间被置起，但 `cpu_idle_poll()` 不在每次中断后重新评估 nohz 状态，导致 nohz_full CPU 上被停止的 tick 在 polling 前被重启、唤醒后持续打断用户态。今日进入评审收口阶段。

## 技术方案

（承接 patch 2/4）进入 dynticks idle 限定在 cpuidle 路径 `cpuidle_idle_call()`，进入 polling 前 `tick_nohz_idle_exit()`，让 polling 期间 tick 按「运行中任务」在 IRQ 出口管理。今日 K Prateek 建议把 patch 2 里的手动 flags/out 标签改成 `guard(irqsave)()` 并可直接 return，Marco 接受。

## 版本演进与当前进展

*current_version: v2（2026-11-11，cover `<20261111114406.346953-1-marco.crivellari@suse.com>`）*。今日无新版本；获得 nohz 维护者 Reviewed-by，Peter 补齐收件（此前漏收其余三封），作者承诺下一版 CC 全系列并采纳 guard 简化。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker（nohz 维护者）**：Reviewed-by（他同时也是方案建议人，方向已双重背书）。
- **Peter Zijlstra（sched 维护者）**：「只收到四封里的一封，所以一直没看」——尚未实质评审，但已要求被 CC 到全系列。
- **K Prateek Nayak**：nit——`guard(irqsave)()` 可直接 return，无需 flags/out 标签。
- 无 NAK；分歧无，仅为「补全收件 + 代码简化」的收口项。

## 合入评估

*likelihood=medium*。方案获 Frederic Reviewed-by，方向明确；但 Peter 尚未实质评审（此前漏收三封），且改动同时涉及 sched 与 time 两个子系统。*blocking_issues*：无硬阻塞；待 Peter 对全系列的评审。*next_action*：作者发下一版（CC Peter 全系列、采纳 guard 简化），等 Peter 评审后收取。

## 效果评估

暂无量化数据。收益为行为正确性：消除 nohz_full + idle=poll 下「唤醒后 tick 持续打断用户态」的延迟问题。

## 我可以参与的点

- **testing**：在 nohz_full 系统上用 `idle=poll` 复现并验证——观测唤醒后 tick 是否保持停止、`/proc/interrupts` 的 local timer 中断计数是否回落。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/
- Frederic 的 Reviewed-by: https://lore.kernel.org/all/avSeXluNMl_XGPEw@localhost.localdomain/
- Peter 的「只收到一封」: https://lore.kernel.org/all/20261111165838.GR1779021@noisy.programming.kicks-ass.net/

---
id: sched-20261112-017
date: '2026-11-12'
subject: "sched/idle: Don't handle polling idle as dynticks idle"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261111114406.346953-1-marco.crivellari@suse.com>"
lore_url: "https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/"
authors: [Marco Crivellari]
maintainers_involved: [Frederic Weisbecker, Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261111114406.346953-1-marco.crivellari@suse.com>"
    date: '2026-11-11'
    summary: "进入 dynticks idle 限定在 cpuidle 路径，polling 前退出"
    review_outcome: "Frederic Reviewed-by；K Prateek guard nit；Peter 要求 CC 全系列"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "作者发下一版（CC Peter 全系列 + guard 简化）后等 Peter 评审"
contribution_opportunities:
  - kind: testing
    description: "nohz_full + idle=poll 下验证唤醒后 tick 保持停止"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 5
related_articles: [sched-20261111-004]
tags: [nohz, idle]
---