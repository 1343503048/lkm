---
id: sched-20261018-007
date: 2026-10-18
subject: 'sched/rt: queue a push when a queued RT task is boosted'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <179229574717.42111.11570330900189006001@gmail.com>
lore_url: https://lore.kernel.org/all/179229574717.42111.11570330900189006001@gmail.com/
authors:
- Chaosheng Qu
maintainers_involved:
- Steven Rostedt
current_version: v2
patch_series:
- version: v1
  msgid: <179229495240.39966.14792426764563252817@gmail.com>
  date: 2026-10-17
  summary: 首版：prio_changed_rt() 里 overloaded 时 rt_queue_push_tasks()，push 从 cpus_mask
    选目标
  review_outcome: Kayra Cizmeci 提两条格式/署名意见
- version: v2
  msgid: <179229574717.42111.11570330900189006001@gmail.com>
  date: 2026-10-18
  summary: '加 Suggested-by: Steven Rostedt，长解释下移、changelog 精简，commit 04de902d6a4e'
  review_outcome: 暂无合入确认回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 无显式 Applied 回帖，是否进 tip/sched/urgent 未确认
  next_action: 等待 Steven Rostedt 确认合入或回合到 RT 相关分支
contribution_opportunities:
- kind: testing
  description: 非 PREEMPT_RT + RT_PUSH_IPI 关闭负载下复现 PI-boost 饥饿并验证修复
- kind: discussion
  description: 讨论 NO_RT_PUSH_IPI 默认关闭策略在 pro-audio 场景的合理性
generated_at: '2026-10-19T09:00:00'
source_email_count: 2
related_articles:
- sched-20261017-004
tags:
- rt
- preempt
- regression
title: 'sched/rt: queue a push when a queued RT task is boosted'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-006-regression-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost.html">sched-20260903-006</a>：Thorsten Leemhuis 催办——`dd29c017aed6` 引入的「非 PREEMPT_RT 下默认关 RT push IPI」导致 pro-audio 负载多秒级 PI-boost 饥饿，被列入回归清单但无修复补丁。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-001-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html">sched-20261015-001</a>：Chaosheng Qu 给出合成复现器；Steven Rostedt 确认是合法 bug，并指明修法——让 `prio_changed_rt()` 感知 rto mask、在 PI boost 时触发一次额外 RT 迁移分析（push）。方向已由维护者拍板，但尚无实现补丁。
- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-004-sched-rt-queue-a-push-when-a-queued-rt-task-is-boosted.html">sched-20261017-004</a>：Chaosheng Qu 发首版修复补丁——在 `prio_changed_rt()` 中，当排队中的非 current RT 任务优先级被提升且 `rq->rt.overloaded` 时 `rt_queue_push_tasks()`，push 从任务自身 cpus_mask 选目标。Kayra Cizmeci 回帖两条格式/署名意见。
- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-007-sched-rt-queue-a-push-when-a-queued-rt-task-is-boosted.html">sched-20261018-007</a>（今天）：Chaosheng 按 review 意见整理——加入 `Suggested-by: Steven Rostedt`、把长解释移到 `---` 之下、精简 changelog，给出更新后的 commit `04de902d6a4e`（基于 `1d08a07fd492`），重发最终版。暂无进一步的合入确认回帖。

## 背景与问题

（承接 20260903-006 → 20261015-001 → 20261017-004）PI 继承把低优先级持锁任务 boost 到高优先级、且它因本 CPU 被更高优先级 hog 占住无法运行时，存在「死亡窗口」：本 CPU 不能跑它（被 hog 占住），pull 侧够不到它（`task_is_pushable()` 要求刚 idle 的 CPU 在任务 cpus_mask 内，本场景不满足），push 侧又因 `NO_RT_PUSH_IPI` 从未被请求——任务卡到 hog 主动 schedule out。复现（作者）：四 vCPU 非 PREEMPT_RT guest，`RT_PUSH_IPI` 关闭，FIFO-10 任务持 PI mutex 被另一 CPU 上的 waiter 提升到 FIFO-90，同时一个 FIFO-99 hog 占住其 CPU，任务整个 1.5s 驻留期都卡在队列里；一个 FIFO-60 空闲任务在其 cpus_mask 内某 CPU 上却派不上用场。开 `RT_PUSH_IPI` 后同 setup 6ms 内恢复。

## 技术方案

（承接 20261017-004）首版修复补丁（`kernel/sched/rt.c`，+12）今天在 review 后定型：

- 在 `prio_changed_rt()` 中，当排队中的非 current RT 任务优先级被提升（`p->prio < oldprio`）、任务有多个 CPU 可选且 `rq->rt.overloaded` 时，`rt_queue_push_tasks(rq)`。
- push 从任务自身 cpus_mask 经 `find_lowest_rq()` 选目标——这是 pull 侧（受 affinity 测试限制）做不到的选择。
- `rt_mutex_setprio()` 已在末尾调 `__balance_callbacks()`，故 callback 与既有 `rt_queue_pull_task()` 在同一 rq->lock 段内执行。
- 无 boost 时 push 找不到合法目标，行为不变。

今天的变化是提交形态：加入 `Suggested-by: Steven Rostedt <rostedt@goodmis.org>`，把冗长的机制解释移到补丁 `---` 之下、changelog 精简为短说明，更新 commit 为 `04de902d6a4e8a6ce6471b97d73f869c5753dc61`（基于 `1d08a07fd492`）。

## 版本演进与当前进展

*current_version: v2*（重发/整理版）。

- v1（20261017-004）：首版 +11 行，Kayra Cizmeci 提两条格式/署名意见。
- v2（20261018-007，今天）：加 Suggested-by、精简 changelog、重发最终版。

## Maintainer 意见与讨论焦点

Steven Rostedt（scheduler 维护者）是本修复方向的定调者（见 20261015-001），今天的 `Suggested-by` 信用即源于此；Kayra Cizmeci 的格式/署名意见今日被落实（长解释下移、changelog 精简、补 Suggested-by）。无技术分歧。

## 合入评估

*likelihood=high*。方向由 Steven Rostedt 拍板、实现已成型并给出 commit `04de902d6a4e`（基于 `1d08a07fd492`），属典型「等维护者收取」形态。*blocking_issues*：当日缓存无显式「Applied to ...」回帖，是否已进 tip/sched/urgent 尚未确认。*next_action*：等待 Steven Rostedt 确认合入（或据此回合到 RT 相关分支）。

## 效果评估

作者给出 A/B 数据（沿用 20261017-004）：非 PREEMPT_RT 下开 `RT_PUSH_IPI` 6ms 内恢复 vs 关掉后 1.5s 驻留；kprobe 追踪坐实 boost 时 `prio_changed_rt()` 只排 pull、从不排 push。修复本身无新 benchmark，靠机制推理 + 对照实验支撑。

## 我可以参与的点

- `testing`：在非 PREEMPT_RT + `RT_PUSH_IPI` 关闭的 RT 负载下复现 PI-boost 饥饿，验证修复后 push 在 target CPU 空闲时及时迁移。
- `discussion`：`NO_RT_PUSH_IPI` 默认关闭这一背景策略本身是否合理（pro-audio 场景的多秒饥饿），可结合 RT 社区口径继续讨论。

## 参考链接

- 最终补丁：https://lore.kernel.org/all/179229574717.42111.11570330900189006001@gmail.com/
- 作者整理说明（commit 04de902d6a4e）：https://lore.kernel.org/all/179229495240.39966.14792426764563252817@gmail.com/
