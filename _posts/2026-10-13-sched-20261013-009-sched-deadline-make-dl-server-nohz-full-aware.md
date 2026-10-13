---
id: sched-20261013-009
subject: 'sched/deadline: Make dl-server nohz full aware'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261013133010.390823-1-ionut.nechita@windriver.com>
lore_url: https://lore.kernel.org/all/20261013133010.390823-1-ionut.nechita@windriver.com/
authors:
- Ionut Nechita
maintainers_involved:
- Juri Lelli
current_version: v3
patch_series:
- version: v2
  msgid: <20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>
  date: 2026-05-13
  summary: 保持 tick 不停以达带宽，代价满速 tick
  review_outcome: Peter/Frederic/Juri 讨论，PINNED 建议被撤回
- version: v3
  msgid: <20261013133010.390823-1-ionut.nechita@windriver.com>
  date: 2026-10-13
  summary: arm-only + inc/dec_dl_tasks 驱动 tick，不从 tick-stop 路径 stop server
  review_outcome: 当日无回帖，待复审
upstream_commit: null
fixes_commit: 557a6bfc662c
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 未 review；defer/inactive 定时器残留开销未闭环
  next_action: Peter/Juri 复审 v3 后收取
contribution_opportunities:
- kind: testing
  description: 在 nohz_full + PREEMPT_RT 环境复测 v3 tick 率与带宽达标并回帖
- kind: discussion
  description: 评估 defer/inactive 定时器残余开销，或探讨 hrtimer_start_on() 方向
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261001-002
- sched-20261002-003
- sched-20261005-003
tags:
- deadline
- nohz
title: 'sched/deadline: Make dl-server nohz full aware'
layout: article
---

> **subject**：sched/deadline: Make dl-server nohz full aware

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-013-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20260925-013</a>：Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月未被收取）重新活跃——Ionut Nechita 发现 v2 恢复了 CFS 带宽保证但把隔离核变成满 CONFIG_HZ tick。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-002-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261001-002</a>：Frederic Weisbecker 提出根本性概念问题；Peter Zijlstra 给具体 review（dl-server 定时器加 PINNED、`dl_server_stop_all()` 只放 true 分支），并称方向「best we can hope for」。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-003-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261002-003</a>：Peter 自我否决 PINNED 建议（远程 enqueue 下钉错 CPU，需尚不存在的 `hrtime_start_on()` 原语）。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-003-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261005-003</a>：Ionut 给出 stop-from-tick-stop 路径的可靠复现器与 `running_bw` 下溢双 WARN splats，证明 stop 必须收敛到真正停 tick 的路径。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-009-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261013-009</a>（今天）：Ionut 发 **v3**——重做机制：`sched_can_stop_tick()` 只在 RT 与 CFS/SCX 共存时武装 server、不强制 tick；tick 的启停改由 `inc_dl_tasks()/dec_dl_tasks()` 在 server 进出 dl_rq 时驱动，且不再从 tick-stop 路径 stop server。

## 背景与问题
（承接 20261001-002 → 20261005-003）nohz_full 隔离核上 RT（SCHED_FIFO）与 CFS 任务共存时，dl-server 应在 RT 占满 CPU 的情况下保证 CFS 预留带宽（fair_server 默认 50ms/1s）；但 CFS 带宽记账依赖 tick 调 `update_curr_dl_se()`，安静隔离核上 tick 完全停止导致记账缺位。v2 用「保持 tick 不停」换带宽达标，代价是满速 tick（实测 200 irq_vectors/s vs fair server 关闭时的 ~19/s）；且从 enqueue/dequeue 频率上循环 start/stop server 会让 `rq->dl.running_bw` 状态机下溢触发 WARN。v3 的目标是把「武装 server」与「强制 tick」两件事解耦：deferred server 大部分时间处于零松弛等待（throttled、off dl_rq、等 hrtimer），本不需要 tick。

## 技术方案
v3（`kernel/sched/core.c` +32/−1、`kernel/sched/deadline.c` +4，base tip/sched/core）：
- `sched_can_stop_tick()`：当 `rq->rt.rt_nr_running` 时，若有 CFS 队列则 `dl_server_start(&rq->fair_server)`、若有 SCX 队列则 `dl_server_start(&rq->ext_server)`；非 deferred 启动会立刻 enqueue server，随即经 `rq->dl.dl_nr_running` 复查而保持 tick。
- `inc_dl_tasks()/dec_dl_tasks()`：对 `dl_server()` 分支补 `sched_update_tick_dependency()`——server 入 dl_rq 时启动 tick（其 runtime 由 tick 强制），离开 dl_rq 时再停。
- 不再从 `sched_can_stop_tick()` stop server（避免 `running_bw` 下溢），teardown 交给既有的 `__pick_task_dl()` 惰性路径；代价是 tickless 核继续收 server 的 defer/inactive 定时器（每周期几次中断，非 tick）。
- 全局限定 nohz_full CPU（housekeeping CPU 上 `sched_update_tick_dependency()` 早退）。

`Fixes: 557a6bfc662c ("sched/fair: Add trivial fair server")`。

## 版本演进与当前进展
v3 今日首发（`<20261013133010.390823-1-ionut.nechita@windriver.com>`）。相对 v2：机制重做（arm-only + inc/dec_dl_tasks 驱动 tick）、不再从 tick-stop 路径 stop server、`dl_servers_stop_all()` 已删除、保留 SCX ext_server 处理、rebase tip/sched/core。开放问题：Peter 的 PINNED-timer 想法因缺 `hrtimer_start_on()` 原语搁置，本补丁不依赖它。当日无回帖。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（sched 维护者）：前期认可方向（「best we can hope for」），PINNED 建议已自我撤回；「`dl_server_stop_all()` 只放 true 分支」与 v3「不从 tick-stop 路径 stop」一致。
- **Juri Lelli**（SCHED_DEADLINE 维护者）：对 Peter 前期 diff 表态 OK、澄清 dl-server 激活语义。
- **Frederic Weisbecker**（nohz/tick 维护者）：曾质疑 nohz_full 上 dl-server 的存在合理性（概念分歧，被使用场景解释暂时压下）。
- 焦点：v3 的 arm-only 机制与开放问题（defer/inactive 定时器仍会打扰隔离核）待复审。

## 合入评估
*likelihood=medium*。方向获 Peter/Juri 认可、v3 已按全部讨论意见重做并有双机数据，但仍待 v3 复审。*blocking_issues*：v3 未 review；PINNED/远程 hrtimer 的遗留开销未闭环。*next_action*：Peter/Juri 复审 v3，确认 arm-only 机制与 ext_server 语义后收取。

## 效果评估
v3 提交信息引用 v2 阶段的实测：SCHED_RR hog + CFS 任务每秒访问一次隔离核，v2 方案 tick 永不停止（200 irq_vectors:local_timer_entry/s，tick_stop 报 dependency=SCHED），fair server 关闭时约 19/s；v3 声称把 tick 率从满 CONFIG_HZ 降到「服务窗口内才计」。具体 v3 的 tick/s 数字未在提交信息里给出完整对比（提交信息描述为「drops from CONFIG_HZ to ~the service window」）。

## 我可以参与的点
- testing：在 nohz_full + PREEMPT_RT 环境复测 v3 的 tick 率（RT hog + CFS 共存）与带宽达标，回帖提供数据。
- discussion：评估「defer/inactive 定时器仍打扰隔离核」的残余开销是否可接受，或探讨 Peter 的 PINNED/`hrtimer_start_on()` 方向。

## 参考链接
- v3 lore：https://lore.kernel.org/all/20261013133010.390823-1-ionut.nechita@windriver.com/
- v2 线程：https://lore.kernel.org/lkml/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
