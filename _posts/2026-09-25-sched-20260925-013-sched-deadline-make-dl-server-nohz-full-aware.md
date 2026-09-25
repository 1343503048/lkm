---
id: sched-20260925-013
date: 2026-09-25
subject: 'sched/deadline: Make dl-server nohz full aware'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>
lore_url: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-26T01:15:00'
authors:
- Juri Lelli
- Ionut Nechita (Wind River)
maintainers_involved:
- Juri Lelli
patch_series:
- version: v2
  msgid: <20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>
  date: 2026-05-13
  summary: 让 dl-server 感知 nohz_full，在 RT+CFS 共存时保持 tick 以保证 CFS 预留带宽
  review_outcome: 长期未被收取；09-24 Ionut 实测发现其满 tick 代价、给出仅 server enqueue 期间保持 tick 的变体；09-25
    Juri 欢迎发 v3 并补齐 ext_server
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需要 Ionut 按变体发出正式 v3，并补齐 ext_server 处理
  - dl_servers_stop_all() 调用点的 hazard 需在 v3 中说明
  next_action: Ionut 发 v3（含 ext_server），Juri 复审后排队
contribution_opportunities:
- kind: testing
  description: 在自家 nohz_full + PREEMPT_RT 场景复现三变体对照，验证 dl_servers_stop_all hazard
    与 ext_server 分支
- kind: review
  description: 审读变体里 inc_dl_tasks/dec_dl_tasks 对 dl_server 分支加 sched_update_tick_dependency
    的锁序与幂等性
- kind: discussion
  description: Juri 抛出的「RT 应用是否该依赖 dl-server 做周期性 housekeeping」用法分歧可参与讨论
source_email_count: 2
related_articles: []
tags:
- deadline
- dl_server
- nohz
title: 'sched/deadline: Make dl-server nohz full aware'
layout: article
---

## TL;DR

Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月一直未被收取）今天重新活跃：Ionut Nechita（Wind River，RT 产品）在隔离的 nohz_full 核上追 timer 噪声时找到该补丁，发现它确实恢复了 CFS 带宽保证，但代价是让隔离核从「几乎停 tick」变成满 CONFIG_HZ 的 1001.6 tick/s，反而更贵；他给出一个「只在 server 实际 enqueue 期间才保持 tick」的变体（实测 tick 降到 54.1/s 而带宽不变）。Juri 回帖欢迎 Ionut 发 v3、把该思路并入，并解释了 deferred server 模型。

## 背景与问题

nohz_full 隔离核上，如果有一个 RT 任务（SCHED_FIFO）和一个 CFS 任务共存，dl-server 本应在 RT 任务占满 CPU 时保证 CFS 任务拿到其预留带宽（`fair_server` 默认 runtime 50ms / period 1s，即 5%）。但现状是：CFS 带宽的记账依赖 tick 调用 `update_curr_dl_se()`。在**安静的隔离核上 tick 会完全停止**，没有任何东西触发记账，于是 server 实际把 50ms 预留超额跑了约 58%（实测 7.90% CPU 而不是 5.00%），RT 任务丢掉的 CPU 比准入控制承诺的更多。正确的强制不应依赖环境 tick 活动。

## 技术方案

Juri 的 v2：在 `sched_can_stop_tick()` 里，当 `rt_nr_running && cfs.h_nr_queued` 时启动 fair_server 并因此不让 tick 停。这修复了带宽（5.10% 达标），但代价是隔离核 tick 永不停止（1001.6/s，即满 CONFIG_HZ），把 dl-server 的定时器换成了更贵的满速 tick。

Ionut 的变体（针对 v6.18.y 的 sketch，略去 ext_server）：只在 server **实际 enqueue**（即非 zero-laxity 等待、真正在 dl_rq 上服务）期间保持 tick——`sched_can_stop_tick()` 里先 `dl_server_start()`，仅当 `rq->dl.dl_nr_running` 因该启动而真正非零时才 `return false`；并在 `inc_dl_tasks()/dec_dl_tasks()` 里对 dl_server 分支补 `sched_update_tick_dependency()`，因为 server 跳过 `add_nr_running()/sub_nr_running()`、没人会在 enqueue/throttle 时重新评估 tick 依赖。实测 tick 降到 54.1/s（machine A）/ 52.9/s（machine B），带宽仍 5.09%~5.10%。Ionut 也提到他在等价的自家改动里遇到过 `dl_servers_stop_all()` 调用点的一个 hazard。

## 版本演进与当前进展

- v2（2026-05-13，`<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>`）：Juri 首发，此后一直未被收取。
- 09-24：Ionut 回帖，附双机实测 + 变体 sketch（msgid `<20260924170402.521623-1-ionut.nechita@windriver.com>`）。
- 09-25：Juri 回帖（`<araOR8aTAU_R5lwQ@jlelli-thinkpadt14gen4.remote.csb>`）欢迎 Ionut 发 v3，要求带上 ext_server 处理。

## Maintainer 意见与讨论焦点

- **Juri Lelli（SCHED_DEADLINE 维护者）认可方向**：「Keeping the tick stopped during the server's throttled window sounds reasonable」，并明确「v2 从未被收取，欢迎你带着你的方法发 v3」，要求 v3 一并带上 ext_server 处理以给出完整图景。
- **Juri 的语义澄清（关键分歧点）**：他把 Ionut 观察到的现象归因于 deferred server 模型——dl-server 主要是**防止 RT 下 CFS 完全饿死的安全网**，不是延迟保证；带宽正确（5%）才是重点，其在周期内如何分布是次要的。他反过来质疑：Ionut 那个「与 RT 应用同核的周期性 housekeeping CFS 任务依赖 dl-server 才能跑」的用法本身不安全，RT 应用应该主动 sleep、给 CFS housekeeping 留出运行空间，而不是靠 dl-server 兜底。这是一个「该不该依赖 dl-server 做实时 housekeeping」的用法分歧，不直接影响补丁是否合入。

## 合入评估

*likelihood=medium*。维护者已放行 v3 方向，但尚无 v3、且 ext_server 部分尚未补齐。*blocking_issues*：需要 Ionut 按变体发出正式 v3（含 ext_server 处理）；`dl_servers_stop_all()` 的 hazard 需在 v3 里说清。*next_action*：Ionut 发 v3，Juri 复审后排队。

## 效果评估

Ionut 提供了双机三变体对照（PREEMPT_RT、CONFIG_HZ=1000、fair_server 默认 50ms/1s）：

- Machine A（Dell R750, v7.2, 隔离 CPU 2）：vanilla CFS 带宽 5.10% / tick 66.0/s；Juri v2 5.10% / 1001.6/s；Ionut 变体 5.10% / 54.1/s。phase A（CFS 每 50ms 醒一次）tick 到期次数：vanilla 269/357、Juri v2 5022、变体 4。
- Machine B（Dell XR8620t, v6.18.y, 更安静核）：vanilla 7.90% / 0.9/s（带宽超标 58%）；Juri v2 5.10% / 1000.6/s；变体 5.09% / 52.9/s。

结论：变体用 ~54/s 的 tick 换取与 Juri v2 相同的带宽保证，把 tick 噪声降到接近 vanilla 水平。数据由作者自测，未见他方独立复核。

## 我可以参与的点

- `testing`：在自家的 nohz_full + PREEMPT_RT 场景复现三变体对照（尤其验证 `dl_servers_stop_all()` hazard 与 ext_server 分支），回帖补充数据。
- `review`：Ionut 的 sketch 里 `inc_dl_tasks/dec_dl_tasks` 加 `sched_update_tick_dependency()` 对 dl_server 分支的锁序与幂等性值得审读。
- `discussion`：Juri 抛出的「RT 应用是否该依赖 dl-server 做周期性 housekeeping」用法分歧，可作为讨论点参与。

## 参考链接

- Ionut 的实测 + 变体: https://lore.kernel.org/all/20260924170402.521623-1-ionut.nechita@windriver.com/
- Juri 的回帖（欢迎 v3）: https://lore.kernel.org/all/araOR8aTAU_R5lwQ@jlelli-thinkpadt14gen4.remote.csb/
- v2 原始补丁: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
