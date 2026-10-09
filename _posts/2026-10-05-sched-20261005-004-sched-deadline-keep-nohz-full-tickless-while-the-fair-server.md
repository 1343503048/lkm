---
id: sched-20261005-004
date: '2026-10-05'
subject: 'sched/deadline: keep nohz_full tickless while the fair server is deferred'
subsystem: sched
type: fix
status: rfc
severity: medium
thread_root_msgid: <20261005132038.353661-1-ionut.nechita@windriver.com>
lore_url: https://lore.kernel.org/all/20261005132038.353661-1-ionut.nechita@windriver.com/
authors:
- Ionut Nechita
maintainers_involved: []
current_version: RFC v1
patch_series:
- version: RFC v1
  msgid: <20261005132038.353661-1-ionut.nechita@windriver.com>
  date: '2026-10-05'
  summary: 武装 server 与保持 tick 解耦；inc/dec_dl_tasks 重估 tick 依赖；永不从 sched_can_stop_tick()
    停 server
  review_outcome: 发布当日无回帖
related_articles:
- sched-20260925-013
- sched-20261001-002
- sched-20261002-003
upstream_commit: null
fixes_commit: 557a6bfc662c
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 无维护者 review；ext_server 适配未做；sched_can_stop_tick() 锁上下文待确认
  next_action: Juri v3 整合本 RFC 分层思路
generated_at: '2026-10-06T01:00:00'
tags:
- deadline
- dl_server
- nohz
title: 'sched/deadline: keep nohz_full tickless while the fair server is deferred'
layout: article
---

> **subject**：`sched/deadline: keep nohz_full tickless while the fair server is deferred`

## TL;DR

Ionut Nechita（Wind River）把此前讨论中的「tickless 变体」落成正式 RFC：在 nohz_full 核上，把「武装 fair server 保 CFS 带宽」与「为 server 保持 tick」两个关注点拆开——`sched_can_stop_tick()` 只负责武装 server（RT+CFS 共存且有 runtime 配置时 `dl_server_start()`），**deferred（节流等待 dl_timer）状态下不强制 tick**；`inc_dl_tasks()/dec_dl_tasks()` 为 dl_server 实体补调 `sched_update_tick_dependency()`（server 不走 `add_nr_running()`，此前 dl_timer 入队 server 时无人重估 tick 依赖）；**永远不从 `sched_can_stop_tick()` 停 server**——start/stop 对背着 `running_bw` 带宽状态机，在 enqueue/dequeue 频率上循环会下溢（作者同日提交了 15 splats/4min 的可靠复现器）；teardown 留给 `__pick_task_dl()` 既有的 lazy 路径。实测：SCHED_RR hog + 每秒一次 CFS 访问的隔离核，此前 200 次 local_timer_entry/s（tick_stop 依赖报 SCHED），变体下降到「每周期几次 defer/inactive timer 中断，而非一个 tick」；对照 fair_server 关闭时 ~19/s。基于 Juri Lelli 上游 v2 适配到自家树（6.18.15-rt、有 fair server 无 SCX ext_server），`Fixes: 557a6bfc662c`；ext_server 处理留给上游 v3。

## 背景与问题

nohz_full 隔离核上 RT（SCHED_RR/FIFO）与 CFS 任务共存时，fair（dl-）server 必须武装，否则 CFS 拿不到预留带宽（默认 50ms/1s）。Juri Lelli 的 v2 用「`sched_can_stop_tick()` 返回 false」实现——但这让 tick 在 **CFS 任务等待的全程**保持运转，而 deferred server 的大部分周期处于 zero-laxity 等待态（节流、不在 dl_rq 上、等 dl_timer），该等待由 hrtimer 驱动、根本不需要 tick。实测代价：隔离核 tick 从此再也不停（200 irq_vectors:local_timer_entry/s，tick_stop 报 dependency=SCHED；fair_server 禁用时基线 ~19/s）。另有一层正确性问题（作者同日复现）：从 `sched_can_stop_tick()` 停 server 的路径会以 enqueue/dequeue 频率循环 start/stop，`running_bw` 下溢触发 WARN——详见 <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-003-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261005-003</a>。

## 技术方案

RFC（`<20261005132038.353661-1-ionut.nechita@windriver.com>`，kernel/sched/core.c + deadline.c，+29/−1）：

- **`sched_can_stop_tick()`（core.c）**：
  - `rq->dl.dl_nr_running` 判定注释明确覆盖 fair server 在队服务 CFS 的情形（runtime 由 tick 执行）。
  - 新增：`rq->rt.rt_nr_running && rq->cfs.h_nr_queued && rq->fair_server.dl_runtime` 时调 `dl_server_start(&rq->fair_server)`（已激活时为 no-op）武装 server——但不无条件返回 false；仅当非 deferred 的 start 立即把 server 入队（`rq->dl.dl_nr_running` 非零，紧跟复查）才保持 tick。
  - 明确注释：server 永不从这条路 stop——start/stop 对携带 `running_bw` 记账，不得以 enqueue/dequeue 频率循环。
- **`inc_dl_tasks()/dec_dl_tasks()`（deadline.c）**：`dl_server(dl_se)` 分支改调 `sched_update_tick_dependency(rq)`——dl_timer 把 server 入队时 tick 重新启动（runtime 由 tick 执行），server 离开 dl_rq 时再丢弃。此前 server 实体跳过 `add_nr_running()/sub_nr_running()`，无人重估 tick 依赖。
- **teardown**：留给 `__pick_task_dl()` 既有 lazy 路径（无可挑的 fair 任务时停 server）。代价：tickless 核持续接收 server 的 defer/inactive timer——每周期几次中断，而非一个 tick。
- **作用域**：全部收敛在 nohz_full CPU——`sched_update_tick_dependency()` 对 housekeeping CPU 提前返回，`sched_can_stop_tick()`（及新武装逻辑）只在可停 tick 处运行。
- 基于 Juri 上游 v2 适配：针对自家树（有 fair server、无 SCX ext_server）；ext_server 处理待上游 v3。

## 版本演进与当前进展

- 09-24/09-25：Ionut 在 Juri v2 线程实测 + 变体 sketch（<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-013-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20260925-013</a>）。
- 10-01/10-02：Peter review + 撤回 PINNED（<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-002-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261001-002</a>/003）；讨论中 Ionut 描述过 tickless 变体。
- 10-05（今天）：变体落成正式 RFC（本补丁）；同日提交 stop 路径 running_bw 下溢复现器（<a class="article-ref" href="/lkm/2026/10/05/sched-20261005-003-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261005-003</a>）。Juri 当日未回帖。

## Maintainer 意见与讨论焦点

- **Ionut Nechita**（作者）：明确 RFC 性质（downstream 树适配、ext_server 待并）；方案与 Peter「stop 只放真正停 tick 的路径」意见一致。
- **Juri Lelli**（SCHED_DEADLINE 维护者、v2 作者）：当日未回帖；此前已欢迎 Ionut 发 v3。
- **Peter Zijlstra**：当日未回帖；其 10-01 对 v2 的「`dl_servers_stop_all()` 只放 true 分支」意见与本 RFC 的「永不停」更激进收敛同向。
- 焦点：本 RFC 把「武装但不强制 tick」与「入队时再估 tick」拆分后的中间态——server 武装但 deferred 时，CFS 带宽事实上仍依赖 dl_timer 到期后的服务，tick 不在场的窗口内 `update_curr_dl_se()` 由谁驱动（defer timer 本身即驱动源）值得 v3 review 时确认。

## 合入评估

*likelihood=medium*。方案有实测数据、与维护者意见同向、且规避了已实证的 running_bw 地雷；但它是 downstream 树的 RFC，上游化要并入 Juri 的 v3 框架（含 ext_server），中间还隔一轮维护者 review。*blocking_issues*：Juri/Peter 未 review 本 RFC；ext_server（SCX）适配未做；`sched_can_stop_tick()` 里武装 server 的锁上下文（该路径在 rq 锁外评估）需确认。*next_action*：Juri v3 以本 RFC 为基底整合（或直接采纳其分层），Tejun/Peter review。

## 效果评估

作者实测（隔离 nohz_full 核、SCHED_RR hog + 每秒约一次 CFS 任务访问）：tick 不停场景 200 irq_vectors:local_timer_entry/s、tick_stop dependency=SCHED；fair_server 禁用基线 ~19/s；本 RFC 下 tick 可停，残余开销为每周期几次 defer/inactive timer 中断。既有双机数据（09-24）：带宽达标（5.10%）且 tick 数 vanilla/Juri v2/变体 = 66.0/1001.6/54.1 与 0.9/1000.6/52.9 每/s。

## 我可以参与的点

- `review`：核对 `sched_can_stop_tick()` 调用点的锁约束——`dl_server_start()` 在该路径是否可能与非持有 rq 锁的评估并发，与 `dl_server_start()` 自身要求的锁序是否兼容。
- `review`：deferred 窗口内 CFS 服务的正确性推演——server 武装但不在 dl_rq、tick 已停、RT hog 持续运行时，CFS 的 50ms/1s 供给完全依赖 dl_timer 到期，确认无「timer 被迁移到 housekeeping 核」导致的服务延迟放大（呼应 Peter 已撤回的 PINNED 讨论）。
- `testing`：在本 RFC 上跑 09-24 同款双机带宽测试，验证 tick 数下降的同时带宽仍达标（变体 sketch 期数据是否在正式补丁上复现）。

## 参考链接

- RFC 补丁: https://lore.kernel.org/all/20261005132038.353661-1-ionut.nechita@windriver.com/
- running_bw 下溢复现器（同日）: https://lore.kernel.org/all/20261005125013.324327-1-ionut.nechita@windriver.com/
- Juri 上游 v2: https://lore.kernel.org/lkml/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
- Peter 10-01 review: https://lore.kernel.org/all/20261001142735.GT2009045@noisy.programming.kicks-ass.net/
