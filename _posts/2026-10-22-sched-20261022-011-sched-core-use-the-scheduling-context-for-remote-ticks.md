---
id: sched-20261022-011
date: 2026-10-22
subject: 'sched/core: Use the scheduling context for remote ticks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>
lore_url: https://lore.kernel.org/all/20261021-remote-tick-proxy-v3-1-8c37c5b4d6f6@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261021-remote-tick-proxy-v3-1-8c37c5b4d6f6@gentwo.org>
  date: 2026-10-22
  summary: 重写 changelog、清理 racily 说明、加 John Stultz Acked-by
  review_outcome: John Stultz Acked-by；Christian NIT 已吸收
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待维护者收取
contribution_opportunities:
- kind: testing
  description: 在其它 proxy execution + full-nohz 平台复现并验证
generated_at: '2026-10-23T01:20:00'
source_email_count: 4
related_articles:
- sched-20261021-012
tags:
- nohz
- proxy_execution
title: 'sched/core: Use the scheduling context for remote ticks'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-005-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261017-005</a>：Shubhang Kaushik（Ampere）单补丁——full-nohz 远程 tick `sched_tick_remote()` 对 `rq->curr` 调 `task_tick()`，但 proxy execution 下 `rq->curr` 是 mutex-owner 执行上下文、`rq->donor` 才是调度上下文；改为对 `rq->donor` 调 `task_tick()` 并移除「full-nohz 下必有单任务」的 `WARN_ON_ONCE(curr!=donor)`。带 `Fixes: 7de9d4f94638`。
- <a class="article-ref" href="/lkm/2026/10/19/sched-20261019-010-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261019-010</a>：Christian Loehle（Arm）回帖排版 NIT + 提示可参考 sashiko 审查页。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-012-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261021-012</a>：作者回复 Christian——确认 full-nohz 区间 sanity check 同样假设 `rq->curr` 是调度上下文，宣布 v2 统一用 `rq->donor`。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-011-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261022-011</a>（今天）：作者发 v3——按 John Stultz 建议重写 changelog（说明 full-nohz 可在「SCHED_FIFO 或单 SCHED_RR」情况下以多任务停止 tick、从而允许 proxy execution），澄清 racy 的 tick-stopped 检查非触发必需，并加 John Stultz 的 Acked-by。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-005-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261017-005</a>）proxy execution 下 `rq->curr`（mutex owner 执行上下文）与 `rq->donor`（真正被代理执行的调度上下文）分离；`sched_tick_remote()` 落在 `rq->curr` 上做调度记账，与真正该记账的 `rq->donor` 不一致。关键补充事实（今日写入 changelog）：`sched_can_stop_tick()` 在「无 SCHED_RR 任务时 SCHED_FIFO 无强制 tick 抢占」「恰好一个 SCHED_RR 任务」两种情况下都能合法地在 rq 上还排队着其它任务时停止 tick，于是被 SCHED_NORMAL mutex owner 阻塞的 SCHED_FIFO 任务仍可为 `rq->donor`，而 `find_proxy_task()` 选 owner 为 `rq->curr`。

## 技术方案
（承接 v1/v2）v3（`<20261021-remote-tick-proxy-v3-1-8c37c5b4d6f6@gentwo.org>`）：`sched_tick_remote()` 改用 `rq->donor` 作远程类 tick 与 full-nohz tick 区间 sanity check，对齐 `sched_tick()` 与 `hrtick()`。v3 变化：重写 changelog（解释多任务下可停 tick）、澄清 racy 检查非必需、加 Acked-by。原 `WARN_ON_ONCE(rq->curr != rq->donor)` 已移除。

## 版本演进与当前进展
*current_version: v3*（`<20261021-remote-tick-proxy-v3-1-8c37c5b4d6f6@gentwo.org>`）。v1: `<20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>`，v2: `<20261021-remote-tick-proxy-v2-1-07890601a71e@gentwo.org>`。v3 已带 John Stultz Acked-by。

## Maintainer 意见与讨论焦点
John Stultz（Google）此前审读后认可代码改动，主要意见是 commit message 过于聚焦 proxy 细节、难懂「底层假设如何被打破」，并建议澄清 racy 的 full-nohz 检查是否相关——均已在 v3 落实并获其 Acked-by。Christian Loehle 的排版 NIT 亦已吸收。无反对意见。

## 合入评估
*likelihood=high*。v3 已收 John Stultz Acked-by，代码与 changelog 均收敛、带明确 Fixes；*blocking_issues*：无；*next_action*：等待维护者收取。

## 效果评估
作者在 Ampere Altra（`CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_NO_HZ_FULL=y`，`sched_proxy_exec=1 nohz_full=78`）复现：未打补丁基线（70dd4ee72eb2，7.3.0-rc7）上 mutex locktorture 四写者 + RT boosting 触发 `WARNING: cpu/… @ sched_tick_remote`（`WARN_ON_ONCE(rq->curr != rq->donor)`）；v3 补丁跑同样 10 分钟负载无告警、无 locktorture 失败。

## 我可以参与的点
- *kind: testing*：在其它 proxy execution + full-nohz 平台上复现并验证修复。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org/
- v3: https://lore.kernel.org/all/20261021-remote-tick-proxy-v3-1-8c37c5b4d6f6@gentwo.org/
