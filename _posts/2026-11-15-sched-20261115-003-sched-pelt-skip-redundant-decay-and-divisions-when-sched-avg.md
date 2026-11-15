---
id: sched-20261115-003
date: '2026-11-15'
subject: 'sched/pelt: Skip redundant decay and divisions when sched_avg is zero'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com>
lore_url: https://lore.kernel.org/all/18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com/
authors:
- Chris Wiseman
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com>
  date: '2026-11-15'
  summary: 零负载且 sched_avg 已归零时提前返回；!running 跳过 irq 冗余二次调用
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待维护者 review 优化路径与 tg_load_avg_contrib flush 的必要性
contribution_opportunities:
- kind: review
  description: 核对提前返回是否遗漏 sa 字段/边界场景（如新 fork 任务 load_avg 非零）
- kind: testing
  description: 在 arm64/riscv 或不同 CONFIG 下复现 bit-for-bit 验证与周期级基准
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- perf
- cpufreq
title: 'sched/pelt: Skip redundant decay and divisions when sched_avg is zero'
layout: article
---

## TL;DR

Chris Wiseman（Google）发 PELT 微优化：当 sched_avg 各字段已衰减归零时，`accumulate_sum()` 仍跑三次 `decay_load(0, periods)` 并在跨 1024us 边界后返回 periods>0，触发 `___update_load_avg()` 做三次零除法并向 `cpufreq_update_util()` 报告虚假 decay；`update_irq_load_avg(rq, 0)` 也无条件二次调用 `___update_load_sum()`（恒返 0）。补丁在零负载+已归零时提前返回 0，并在 `!running` 时跳过 capacity scaling 与二次调用。100 万步随机化验证 bit-for-bit 一致，x86_64 微基准 idle 场景 -74.7%、最坏 +0.5%。

## 背景与问题

承接 commit d040e0734fb3（跳过零负载的 `__accumulate_pelt_segments()`，因 load==0 时调用频率是 45 倍）。但该优化没覆盖的是：即使 load 为零且 `sa->load_sum`、`sa->runnable_sum`、`sa->util_sum`、`sa->load_avg` 都已衰减归零，`accumulate_sum()` 仍执行三次 `decay_load(0, periods)`，且每跨 1024us PELT 周期边界就返回 periods>0 → `___update_load_avg()` 做三次 `0 / divider` 除法，并向 `__sched_balance_update_blocked_averages()` → `cpufreq_update_util()`（commit bef69dd87828 接入）报告虚假 decay。此外 `update_irq_load_avg(rq, 0)` 在 running==0 时无条件再次调用 `___update_load_sum()`——首次调用已把 last_update_time 推进到 `rq->clock & ~1023ULL`，二次调用 delta<1024 恒返 0，纯属冗余的 clock/capacity scaling 运算。

## 技术方案

在 `___update_load_sum()` 里，当 `!load` 且 `unlikely(!(sa->load_sum | sa->runnable_sum | sa->util_sum | sa->load_avg))` 时，仅更新 `sa->period_contrib = (delta + sa->period_contrib) % 1024` 并 return 0（检查 load_avg 是为新 fork 任务的 `init_entity_runnable_average` 场景）；同时在 `__update_blocked_fair()` 里补 flush 残留的 rate-limited `cfs_rq->tg_load_avg_contrib`。`update_irq_load_avg()` 在 `!running` 时跳过两次 `cap_scale` 与第二次 `___update_load_sum()` 调用。改动 kernel/sched/pelt.c +21/-7、kernel/sched/fair.c +2。

## 版本演进与当前进展

*current_version: v1（2026-11-15，`<18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com>`）*。当日发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

当日无维护者/资深成员回帖。作者附详细的正确性验证（bit-for-bit 一致）与逐场景性能数据作为论据。

## 合入评估

*likelihood=unknown*。纯优化、不改语义并有 bit-for-bit 验证，方向合理，但尚无维护者表态。*blocking_issues*：无实质分歧，等待 maintainer review。*next_action*：等待 Vincent Guittot/Ingo 等维护者 review 提前返回路径的正确性及 flush tg_load_avg_contrib 的必要性。

## 效果评估

作者 1,000,000 步随机化验证 `update_other_load_avgs()` 各字段 bit-for-bit 一致；10,000,000 次迭代 x86_64 微基准（1ms blocked-avg 更新）：idle（RT/DL/HW/IRQ）72.53→18.33 cyc（-74.7%），100% active RT+DL+HW+IRQ（最坏）99.21→99.68 cyc（+0.5%）。RT/DL/HW/IRQ 均值已归零时，`update_other_load_avgs()` 的虚假 decay 返回从 100% 降到 0。

## 我可以参与的点

- **review**：核对提前返回是否遗漏 sa 字段或边界场景（尤其新 fork 任务 load_avg 非零、其余字段为零的路径），以及 `tg_load_avg_contrib` flush 的时序。
- **testing**：在 arm64/riscv 或不同 CONFIG（如 CONFIG_SMP 关、无 irq load avg）下复现 bit-for-bit 验证与周期级基准。

## 参考链接

- lore thread: https://lore.kernel.org/all/18e837a02ddbadb6.3137322e32332e3235332e313736.1b3220.0000sendgmr@google.com/
