# sched/idle: Don't handle polling idle as dynticks idle

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261111-004：Marco Crivellari（SUSE）发 v2 四补丁（当日仅收到 patch 2/4），修 `idle=poll` 与 nohz_full 的交互缺陷——polling 期间 `TS_FLAG_INIDLE` 被误置导致 tick 在 nohz_full CPU 上被重启、唤醒后持续打断用户态。方案由 Frederic Weisbecker 建议。
- sched-20261112-017：Frederic 给 Reviewed-by；K Prateek 提 nit（用 `guard(irqsave)()` 简化）；Peter 表示「只收到四封里的一封，所以一直没看」，Marco 道歉并承诺下一版 CC 完整系列。
- sched-20261113-019（今天）：**v3 发出（当日仅见 patch 2/5）**——采纳 `guard(irqsave)()` 简化，patch 2 的 `tick_nohz_idle_enter()` 移到 `cpuidle_idle_call()` 前、`tick_nohz_idle_exit()` 在 `cpu_idle_poll()` 前，并附 Frederic 的 Reviewed-by。

## 背景与问题
（承接 20261111-004 / 20261112-017）`TS_FLAG_INIDLE` 告诉 nohz 框架「CPU 的 tick 由 idle 循环还是 IRQ 出口管理」。`idle=poll` 时该标志在 polling 期间被置起，但 `cpu_idle_poll()` 不在中断后重新评估 nohz 状态：nohz_full 的 kick 或已停 tick 的到期直到 `TIF_NEED_RESCHED` 置位才被重新评估，tick 在 polling 前被重启，nohz_full CPU 上唤醒后持续打断用户态。今日 v3 发出。

## 技术方案
（承接 v2，采纳 K Prateek 的 `guard(irqsave)()` 建议）仅沿 cpuidle 路径进入 dynticks idle（`tick_nohz_idle_enter()` 移进 `cpuidle_idle_call()`），在 `cpu_idle_poll()` 前离开（`tick_nohz_idle_exit()`）。polling 期间 tick 按「运行中任务」在 IRQ 出口管理：nohz_full CPU 上尽可能保持停止、唤醒后无事可做，任务不用为唤醒后的 tick stop 付费；其它 CPU 离开 dynticks idle 后重启 tick 如旧。`tick_nohz_idle_enter()` 现在可能每次 idle 循环迭代都调用、恒在关中断下运行；`tick_nohz_idle_exit()` 可能在 dynticks idle 之外、关中断下被调用。

## 版本演进与当前进展
v1 → v2（20261111）→ **v3（今日，仅见 2/5）**。v3 采纳 `guard(irqsave)()` 简化并携带 Frederic 的 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Frederic Weisbecker（nohz 维护者）**：Reviewed-by（patch 2 已带）。
- 无 NAK；此前 Peter 的「只收到一封」是分发问题（作者已承诺下版 CC 完整系列），非技术异议。

## 合入评估
有 Frederic Reviewed-by、方案由他建议，合入概率高；当前待完整 v3 系列（5 补丁）被维护者完整评审收取。

## 效果评估
无 benchmark；属 nohz_full 下 tick 行为修复（消除 polling 后持续打断用户态）。

## 我可以参与的点
- **review**：核对 `tick_nohz_idle_exit()` 在「dynticks idle 之外、关中断」新调用语义下无副作用。
- **testing**：在 nohz_full + `idle=poll` 环境验证 tick 停止/重启行为与唤醒延迟。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/
- v3 patch 2/5: https://lore.kernel.org/all/20261112163813.524336-3-marco.crivellari@suse.com/

---
id: sched-20261113-019
subject: "sched/idle: Don't handle polling idle as dynticks idle"
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261111114406.346953-1-marco.crivellari@suse.com>"
lore_url: "https://lore.kernel.org/all/20261111114406.346953-1-marco.crivellari@suse.com/"
authors: [Marco Crivellari]
maintainers_involved: [Frederic Weisbecker]
current_version: v3
patch_series:
  - version: v2
    msgid: "<20261111114406.346953-1-marco.crivellari@suse.com>"
    date: 2026-11-11
    summary: "四补丁修 idle=poll 与 nohz_full 交互（进入 dynticks idle 限定 cpuidle 路径）"
    review_outcome: "Frederic Reviewed-by；K Prateek 建议 guard(irqsave)() 简化"
  - version: v3
    msgid: "<20261112163813.524336-1-marco.crivellari@suse.com>"
    date: 2026-11-13
    summary: "采纳 guard(irqsave)() 简化，携带 Reviewed-by"
    review_outcome: "刚发出（仅见 2/5），暂无新回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "完整 v3 系列（5 补丁）待维护者完整评审收取"
contribution_opportunities:
  - kind: review
    description: "核对 tick_nohz_idle_exit() 新调用语义（dynticks idle 外、关中断）无副作用"
  - kind: testing
    description: "nohz_full + idle=poll 环境验证 tick 停止/重启与唤醒延迟"
generated_at: "2026-11-14T01:30:00"
source_email_count: 1
related_articles: [sched-20261111-004, sched-20261112-017]
tags: [nohz, idle]
---