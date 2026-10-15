---
id: sched-20261015-021
date: 2026-10-15
subject: 'sched/rt: Avoid RTO push to stopped CPUs during shutdown'
subsystem: sched
type: fix
status: superseded
severity: low
thread_root_msgid: <20261015014005.8885-1-wangqk1@xiaopeng.com>
lore_url: https://lore.kernel.org/all/20261015014005.8885-1-wangqk1@xiaopeng.com/
authors:
- wangqk1
maintainers_involved:
- Peter Zijlstra
current_version: null
patch_series:
- version: v1
  msgid: null
  date: 2026-10-13
  summary: rto_next_cpu() 读 system_state + 跳过 offline CPU
  review_outcome: Peter 否决（horrific），作者今日撤回
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 方案方向被维护者否决
  next_action: 若要推进需在 arm64 停机路径处理 rto overload 状态；当前无后续
contribution_opportunities:
- kind: discussion
  description: 探讨 arm64 关机路径如何正确清理 rto overload 状态
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20261013-003
tags:
- rt
- arm64
title: 'sched/rt: Avoid RTO push to stopped CPUs during shutdown'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-003-sched-rt-avoid-rto-push-to-stopped-cpus-during-shutdown.html">sched-20261013-003</a>：wangqk1（小鹏）发 RFC——SMP PREEMPT_RT arm64 关机时 `machine_power_off()` 触发 `smp_send_stop()`，被 stop 的 CPU 不跑 hotplug teardown，RT overload 状态残留 stale `rto_mask` 位；仍在跑的 CPU 的 `rto_push_irq_work_func()` 会选中该 stale 位并把 irq_work 排到已停机 CPU。Peter Zijlstra 直接否定该方案（「This is horrific; lets not do this」），要求把 bug 修在「无预警停机 CPU」的地方。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-021-sched-rt-avoid-rto-push-to-stopped-cpus-during-shutdown.html">sched-20261015-021</a>（今天）：wangqk1 明确**撤回该补丁**，并补充触发细节——arm64 正常 poweroff 路径（非 panic/crash）就命中，`machine_power_off()` 在 `do_kernel_power_off()` 前调 `smp_send_stop()`。

## 背景与问题
（承接 20261013-003）arm64 上 `machine_power_off()` 先 `smp_send_stop()`，被停的 secondary CPU 不跑 hotplug teardown（尤其 `rq_offline_rt()` 不执行），overloaded RT runqueue 残留 stale `rto_mask` 位；另一 CPU 仍可跑 `rto_push_irq_work_func()` 并选中该位。作者补充：这发生在**正常 orderly poweroff** 路径，不是 panic/crash。

## 技术方案
（承接 20261013-003）原方案在 `rto_next_cpu()` 加 `rto_push_allowed()`（读 `system_state`，终止态返回 false）并跳过 `!cpu_online()` 候选。Peter 已否。今日作者撤回补丁，认同修复应落在「把 CPU 停下来的路径」（需考虑 rto overload 状态），并表态若找到可行方式会再提出，愿意测试/审查该领域任何改动。

## 版本演进与当前进展
- RFC（2026-10-13）：见 related 文章。
- 今天：作者撤回补丁，讨论暂告一段落。

## Maintainer 意见与讨论焦点
Peter Zijlstra 的否定立场不变（修在停机路径，而非 rt push 侧打 workaround）。作者接受并撤回。

## 合入评估
*likelihood=rejected*。维护者否决该方案、作者撤回。*blocking_issues*：方案方向被否。*next_action*：若重新推进，需在 arm64 停机路径（`smp_send_stop`/`machine_power_off`）处理 rto overload 状态；当前无后续。

## 效果评估
无量化数据；观测到的调用栈（`irq_work_queue_on → rto_push_irq_work_func → ...`）为定性证据。

## 我可以参与的点
- *discussion*：若要真正修复，可探讨 arm64 关机路径如何正确清理 rto overload 状态（`rq_offline_rt()` 等价物），作者已表示愿意测试/审查。

## 参考链接
- 作者撤回并补充细节：https://lore.kernel.org/all/20261015014005.8885-1-wangqk1@xiaopeng.com/
- Peter 的否决：https://lore.kernel.org/all/20261013120302.GJ2009045@noisy.programming.kicks-ass.net/
