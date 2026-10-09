---
id: sched-20261001-002
date: '2026-10-01'
subject: 'sched/deadline: Make dl-server nohz full aware'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>
lore_url: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
authors:
- Juri Lelli
- Ionut Nechita
maintainers_involved:
- Juri Lelli
- Peter Zijlstra
- Frederic Weisbecker
current_version: v2
patch_series:
- version: v2
  msgid: <20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>
  date: '2026-05-13'
  summary: 让 dl-server 感知 nohz_full，RT+CFS 共存时保持 tick 以保证 CFS 预留带宽
  review_outcome: 09-24 Ionut 实测暴露满 tick 代价并给出变体；09-25 Juri 欢迎发 v3；10-01 Peter 给 PINNED/stop_all
    具体 diff、Frederic 提概念分歧、Juri 认可 diff
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 未发出（需并入 Ionut 变体与 Peter 的 PINNED/stop_all 建议）
  - ext_server 启动语义待澄清
  - Frederic 的 nohz_full 语义概念分歧未闭环
  next_action: 整合各方意见发 v3（含 ext_server），Peter/Juri 复审后排队
contribution_opportunities:
- kind: review
  description: 审读 PINNED diff 与 stop_all 只放 true 分支后的 timer 生命周期边界
- kind: testing
  description: nohz_full + PREEMPT_RT 三变体对照叠加 PINNED，量化 timer 迁移噪声下降
- kind: discussion
  description: 参与 Frederic 的 nohz_full vs dl-server 概念分歧讨论
generated_at: '2026-10-09T01:00:00'
source_email_count: 7
related_articles:
- sched-20260925-013
tags:
- deadline
- dl_server
- nohz
title: 'sched/deadline: Make dl-server nohz full aware'
layout: article
---

> **subject**：`sched/deadline: Make dl-server nohz full aware`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-013-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20260925-013</a>：Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月一直未被收取）重新活跃——Ionut Nechita（Wind River，RT 产品）发现 v2 确实恢复了 CFS 带宽保证，但把隔离核从「几乎停 tick」变成满 CONFIG_HZ 的 1001.6 tick/s，反而更贵；他给出「只在 server 实际 enqueue 期间才保持 tick」的变体（实测 tick 降到 54.1/s 而带宽不变），Juri 欢迎其发 v3 并解释了 deferred server 模型。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-002-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20261001-002</a>（今天）：讨论迎来三方深水区。Frederic Weisbecker 提出根本性问题（sched bandwidth 与 nohz_full 本不相容、隔离核上本不该有 dl-server 在跑）；Juri 解释 fair 任务入队到正跑 FIFO 任务的 nohz_full 核时 dl-server 会激活兜底；Peter Zijlstra 给出具体 review——dl-server 定时器应加 `HRTIMER_MODE_PINNED`（避免被 NOHZ_FULL 迁移机制搬走）、`dl_server_stop_all()` 只应放 true 分支，并称当前方向「more or less the best we can hope for」；Juri 对 diff 表示 OK，Peter 另提一处布尔化简、Juri 指出 ext_server 交互后 Peter 自嘲「需要休息」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-013-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20260925-013</a>）nohz_full 隔离核上 RT（SCHED_FIFO）与 CFS 任务共存时，dl-server 应在 RT 占满 CPU 的情况下保证 CFS 的预留带宽（fair_server 默认 50ms/1s 即 5%）；但 CFS 带宽记账依赖 tick 调用 `update_curr_dl_se()`，安静隔离核上 tick 完全停止导致记账缺位（实测带宽超标 58%）。Juri 的 v2 用「保持 tick 不停」换取带宽达标，代价是满速 tick 噪声；Ionut 的变体只在 server 实际 enqueue 期间保持 tick。今天的新分歧是概念层：Frederic 质疑 nohz_full 上为什么会有 dl-server 在跑——「in general sched bandwidth is incompatible with nohz_full. It's about a single task running so there shouldn't need to limit access to the CPU. And therefore there should be no dl_server running there, right?」Juri 回答：dl-server 在 fair 任务入队到当前正跑 FIFO 任务的 nohz_full 核时被激活（使该 fair 任务在 FIFO 不睡的情况下也有机会运行），这正是要修的场景。

## 技术方案

（承接）Juri v2：`sched_can_stop_tick()` 里当 `rt_nr_running && cfs.h_nr_queued` 时启动 fair_server 并因此不让 tick 停。Ionut 变体：只在 server 实际 enqueue（`rq->dl.dl_nr_running` 因启动而真正非零）期间保持 tick，并在 `inc_dl_tasks()/dec_dl_tasks()` 的 dl_server 分支补 `sched_update_tick_dependency()`。

今天 Peter 给出两处具体修改建议（附 diff）：

1. **dl-server 定时器加 PINNED**：`task_non_contending()`（`HRTIMER_MODE_REL_HARD`）与 `start_dl_timer()`（`HRTIMER_MODE_ABS_HARD`）中，仅对 dl_server 分支追加 `HRTIMER_MODE_PINNED`——普通 dl timer 是 ABS_HARD 且 !PINNED，NOHZ_FULL 机制会把它们搬来搬去毫无收益；dl-server 严格 per-CPU，PINNED 才对。
2. **`dl_server_stop_all()` 只放 true 分支**：既然 false 情形下没停 tick、没人会关心那些 timer，「I don't see why we would stop the dl-server in the false case」。
3. 另一封里指出 `sched_can_stop_tick()` 新代码里该布尔的用途可疑——两处 true 赋值大可直接 `return false`；且该路径已无 DL 任务（在上面被过滤）。

Peter 并表态：「Anyway, yes, I think this is more or less the best we can hope for. In the down-thread case where someone is running both FIFO and CFS tasks, they get to keep the pieces, since that is violating NOHZ_FULL premise anyway.」

## 版本演进与当前进展

- v2（2026-05-13，`<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>`）：Juri 首发，长期未被收取。
- 09-24/09-25：Ionut 实测 + 变体 sketch；Juri 欢迎 v3（见 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-013-sched-deadline-make-dl-server-nohz-full-aware.html">sched-20260925-013</a>）。
- 10-01：Frederic 根本性提问（`<ar5YqUCMbhZyjvtn@localhost.localdomain>`）→ Juri 解释 dl-server 激活条件（`<ar5k_SmqKTmYKJvh@jlelli-thinkpadt14gen4.remote.csb>`）→ Peter review（`<20261001142735.GT2009045@noisy.programming.kicks-ass.net>`，含 PINNED diff 与 stop_all 建议）→ Juri 认可「The below makes sense to me... OK.」并指出 Ionut 抱怨的正是 dl-server 有自己的 timer 时仍保持 tick 徒增 FIFO 扰动 → Peter 追问布尔化简（`<20261001143314.GK4121620@noisy.programming.kicks-ass.net>`）→ Juri 指出「我们不会启动 ext_server，即使 EXT 任务存在，只要 CFS 任务在场就 return false」（`<ar57h-DsEVtuZnVw@jlelli-thinkpadt14gen4.remote.csb>`）→ Peter「Ah, see, I need a break ;-) /me stomps off to brew tea...」。
- v3 尚未发出。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：给出 PINNED 定时器与 stop_all 位置的具体 diff；总体认可方向（「best we can hope for」）；同时坚持「同核跑 FIFO+CFS 本就违反 NOHZ_FULL 前提，后果自负」的立场。
- **Juri Lelli**（SCHED_DEADLINE 维护者）：对 Peter 的 diff 表态 OK；澄清 dl-server 激活语义；对布尔化简提醒 ext_server 交互（CFS 在场 return false 时 EXT 任务也不会启动 ext_server）。
- **Frederic Weisbecker**（nohz/tick 维护者）：质疑 nohz_full 上 dl-server 存在的合理性——这是「nohz_full 语义 vs dl-server 兜底」的概念分歧，Juri 的解释（FIFO 不睡时 fair 任务靠 dl-server 得到运行机会）暂时回答了它。
- 无 NAK；三方均在建设性收敛，但 v3 未出、ext_server 语义仍在打磨。

## 合入评估

*likelihood=medium*。相较 09-25（仅 Juri 放行 v3 方向），今天 Peter 深度介入并给出具体 diff、Juri 认可，方向收敛程度显著提高；但 v3 尚未发出，PINNED/stop_all/布尔化简/ext_server 交互需统一落地并复测数据。*blocking_issues*：v3 未发出（需并入 Ionut 变体 + Peter 的 PINNED 与 stop_all 建议）；ext_server 启动语义待澄清；Frederic 的概念分歧未闭环。*next_action*：Ionut/Juri 整合各方意见发 v3（含 ext_server），Peter/Juri 复审后排队。

## 效果评估

本日无新 benchmark。既有数据（09-24，作者自测）：Machine A vanilla/Juri v2/Ionut 变体的带宽均为 5.10% 左右，tick 分别 66.0/1001.6/54.1 每/s；Machine B 分别 7.90%（超标）/5.10%/5.09%，tick 0.9/1000.6/52.9 每/s。Peter 的 PINNED 建议针对的是 dl-server 自身 timer 被迁移的开销，尚无量化数据。

## 我可以参与的点

- `review`：审读 Peter 的 PINNED diff 与 `dl_server_stop_all()` 只放 true 分支后的生命周期边界（false 分支下 timer 未停是否真的无人关心）。
- `testing`：在 nohz_full + PREEMPT_RT 场景复现三变体对照并叠加 PINNED 修改，量化 dl-server timer 迁移消除后的噪声下降。
- `discussion`：Frederic 的「nohz_full 上该不该有 dl-server」概念分歧仍开放，可参与讨论边界语义。

## 参考链接

- Peter 的 review（含 diff）: https://lore.kernel.org/all/20261001142735.GT2009045@noisy.programming.kicks-ass.net/
- Peter 的追问: https://lore.kernel.org/all/20261001143314.GK4121620@noisy.programming.kicks-ass.net/
- Frederic 的提问: https://lore.kernel.org/all/ar5YqUCMbhZyjvtn@localhost.localdomain/
- Juri 的解释: https://lore.kernel.org/all/ar5k_SmqKTmYKJvh@jlelli-thinkpadt14gen4.remote.csb/
- Juri 认可 diff: https://lore.kernel.org/all/ar54JPCpCZTITK6B@jlelli-thinkpadt14gen4.remote.csb/
- v2 原始补丁: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/
