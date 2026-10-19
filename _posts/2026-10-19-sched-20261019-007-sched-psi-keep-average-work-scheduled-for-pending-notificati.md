---
id: sched-20261019-007
subject: 'sched/psi: Keep average work scheduled for pending notifications'
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261019041456.2589789-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261019041456.2589789-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261019041456.2589789-1-sh_def@163.com>
  date: 2026-10-19
  summary: 平均聚合 worker 提前运行时检查 pending 事件，复用 trigger walk 结果，通知投递后允许回到 idle
  review_outcome: 暂无回帖
upstream_commit: null
fixes_commit: d82caa273565
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  next_action: 等 PSI 维护者 review
contribution_opportunities:
- kind: testing
  description: 真实 cgroup v2 非特权轮询负载下复现 pending 通知不投递并验证修复
- kind: review
  description: 复核 psi_show() 推进 avg_next_update 与 worker 提前运行的时序交互
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles: []
tags:
- psi
title: 'sched/psi: Keep average work scheduled for pending notifications'
layout: article
---

## TL;DR

Hui Su 发往 sched/psi 的单补丁修复：非特权 PSI trigger 用平均聚合 worker，若在 rate-limit 窗口内触发阈值、通知被 `pending_event` 推迟，而窗口未到压力就停了，`psi_avgs_work()` 因 `PSI_STATE_RESCHEDULE` 不再置位而停止续排，pending 事件可能一直不投递直到新活动重启 worker。补丁复用 trigger walk 结果、提前检查 pending 事件。当日新发，暂无回帖。

## 背景与问题

非特权 PSI trigger 走平均聚合（PSI_AVGS）worker。阈值在 rate-limit 窗口内被突破时，通知经 `pending_event` 推迟。若压力在 rate limit 到期前停止，`psi_avgs_work()` 因 `PSI_STATE_RESCHEDULE` 未置位而停止续排，pending 事件悬空，直到有新的压力活动重启 worker 才投递——即非特权轮询可能漏发一次通知。带 `Fixes: d82caa273565 ("sched/psi: Allow unprivileged polling of N*2s period")`。

## 技术方案

单补丁（`kernel/sched/psi.c`，+25/−5）：平均更新到期时复用 trigger walk 结果；worker 提前运行时检查 pending 事件（因为 `psi_show()` 可能在未处理 trigger 的情况下推进 `avg_next_update`）；通知投递完成且压力停止后允许 worker 重新回到 idle。

## 版本演进与当前进展

*current_version: v1*。当日新发（`<20261019041456.2589789-1-sh_def@163.com>`），暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无回帖。潜在评审点（无人提出）：复用 trigger walk 结果与 `psi_show()` 推进 `avg_next_update` 的时序交互是否正确覆盖所有 pending 场景。

## 合入评估

*likelihood=unknown*。改动小、带 KUnit + QEMU 复现数据，但当日无 review。*blocking_issues*：无 review。*next_action*：等 PSI 维护者（Johannes Weiner）review。

## 效果评估

作者测试（x86_64）：KASAN KUnit 候选 PSI_AVGS 6/6 通过（含 trigger 销毁）、refcount 4/4 通过、无 KASAN 报告（基线有 3/6 预期回归失败）；QEMU cgroup v2 非特权 `some 5000 4000000`：基线在 `pending=1/rearm=0` 时漏发第二次事件，候选在 3999.9ms 以 `pending=1/rearm=1` 投递后清除 pending，第二次压力 delta 505240/490317 us、静默期 delta 均为 0。

## 我可以参与的点

- `testing`：在真实 cgroup v2 非特权轮询负载下复现「压力提前停止导致 pending 通知不投递」并验证修复。
- `review`：复核 `psi_show()` 推进 `avg_next_update` 与 worker 提前运行的时序交互。

## 参考链接

- patch：https://lore.kernel.org/all/20261019041456.2589789-1-sh_def@163.com/
