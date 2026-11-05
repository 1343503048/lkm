# Revert "sched/rt: Substract number of tasks of throttled queues from rq->nr_running"

## TL;DR

Qais Yousef 的 `[PATCH RFC v5 0/4]`（sched/rt 节流记账清理）中 patch 3/4 为 revert「从被节流队列的 rq->nr_running 中减任务数」这一历史提交；今天是原作者 Kayra Cizmeci 与 Qais 就该 revert 及 `inc/dec_rt_tasks()` 实现是否等价展开的 RFC 讨论——目前双方仍在厘清 `rt_entity_is_task()` 与 `!group_rt_rq()` 的等价性，以及 `rt_queued`/`dequeue_top_rt_rq()` 是否真为死代码，尚未有维护者表态。

## 背景与问题

Qais Yousef 在 RFC 中想清理 sched/rt 的节流与 nr_running 记账逻辑，其中一个动作是 revert 掉「Substract number of tasks of throttled queues from rq->nr_running」这一历史改动（即把被节流队列的任务数从 runqueue 的 nr_running 中扣掉）。他在 cover letter 中坦言「不确定 inc/dec_rt_tasks() 的实现该怎么写」，发 RFC 正是为了寻求这段历史代码当初必须这样写的背景。

## 技术方案

Qais 提出的替代写法是：把 `inc_rt_tasks()`/`dec_rt_tasks()` 中对「是否 group rt_rq」的判断从 `!group_rt_rq(rt_se)` 换成 `rt_entity_is_task(rt_se)`：

```c
-       if (!group_rt_rq(rt_se)) {
+       if (rt_entity_is_task(rt_se)) {
                struct rq *rq = rq_of_rt_rq(rt_rq);
                add_nr_running(rq, 1);
```

Kayra 指出这两者语义等价（`rt_entity_is_task(rt_se)` 定义就是 `!(rt_se)->my_q`，而 `group_rt_rq()` 返回的正是 `rt_se->my_q`），因此该替换本身不改变行为。真正有分歧的是配套的 `rt_queued` 与 `dequeue_top_rt_rq()` 移除：Kayra 强调「dequeue_top_rt_rq() 并非死代码」——当把根 cgroup 的 `cpu.rt_runtime_us` 设为 950000 时，root throttle 路径会走到它，移除后 `pick_task_rt()` 里 `sched_rt_runnable()` 会错误返回 true 而不再返回 NULL。Kayra 据此倾向「也许干脆放弃 revert 更好」，但把决定权留给 Qais。

## 版本演进与当前进展

*current_version: v5（RFC，2026-11-03 发出）*。系列为 4 补丁 RFC（patch 3/4 即本 revert）。今日无新版本，仅两个来回：Qais 抛出 `rt_entity_is_task()` 替代方案征询意见，Kayra 回复等价性 + 指出 `dequeue_top_rt_rq()`/`rt_queued` 移除存在根 cgroup 节流场景下的真实问题。

## Maintainer 意见与讨论焦点

尚无调度维护者（Peter Zijlstra / Juri Lelli 等）在今日邮件中表态，讨论仅在作者（Qais Yousef）与原改动作者（Kayra Cizmeci）之间。核心分歧：Qais 想 revert 并简化，Kayra 提醒被 revert 的历史行为在根 cgroup 节流场景下是必须的、并非死代码，建议可能干脆放弃 revert。

## 合入评估

*likelihood=unknown*。这是 RFC（作者明言是来「找历史背景与实现建议」的），且核心分歧（是否 revert、`rt_queued` 移除是否安全）尚未解决，无维护者介入，无法判断合入走向。*blocking_issues*：① 根 cgroup 节流场景下 `dequeue_top_rt_rq()`/`rt_queued` 的作用需要澄清；② revert 的动机是否成立仍待论证。*next_action*：Qais 需要先厘清历史背景、确认自己是否仍要 revert，或改为与 Kayra 商定保留现状。

## 效果评估

暂无效果数据。讨论停留在代码语义与正确性层面，未涉及 benchmark 或复现数据。

## 我可以参与的点

- **discussion**：帮忙查证被 revert 提交的历史背景（git blame + lore），确认「从节流队列 nr_running 减任务数」当初是为了修什么 bug/回退行为，这正是 Qais 发 RFC 想找的。
- **testing**：在启用 `cpu.rt_runtime_us` 根 cgroup 节流的系统上验证 `rt_queued`/`dequeue_top_rt_rq()` 移除后的行为差异。

## 参考链接

- lore thread（patch 3/4 RFC v5）: https://lore.kernel.org/all/20261103005953.56271-4-qyousef@layalina.io/
- Qais 替代方案回复: https://lore.kernel.org/all/8401ef7a-de1a-4cb2-a3eb-be02a8436360@layalina.io/

---
id: sched-20261105-003
date: 2026-11-05
subject: 'Revert "sched/rt: Substract number of tasks of throttled queues from rq->nr_running"'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: "<20261103005953.56271-1-qyousef@layalina.io>"
lore_url: "https://lore.kernel.org/all/20261103005953.56271-4-qyousef@layalina.io/"
authors: [Qais Yousef]
maintainers_involved: []
current_version: v5
patch_series:
  - version: v5
    msgid: "<20261103005953.56271-4-qyousef@layalina.io>"
    date: 2026-11-03
    summary: "RFC v5 4 补丁：patch 3/4 revert 从节流队列 nr_running 减任务数，配套改 inc/dec_rt_tasks。"
    review_outcome: "Kayra 指出 rt_entity_is_task 等价，rt_queued/dequeue_top_rt_rq 移除在根 cgroup 节流场景不安全。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "根 cgroup 节流下 dequeue_top_rt_rq/rt_queued 移除会导致 pick_task_rt 误判 runnable"
    - "revert 动机与历史背景仍需澄清"
  next_action: "Qais 先厘清历史背景并决定是否继续 revert，或与 Kayra 商定保留现状"
contribution_opportunities:
  - kind: discussion
    description: "查证被 revert 提交的历史背景（为何要扣节流队列的 nr_running）"
  - kind: testing
    description: "在启用根 cgroup cpu.rt_runtime_us 的系统验证 rt_queued 移除后的行为"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [rt]
---