# sched/deadline: Make dl-server nohz full aware

> **subject**：`sched/deadline: Make dl-server nohz full aware`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260925-013：Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月未被收取）重新活跃——Ionut Nechita 发现 v2 恢复了 CFS 带宽保证但把隔离核变成满 CONFIG_HZ tick，给出「只在 server 实际 enqueue 期间保持 tick」的变体，Juri 欢迎其发 v3。
- sched-20261001-002：Frederic Weisbecker 提出根本性概念问题（nohz_full 上为什么会有 dl-server 在跑）；Juri 解释 fair 任务入队到正跑 FIFO 任务的核时 dl-server 兜底激活；Peter Zijlstra 给出具体 review——dl-server 定时器应加 `HRTIMER_MODE_PINNED`、`dl_server_stop_all()` 只放 true 分支，并称方向「more or less the best we can hope for」。
- sched-20261002-003（今天）：Peter 自我否决了 PINNED 建议——远程 enqueue 时可以在远端启动 dl-server，一旦 timer 被 PINNED 就落在「错误」的 CPU 上；正确的做法需要一个尚不存在的 `hrtime_start_on(timer, act, mode, rq->cpu)` 原语，而「Doing remote hrtimer_start isn't entirely trivial either. So scrap this for now :-(」。

## 背景与问题

（承接 sched-20260925-013）nohz_full 隔离核上 RT（SCHED_FIFO）与 CFS 任务共存时，dl-server 应在 RT 占满 CPU 的情况下保证 CFS 预留带宽（fair_server 默认 50ms/1s 即 5%）；但 CFS 带宽记账依赖 tick 调 `update_curr_dl_se()`，安静隔离核上 tick 完全停止导致记账缺位（实测带宽超标 58%）。Juri v2 用「保持 tick 不停」换带宽达标，代价满速 tick；Ionut 变体只在 server 实际 enqueue 期间保持 tick。今天无新背景，进展是 Peter 撤回了 10-01 的 PINNED 修改建议。

## 技术方案

（承接）Juri v2：`sched_can_stop_tick()` 里 `rt_nr_running && cfs.h_nr_queued` 时启动 fair_server 不让 tick 停；Ionut 变体：仅 server 实际 enqueue 期间保持 tick。

Peter 10-01 建议（已撤回）：`task_non_contending()`/`start_dl_timer()` 的 dl_server 分支追加 `HRTIMER_MODE_PINNED`。今天的撤回理由：PINNED 假设定时器与 dl-server 同核，但**远程 enqueue**（remote enqueue）可以在别的 CPU 上启动 dl-server，此后 timer 被钉死在启动时的 CPU（「wrong」CPU）上。正确解需要 `hrtime_start_on(timer, act, mode, rq->cpu)` 这类「在指定 CPU 上启动 hrtimer」的原语——当前内核没有；直接做远程 `hrtimer_start` 也不平凡。结论：「So scrap this for now :-(」——PINNED 从 v3 待办中移除，`dl_server_stop_all()` 位置与布尔化简建议不受影响。

## 版本演进与当前进展

- v2（2026-05-13，`<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>`）：Juri 首发，长期未被收取。
- 09-24/09-25：Ionut 实测 + 变体 sketch；Juri 欢迎 v3（sched-20260925-013）。
- 10-01：Frederic 概念提问 → Juri 解释 → Peter review（PINNED diff + stop_all 建议，「best we can hope for」）→ 布尔化简与 ext_server 交互讨论（sched-20261001-002）。
- 10-02（今天）：Peter（`<20261002092058.GA409038@noisy.programming.kicks-ass.net>`）回复自己 10-01 的邮件，撤回 PINNED 建议。v3 仍未发出。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：撤回 PINNED 建议，理由是远程 enqueue 下 PINNED 反而把定时器钉在错误 CPU；对补丁总体方向「best we can hope for」的态度未变。这体现了其对建议的自我审查——发现与远程启动路径冲突后主动收回。
- **Juri Lelli**（SCHED_DEADLINE 维护者）/ **Ionut Nechita**（Wind River）：当日未回帖。
- 焦点收敛后剩余：v3 需整合 Ionut 变体 + stop_all 位置建议；PINNED 移除后 dl-server 自身 timer 在 nohz_full 下被迁移的开销问题回到「暂不处理」状态；Frederic 的概念分歧（nohz_full 上该不该有 dl-server）仍未闭环但已被 Juri 的使用场景解释暂时压下。

## 合入评估

*likelihood=medium*。方向仍获 Peter 认可（撤回的只是其中一个技术细节），Ionut 变体有双机数据；但 v3 迟迟未发，且今日减少了一个待并入的修改项（未必是坏事——v3 复杂度下降）。*blocking_issues*：v3 未发出（需并入 Ionut 变体 + stop_all 建议，PINNED 已剔除）；ext_server 语义仍未澄清。*next_action*：Ionut/Juri 发 v3（不含 PINNED），Juri 复审后排队。

## 效果评估

本日无新 benchmark。既有数据（09-24，作者自测）：Machine A vanilla/Juri v2/Ionut 变体带宽均约 5.10%，tick 分别 66.0/1001.6/54.1 每/s；Machine B 7.90%（超标）/5.10%/5.09%，tick 0.9/1000.6/52.9 每/s。

## 我可以参与的点

- `review`：v3 发出后核对「PINNED 剔除 + stop_all 只放 true 分支」的组合是否引入新的定时器迁移开销，以及 Ionut 变体里 `inc_dl_tasks()/dec_dl_tasks()` 补 `sched_update_tick_dependency()` 的锁序。
- `discussion`：评估是否值得推动 `hrtime_start_on()` 原语（Peter 指出其缺失）——若社区有其它远程 hrtimer 需求可一并讨论，作为 dl-server 问题的长期解。

## 参考链接

- Peter 撤回 PINNED: https://lore.kernel.org/all/20261002092058.GA409038@noisy.programming.kicks-ass.net/
- Peter 10-01 的 PINNED 建议（被撤回）: https://lore.kernel.org/all/20261001142735.GT2009045@noisy.programming.kicks-ass.net/
- v2 原始补丁: https://lore.kernel.org/all/20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com/

---
id: sched-20261002-003
date: '2026-10-02'
subject: 'sched/deadline: Make dl-server nohz full aware'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>'
lore_url: 'https://lore.kernel.org/all/20261002092058.GA409038@noisy.programming.kicks-ass.net/'
authors:
  - 'Juri Lelli'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260513-upstream-fix-dlserver-nohzfull-b4-v2-1-d3e9cbe5c845@redhat.com>'
    date: '2026-05-13'
    summary: 'RT+CFS 共存时保持 tick 以保证 CFS 预留带宽'
    review_outcome: '10-01 Peter 深度 review 后，10-02 其撤回 PINNED 建议（远程 enqueue 下钉错 CPU）'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 未发出（并入 Ionut 变体 + stop_all 建议，PINNED 已剔除）'
    - 'ext_server 语义未澄清'
  next_action: 'Ionut/Juri 发 v3（不含 PINNED），Juri 复审后排队'
contribution_opportunities:
  - kind: review
    description: 'v3 后核对 PINNED 剔除+stop_all 组合的定时器迁移开销与 inc/dec_dl_tasks 锁序'
  - kind: discussion
    description: '评估推动 hrtime_start_on() 原语作为远程 hrtimer 启动的长期解'
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260925-013
  - sched-20261001-002
tags:
  - deadline
  - dl_server
  - nohz
---
