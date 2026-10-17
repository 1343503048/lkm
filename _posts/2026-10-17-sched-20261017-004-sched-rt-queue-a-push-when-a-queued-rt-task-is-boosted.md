---
id: sched-20261017-004
subject: 'sched/rt: queue a push when a queued RT task is boosted'
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261017121423.393837-1-chaosheng.qu.linux@gmail.com>
lore_url: https://lore.kernel.org/all/20261017121423.393837-1-chaosheng.qu.linux@gmail.com/
authors:
- Chaosheng Qu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261017121423.393837-1-chaosheng.qu.linux@gmail.com>
  date: 2026-10-17
  summary: prio_changed_rt() 在排队非 current RT 任务优先级提升且 overloaded 时 rt_queue_push_tasks()
  review_outcome: Kayra 要求整理 commit message（解释下移）并加 Suggested-by Steven Rostedt
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Kayra 的 commit message 组织与 Suggested-by 署名意见待 respin；是否 gate 到 PI boost 场景待定
  next_action: 作者按 Kayra 意见整理 commit message、加 Suggested-by，并回应 scope 问题
contribution_opportunities:
- kind: testing
  description: 在真实 pro-audio/livefx 与 PREEMPT_RT 配置上验证修复，补作者未覆盖盲区
- kind: review
  description: 就「是否仅 gate 到 PI boost 而非普通优先级变更」给出取舍意见
- kind: new_patch
  description: 按 Kayra 意见整理 commit message、补 Suggested-by，完成 respin
generated_at: '2026-10-18T01:16:00'
source_email_count: 2
related_articles:
- sched-20260903-006
- sched-20261015-001
tags:
- rt
- rt_bandwidth
- regression
title: 'sched/rt: queue a push when a queued RT task is boosted'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-006-regression-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost.html">sched-20260903-006</a>：Thorsten Leemhuis 催办——`dd29c017aed6` 引入的「非 PREEMPT_RT 下默认关 RT push IPI」导致 pro-audio 负载多秒级 PI-boost 饥饿，被列入回归清单但无修复补丁。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-001-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html">sched-20261015-001</a>：Chaosheng Qu 给出合成复现器；Steven Rostedt 确认是合法 bug，并指明修法——让 `prio_changed_rt()` 感知 rto mask、在 PI boost 时触发一次额外 RT 迁移分析（push）。方向已由维护者拍板，但尚无实现补丁。
- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-004-sched-rt-queue-a-push-when-a-queued-rt-task-is-boosted.html">sched-20261017-004</a>（今天）：Chaosheng Qu 发首版修复补丁——在 `prio_changed_rt()` 中，当排队中的非 current RT 任务优先级被提升且 `rq->rt.overloaded` 时 `rt_queue_push_tasks()`，push 从任务自身 cpus_mask 选目标（正是 pull 侧做不到的选择）。附带详尽的 kprobe 追踪与 A/B 数据。Kayra Cizmeci 回帖两条格式/署名意见。

## 背景与问题
（承接 20260903-006 → 20261015-001）PI 继承把低优先级持锁任务 boost 到高优先级、且它因本 CPU 被更高优先级 hog 占住无法运行时，存在一个「死亡窗口」：本 CPU 不能跑它（被 hog 占住），pull 侧够不到它（`task_is_pushable()` 要求刚 idle 的 CPU 在任务 cpus_mask 内，本场景不满足），push 侧又因 `NO_RT_PUSH_IPI` 从未被请求——任务卡到 hog 主动 schedule out。今天 Chaosheng 用 kprobes 把机制坐实：boost 时 `prio_changed_rt()` 只排队 pull、从不排队 push；pull 侧因 affinity 测试空手而归，于是非 PUSH 路径两边都错过该任务。

## 技术方案
（承接 20261015-001）首版修复补丁（`kernel/sched/rt.c`，+11），实现 Steven Rostedt 在 20261015-001 定下的方向：
- 在 `prio_changed_rt()` 中，保留原有 `if (p->prio < rq->donor->prio) resched_curr(rq);` 之外，新增：`if (p->prio < oldprio && rq->rt.overloaded) rt_queue_push_tasks(rq);`——当排队中的非 current RT 任务优先级被提升（`p->prio < oldprio`）且本 rq overloaded 时，请求一次 push。
- push 从任务自身 cpus_mask 经 `find_lowest_rq()` 选目标，这是 pull 侧（受 affinity 测试限制）做不到的选择。
- `rt_mutex_setprio()` 已在末尾 `__balance_callbacks()`，故 callback 在同一 rq->lock 段内、与既有 `rt_queue_pull_task()` 同路径执行。
- 无 boost 时没有合法目标、push 找不到任何东西，行为不变（对照实验证实）。

## 版本演进与当前进展
- 2026-08-14：Martin King 报告 + 早期修复尝试（rto 计数）。
- 2026-09-03：Thorsten 催办，无新补丁。
- 2026-10-15：Chaosheng 复现器 + Steven 定位根因、明确修法。
- 2026-10-17（今天）：Chaosheng 发首版实现补丁（v1，`<20261017121423.393837-1-chaosheng.qu.linux@gmail.com>`）；Kayra Cizmeci 回帖。

## Maintainer 意见与讨论焦点
- Steven Rostedt（前一日，方向拍板者）：「We need to make the prio_changed_rt() aware of the rto mask and trigger a push if needed.」
- Kayra Cizmeci（今日回帖，非维护者 reviewer）两条意见：① 那大段解释应放到 `---` 之下、不进 commit message；② 这既是 Steven 的建议，应加 `Suggested-by: Steven Rostedt`。
- 作者自留的开放点：`prio_changed_rt()` 也会被普通 `sched_setscheduler()` 优先级变更触达，会顺带为用户态优先级提升排队 push——作者未对该对称场景做 A/B，问是否要 gate 在 `pi_top_task` 上；PREEMPT_RT 组合因本树无 RT patchset 未测。

## 合入评估
*likelihood=high*。回归获维护者确认属实、修法明确，作者已按方向给出实现并附数据；今日 reviewer 意见仅为 commit message 组织与 `Suggested-by` 署名，非技术阻塞。*blocking_issues*：Kayra 的格式/署名意见待作者 respin；是否 gate 到 PI boost 场景待定。*next_action*：作者按 Kayra 意见整理 commit message、加 Suggested-by，并就 scope（是否仅 PI boost）回应。

## 效果评估
作者今日 A/B（同树、同配置、同 kprobe，仅补丁不同，dwell 1.5s、100ms「及时迁移」阈值）：
- OFF、mask {1,3}：修复前 1/17 及时、median 1498.5ms；修复后 13/13 及时、median 4.8ms（0.6–59.6）。
- 无 boost 对照：修复前 0/2 迁移、median 1498.2ms；修复后 0/3、median 1499.2ms（行为不变，符合预期）。
- ON（RT_PUSH_IPI）：修复前 3/3、median 3.06ms；修复后 5/5、median 0.72ms。
- 局限性：仅 KASAN+PROVE_LOCKING debug 配置、非 PREEMPT_RT、合成拓扑，未在 Martin 的 REAPER/livefx 真实负载上验证；PREEMPT_RT 未测。

## 我可以参与的点
- *testing*：在真实 RT/pro-audio（或 Martin 的 livefx/REAPER 负载）与 PREEMPT_RT 配置上复现并验证修复，补上作者未覆盖的盲区。
- *review*：审视「是否应 gate 在 PI boost（`pi_top_task`）而非覆盖普通优先级变更」这一 scope 问题，给出取舍意见。
- *new_patch*：按 Kayra 意见整理 commit message、补 `Suggested-by`，完成 respin。

## 参考链接
- 今日补丁：https://lore.kernel.org/all/20261017121423.393837-1-chaosheng.qu.linux@gmail.com/
- Kayra Cizmeci 的 review：https://lore.kernel.org/all/atOGI0tcyXnuWuD9@scheduler.schedules/
- 原始报告线程根：https://lore.kernel.org/all/CAEB5A_91hob8ddOhW=PrO1=O7GrFmSxY3r1-_Ard6x8KHHuJGA@mail.gmail.com/
- Steven Rostedt 的确认与修法：https://lore.kernel.org/all/20261015084615.05957ae3@gandalf.local.home/
