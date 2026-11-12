---
id: sched-20261112-011
date: '2026-11-12'
subject: 'sched: Remove sched_class::balance()'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261107115913.261163891@infradead.org>
lore_url: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
current_version: v2
patch_series:
- version: v2
  msgid: <20261107115913.261163891@infradead.org>
  date: '2026-11-07'
  summary: 重做 rq_clock/rq_lock 语义；修 pick_next_task 自重入与 core-sched balance；12/12 移除
    sched_class::balance
  review_outcome: Peter 给 DL wakeup_preempt vs dl_server 修复并被 Kayra 抓到崩溃；balance 语义仍讨论中
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - DL 修复的 dl_se->rq 崩溃待修正
  - RETRY_TASK 语义疑问待回应
  - clock 状态机待重构
  next_action: 采纳 resched_curr(rq) 修正、回应 RETRY_TASK、按两点模型重构 clock 后发 v3
contribution_opportunities:
- kind: testing
  description: 带 deadline server 负载验证 DL 修复无 dl_se->rq 崩溃且 DL 抢占正确重启 pick
- kind: review
  description: 复核 RETRY_TASK 是否应重做 balance（关系到移除 balance() 的核心论证）
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 8
related_articles:
- sched-20261107-001
- sched-20261108-005
- sched-20261109-007
- sched-20261111-005
tags:
- core_sched
- cfs
- deadline
- rt
title: 'sched: Remove sched_class::balance()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-001-sched-core-sched-fixes-and-balancing.html">sched-20261107-001</a>：Peter Zijlstra 发 v2 系列（12 补丁）整体重做 rq_clock/rq_lock 语义（Tejun 指出上一版 rq_clock 方向错了）。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-005-sched-core-sched-fixes-and-balancing.html">sched-20261108-005</a>：Kayra 评审 02/12 给 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-007-sched-core-sched-fixes-and-balancing.html">sched-20261109-007</a>：Kayra 发现 05/12 的 rq_clock_freeze 类型 bug。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-005-sched-core-sched-fixes-and-balancing.html">sched-20261111-005</a>：Tejun 密集评审发现多个 bug；12/12 移掉 `sched_class::balance()` 后暴露 DL `rq->next_class` 未被 dl_server 路径提升；Peter 现场给修复，Kayra 又指出该修复让 DL 任务不抢占 FAIR，Peter 承认「行不通」。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-011-sched-remove-sched-class-balance.html">sched-20261112-011</a>（今天）：**Peter 给出 `sched/deadline: Fix wakeup_preempt() vs dl_server` 正式修复**（dl_server 的 timer enqueue 不经过 `wakeup_preempt()`、不提升 `rq->next_class`）；**Kayra 实跑又发现该修复里 `dl_se->rq` 解引用崩溃**，经 `WARN_ON` 定位后改成 `resched_curr(rq)` 即正常工作（latency 13us vs base 12us）。K Prateek 对「balance 是否必要 / RETRY_TASK 语义」提出根本性疑问，Andrea Righi 从 sched_ext 角度确认「分离 balance 与 pick 可行，保留 `rq->next_class` 与 IMMED reenqueue 即可」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-001-sched-core-sched-fixes-and-balancing.html">sched-20261107-001</a> / 20261108-005 / 20261109-007 / 20261111-005）12/12 `Remove sched_class::balance()` 移除后暴露：`rq->next_class` 只被 `wakeup_preempt()` 提升，而 `dl_server_start()`/`dl_task_timer()`/`dl_server_timer()` 直接 `resched_curr()` 不经过它，导致 pick 失败后 balance 掉锁期间入队的 DL entity 无人注意、pick 不重启。昨日 Peter 的修复被 Kayra 实测定性为「DL 不抢占 FAIR」的坏修复，今日 Peter 换思路直接修 DL 侧。

## 技术方案

今日 Peter 给出独立修复 `sched/deadline: Fix wakeup_preempt() vs dl_server`（`Fixes: 704069649b5b "sched/core: Rework sched_class::wakeup_preempt() and rq_modified_*()"`，`Reported-by: Tejun Heo`）：Tejun 指出 dl_se 从 timer（尤其 dl_server）入队不经过 `wakeup_preempt()`、不会提升 `rq->next_class`，schedule() 中段这种入队可能不重启 pick 而跑去跑低优先级 entity。修复改 `enqueue_dl_entity()` 签名（显式传 rq）并在成功入队时置 `rq->next_class = &dl_sched_class`。Kayra 实跑发现其中 `resched_curr(dl_se->rq)` 解引用 `dl_se->rq`（此时为 NULL）崩溃，改为 `resched_curr(rq)` 后正常。

## 版本演进与当前进展

*current_version: v2（系列仍无 v3，以现场 diff 迭代）*。今日在 12/12 的修复上进一步演进：① 独立 DL 修复 diff（Fix wakeup_preempt vs dl_server）发出；② 该 diff 被 Kayra 实测抓到 `dl_se->rq` 崩溃并给出改为 `resched_curr(rq)` 的正确形式。rq_clock 状态机仍待按 Tejun「两点模型」重构。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（作者/维护者）**：对 K Prateek 的疑问确认「这里确实出现了一次不必要的 balance」，并指出 `wakeup_preempt_scx()` 已经做了该做的事（调 `scx_schedule_reenq_local()`）；05/12 上自责「grep 那天肯定坏了」（漏看 `rq_clock_start_loop_update()`）。
- **Tejun Heo**：04/12 上澄清 rq clock 失效机制的初衷（避免 session 后读到陈旧时钟，而非每次 lock drop 都取新时钟），并主张 scx 复用 core 的时钟状态机、不需自己的 valid 标志。
- **K Prateek Nayak（AMD）**：提出根本性疑问——若 wakeup 路径已对刚唤醒的 RT 任务做过 balance，为什么 RETRY_TASK 要再为旧 `rq->donor` 重做一次 balance；并回溯 `50653216e4f`/`67692435c41` 的历史语义。
- **Andrea Righi（sched_ext）**：确认 `ops.cpu_acquire()/cpu_release()` 已 deprecated，balance-to-pick 缺口正是废弃原因之一；sched_ext 侧不需要 cpu_release 通知，只要保留 `rq->next_class` 追踪与 IMMED reenqueue 检查即可分离 balance 与 pick。
- **Kayra Cizmeci**：实跑 Peter 的 DL 修复发现 `dl_se->rq` 崩溃，定位并验证改为 `resched_curr(rq)` 后正常。
- 无 NAK。焦点仍是 balance 语义是否可整体移除（K Prateek 的 RETRY_TASK 之问）与 DL 侧 next_class 维护的正确实现。

## 合入评估

*likelihood=medium*。作者与维护者协作密集、方向一致，DL 独立修复已成型但仍被 Kayra 抓到一处崩溃（作者尚未回应是否采纳 `resched_curr(rq)`），且 clock 状态机与 balance 语义的重构尚未收口。*blocking_issues*：DL 修复的 `dl_se->rq` 崩溃需修正（Kayra 已给正确形式）；K Prateek 的 RETRY_TASK 语义疑问需明确回应；clock 状态机待重构。*next_action*：Peter 采纳 `resched_curr(rq)` 修正、回应 RETRY_TASK 疑问并按两点模型重构 clock，出 v3。

## 效果评估

Kayra 给出 Peter 的 DL 修复实测：`WARN_ON_ONCE(!dl_se->rq)` 触发（崩溃），改为 `resched_curr(rq)` 后正常工作，latency 约 13us（base 约 12us，可视为相同）。均为正确性证据，无性能收益数据。

## 我可以参与的点

- **testing**：在带 deadline server 的负载上跑 Peter 的 DL 修复（含 `resched_curr(rq)` 修正），验证 timer 入队的 DL entity 能正确重启 pick、无 `dl_se->rq` 崩溃。
- **review**：复核 K Prateek 的 RETRY_TASK 语义疑问——唤醒路径已 balance 后 RETRY_TASK 是否还应重做 balance，这关系到 `sched_class::balance()` 能否被安全移除的核心论证。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
- Peter 的 DL 修复 diff: https://lore.kernel.org/all/20261111161522.GD1922751@noisy.programming.kicks-ass.net/
- Kayra 的崩溃报告与修正: https://lore.kernel.org/all/avSYpkVnyRKfaZIo@scheduler.schedules/
- K Prateek 的 RETRY_TASK 疑问: https://lore.kernel.org/all/56e1d372-c938-468a-950b-4f984ad6bde1@amd.com/
