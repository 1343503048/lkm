# sched/deadline: Make dl-server nohz full aware

> **subject**：`sched/deadline: Make dl-server nohz full aware`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260925-013：Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月未被收取）重新活跃——Ionut Nechita 发现 v2 恢复了 CFS 带宽保证但把隔离核变成满 CONFIG_HZ tick，给出「只在 server 实际 enqueue 期间保持 tick」的变体，Juri 欢迎其发 v3。
- sched-20261001-002：Frederic Weisbecker 提出根本性概念问题（nohz_full 上为什么会有 dl-server 在跑）；Juri 解释 fair 任务入队到正跑 FIFO 任务的核时 dl-server 兜底激活；Peter Zijlstra 给出具体 review——dl-server 定时器应加 `HRTIMER_MODE_PINNED`、`dl_server_stop_all()` 只放 true 分支，并称方向「more or less the best we can hope for」。
- sched-20261002-003：Peter 自我否决了 PINNED 建议——远程 enqueue 时可以在远端启动 dl-server，一旦 timer 被 PINNED 就落在「错误」的 CPU 上；正确做法需要尚不存在的 `hrtime_start_on()` 原语，「So scrap this for now :-(」。
- sched-20261005（今天）：Ionut 给出 `dl_servers_stop_all()` 类路径的**可靠复现器与 splats**——PREEMPT_RT 6.18.15-rt、隔离 nohz_full CPU 2 上以 SCHED_FIFO hog + CFS 共存 + perf/fork-exit 短命任务搅动，4 分钟 15 次 WARN：`dl_server_stop()` 在 inactive_timer 仍武装时扣减从未加回的 `running_bw` → 下溢，`__sub_running_bw()`（deadline.c:239）与 `task_non_contending()`（deadline.c:425）双 WARN，schedule 路径与 hrtimer 路径都触发。虽未在 Juri v2 原样上复现，但交错相同——**结论是把 stop 收敛到真正停 tick 的路径**（与 Peter 意见一致）。Frederic 简短回复 Peter 的 hrtimer 讨论：非 PINNED hrtimer 不如 jiffies timer 那样容易迁移——侧面支持「暂不做 PINNED」的现状。

## 背景与问题

（承接 sched-20260925-013 → sched-20261002-003）nohz_full 隔离核上 RT 与 CFS 任务共存时，dl-server 应在 RT 占满 CPU 的情况下保证 CFS 预留带宽（fair_server 默认 50ms/1s）；但 CFS 带宽记账依赖 tick，安静隔离核上 tick 完全停止导致记账缺位。Juri v2 用「保持 tick 不停」换带宽达标（代价满速 tick）；Ionut 变体只在 server 实际 enqueue 期间保持 tick。今天的新问题是**stop 侧的隐藏地雷**：`dl_server_start()/dl_server_stop()` 背着 `rq->dl.running_bw` 的「active contending / active non contending」状态机（中间夹 inactive_timer），任何在 enqueue/dequeue 频率上循环 start/stop 的路径都会让状态机超频运转——stop 撞上仍武装的 inactive_timer 时扣掉从未加回的带宽，`running_bw` 下溢触发 WARN。

## 技术方案

（承接）Juri v2：`sched_can_stop_tick()` 里 `rt_nr_running && cfs.h_nr_queued` 时启动 fair_server 不让 tick 停；Ionut 变体：仅 server 实际 enqueue 期间保持 tick。PINNED 建议已被 Peter 撤回（远程 enqueue 下钉错 CPU，需尚不存在的 `hrtime_start_on()` 原语）。

今天的复现器（Ionut，`<20261005125013.324327-1-ionut.nechita@windriver.com>`）：

- 环境：PREEMPT_RT、kernel 6.18.15-rt、Dell PowerEdge R750、隔离 nohz_full CPU 2、fair_server 默认 50ms/1s。
- 负载：SCHED_FIFO hog + CFS 任务共存（fair_server 武装），perf 与 fork()/exit() 循环在该核上反复来去——`dl_server_start()/dl_server_stop()` 以 wakeup/dequeue 频率循环穿过带宽记账状态机。
- 触发代码（Ionut 自己变体的早期版本）：在 `sched_can_stop_tick()` 的 RR/FIFO 分支加 `sched_tick_stop_fair_server()`（`!rt_nr_running || !h_nr_queued` 时 stop）——该函数随每次 `add_nr_running()/sub_nr_running()` 被评估，即 stop 以 enqueue/dequeue 频率驱动。
- 结果：15 次 WARN / ~4 分钟，双 WARN 位点、双路径（`pick_task_dl → task_non_contending → __schedule` 与 `inactive_task_timer → hrtimer_interrupt`）。Ionut 现行版本（不在 tick-stop 路径 stop）干净。
- 定位：与 Juri v2 里 `dl_servers_stop_all()` 只在 RT-only 分支调用的结构同源——「it is the same interleaving」，故建议把 stop 收敛到真正停 tick 的路径（Peter 在 v2 上也已指出这一点）。

**Frederic 的回复**（`<asO1DctL9BydDNGV@localhost.localdomain>`，回 Peter 10-01）：非 PINNED 的 hrtimer 不像非 PINNED 的 jiffies timer 那样容易迁移（"non pinned hrtimers don't move as easily as non pinned jiffies timers. But yes."）——是对 Peter「PINNED 撤回、dl-server timer 迁移问题暂搁」讨论的技术注脚，缓解但不消除 timer 落错核的顾虑。

## 版本演进与当前进展

- v2（2026-05-13，`<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>`）：Juri 首发，长期未被收取。
- 09-24/09-25：Ionut 实测 + 变体 sketch；Juri 欢迎 v3（sched-20260925-013）。
- 10-01：Frederic 概念提问 → Juri 解释 → Peter review（PINNED diff + stop_all 建议）→ 布尔化简与 ext_server 交互讨论（sched-20261001-002）。
- 10-02：Peter 撤回 PINNED 建议（sched-20261002-003）。
- 10-05（今天）：Ionut 提交可靠复现器与 splats（此前 Juri 自述无法复现）；Ionut 另发独立 RFC「keep nohz_full tickless while the fair server is deferred」（见 sched-20261005-004）；Frederic 回复 hrtimer 迁移性讨论。v3 仍未发出，但今天的复现器实质上把 v3 的设计约束钉死了：**不得从 `sched_can_stop_tick()` 停 server**。

## Maintainer 意见与讨论焦点

- **Ionut Nechita**（Wind River，报告者/变体作者）：把口头警告升级为可复现证据（Juri 此前未复现成功）；明确「未在 v2 原样上复现」的边界，避免误伤 Juri 的版本。
- **Frederic Weisbecker**：hrtimer 迁移性的技术注脚，回应 Peter 10-01/10-02 的 PINNED 讨论。
- **Juri Lelli**（SCHED_DEADLINE 维护者）：当日未回帖；其 v3 待办现在多了「stop 路径收敛」的硬约束。
- **Peter Zijlstra**：当日未回帖；其 10-01 的「`dl_server_stop_all()` 只放 true 分支」意见与今天的复现器互相印证。
- 焦点：stop-from-tick-stop 的带宽状态机危害已从「理论担忧」变为「有 splats 的实证」；Frederic 的概念分歧（nohz_full 上该不该有 dl-server）仍未闭环。

## 合入评估

*likelihood=medium*。方向获 Peter 认可、Ionut 变体有双机数据、今天的复现器又为 v3 划清了设计红线；但 v3 迟迟未发，且 ext_server 语义仍未澄清。*blocking_issues*：v3 未发出（需整合 Ionut 变体 + stop 路径收敛 + ext_server 处理；PINNED 已剔除）；running_bw 下溢本身（如果确为通用 bug 而非仅变体触发）是否需要独立修复未定。*next_action*：Juri 发 v3（吸收 Ionut RFC 的分层思路），或 Ionut 的 RFC 直接演进为 v3 基底。

## 效果评估

今天新增的是正确性证据而非性能数据：15 splats/4min（双 WARN 位点、双触发路径）证明 stop-at-enqueue-rate 会下溢 `running_bw`。既有性能数据（09-24，Ionut 双机）：Machine A vanilla/Juri v2/Ionut 变体带宽均约 5.10%，tick 66.0/1001.6/54.1 每/s；Machine B 7.90%（超标）/5.10%/5.09%，tick 0.9/1000.6/52.9 每/s。Ionut RFC 附新观测：默认（tick 因 SCHED 依赖不停）200 次 local_timer_entry/s vs fair_server 关闭时 ~19/s。

## 我可以参与的点

- `review`：v3/IONUT RFC review 时核对 `inc_dl_tasks()/dec_dl_tasks()` 新加 `sched_update_tick_dependency()` 的调用点锁序（rq 锁持有状态下调用是否安全）。
- `testing`：用 Ionut 的复现器负载（FIFO hog + CFS + perf/fork-exit churn）跑 Juri v2 原样——补上「v2 原样是否也触发」的空档，直接决定 v3 的修复范围是「收敛 stop 路径」还是「另修 running_bw 状态机」。
- `new_patch`：若 `running_bw` 下溢确认为独立通用 bug（stop 撞武装中的 inactive_timer），可先行单独发 `__sub_running_bw()` 防御或状态机修复补丁，不绑 v3 节奏。

## 参考链接

- Ionut 复现器 + splats: https://lore.kernel.org/all/20261005125013.324327-1-ionut.nechita@windriver.com/
- Frederic 回复（hrtimer 迁移性）: https://lore.kernel.org/all/asO1DctL9BydDNGV@localhost.localdomain/
- Peter 撤回 PINNED（10-02）: https://lore.kernel.org/all/20261002092058.GA409038@noisy.programming.kicks-ass.net/
- Peter 10-01 review: https://lore.kernel.org/all/20261001142735.GT2009045@noisy.programming.kicks-ass.net/
- v2 原始补丁: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/

---
id: sched-20261005-003
date: '2026-10-05'
subject: 'sched/deadline: Make dl-server nohz full aware'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>'
lore_url: 'https://lore.kernel.org/all/20261005125013.324327-1-ionut.nechita@windriver.com/'
authors:
  - 'Juri Lelli'
maintainers_involved:
  - 'Frederic Weisbecker'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>'
    date: '2026-05-13'
    summary: 'RT+CFS 共存时保持 tick 以保证 CFS 预留带宽'
    review_outcome: '10-05 Ionut 提交 stop 路径 running_bw 下溢的可靠复现器（15 splats/4min）；Frederic 注脚 hrtimer 迁移性'
related_articles:
  - sched-20260925-013
  - sched-20261001-002
  - sched-20261002-003
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 'v3 未发出；stop 路径需收敛；ext_server 语义未澄清'
  next_action: 'Juri 发 v3 或 Ionut RFC 演进为 v3 基底'
generated_at: '2026-10-06T01:00:00'
---
