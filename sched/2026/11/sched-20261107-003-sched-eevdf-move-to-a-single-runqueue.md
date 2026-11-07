# sched/eevdf: Move to a single runqueue

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261101-008：Chengfeng Lin 的 v3 系列尝试把 EEVDF 收敛到单一 runqueue；窗口内讨论单 runqueue 下 DELAY_DEQUEUE 记账与跳过一次冗余 `update_curr_eevdf()`（15-worker -0.22%、2-worker +1.27%）。
- sched-20261102-015：作者与 Mike Galbraith 继续 benchmark 对话，澄清 Mike 观测的负面影响来自其 measurement 场景，作者愿意全范围重跑。
- sched-20261103-015：Tianchen Ding 报告 pipe 上下文切换回退、bisect 到 `333238da9a19`（"sched: Update time before requeueing delayed entities"），建议 DELAY_ZERO 默认关；Chengfeng Lin 实测关闭 DELAY_ZERO 在 15-worker 场景 +13.7% 吞吐。
- sched-20261107-003（今天）：Vincent Guittot（sched/fair 维护者）贴出长文为 `333238da9a19` 正名——用 TA/TB 双任务逐步推演证明该 commit 修复的是「delayed dequeued 任务 lag 记账错误」，并指出「关 DELAY_ZERO 只是回到过去的（同样不公平的）行为」。Mike Galbraith 肯定该 correctness 说明「比 changelog 更利于分辨正确性 vs 笔误」，并主动表示会去查「sleepers 在 tick 尺度存活作恶」的问题。

## 背景与问题

（承接 sched-20261101-008 / 20261102-015 / 20261103-015）单一 runqueue 是 EEVDF 方向性重构，目标是消除多核 per-CPU runqueue 的负载分布与迁移开销；评审持续关注对 DELAY_DEQUEUE 记账行为的影响。前日 Tianchen 报告 pipe 上下文切换回退并把锅指向 `333238da9a19`（"sched: Update time before requeueing delayed entities"），提议 DELAY_ZERO 默认关。

今日核心是 Vincent Guittot 对 `333238da9a19` 的正面辩护：该 commit 修复的正是「delayed dequeued 任务 lag 记账错误」——改动前，睡眠任务 TA 以负 lag delayed dequeue，醒来时 `update_entity_lag()` 先清 lag、再在 `wakeup_preempt_fair()` 里 `update_curr_fair()` 才把 curr TB 的上一个 tick 补记，导致 avg_vruntime 前移、TA 凭空获得最多半个 tick 的正 lag（截到 slice 上限），从而错误抢占 TB；改动后先 `update_curr()` 补记 TB 再算 TA 的 lag，TA 保持零/负 lag、不再抢占。Vincent 进一步点明：关 DELAY_ZERO 之所以「回到过去行为」，正是因为它不再重置 delayed dequeue 期间累积的正 lag——但这是「still unfair」。

## 技术方案

（承接）今日无新补丁，为回退机理的权威澄清。Vincent 的推演要点：

- 无 `333238da9a19`：TA 睡眠 delayed dequeue（负 lag -1us）→ TB 变 curr；tick 里 `update_curr()` 推进 TB vruntime 但未到 deadline 不 resched；TA 在下一 tick 前醒来，`enqueue_task_fair()→requeue_delayed_entity()→update_entity_lag()` 把 TA lag 清 0、TA vruntime == avg_vruntime == TB 在 tick N-1 的 vruntime；随后 `wakeup_preempt_fair()→update_curr_fair()` 补记 TB 本 tick，avg_vruntime 前移约半 tick，TA 反而获得约半 tick（≤5ms、被 slice 截断）的正 lag——TA 错误抢占 TB。
- 有 `333238da9a19`：`requeue_delayed_entity()` 里先 `update_curr()` 补记 TB，再 `update_entity_lag(TA)`，TA 醒来时 vruntime 对齐「当下」而非「tick N-1」，保持零/负 lag；若 TB 仍在 vprot 保护内则 TA 不抢占。
- 关 DELAY_ZERO：只是不再重置这个 delayed dequeue 累积的正 lag，等于退回改动前的（同样不公平的）行为，不是正确修复。

## 版本演进与当前进展

*current_version: v3（7 补丁系列，cover msgid 未获取到；今日仍 v3）*。今日 Vincent Guittot 与 Mike Galbraith 继续讨论，无新版本代码。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**（sched/fair 维护者）：为 `333238da9a19` 正名，逐 tick 推演证明「改动前 TA 会错误抢占 TB、改动后不会」，并断言关 DELAY_ZERO 是「still unfair」而非修复。这是对 Tianchen 回退报告的维护者级回应。
- **Mike Galbraith**：肯定该 correctness 说明「正确性优先于一切是罕见的速度障碍；changelog 无助于分辨正确性与笔误，这个（说明）可以」，并主动表示「尚未查过 sleepers 在 tick 尺度存活作恶，几乎肯定现在会去做，至少要看一眼那个也想被拉平的 bug」。

无 NAK，方向仍属「DELAY_DEQUEUE/DELAY_ZERO 记账语义收敛中」；Peter/Ingo 本窗口仍未表态。

## 合入评估

*likelihood=low*。单 runqueue 是调度器核心结构重构，DELAY_ZERO 记账语义仍在争论；今日虽有维护者澄清 `333238da9a19` 正确，但未改变「尚无维护者认可整体方向」的格局。*next_action*：在 Vincent 的澄清之上，就 DELAY_ZERO 默认关/回退修复给出更完整的论证与广泛负载数据。

## 效果评估

今日无新量化数据。Vincent 的推演是机理澄清而非 benchmark；此前 Chengfeng 的 +13.7%（关 DELAY_ZERO）与 Tianchen 的 pipe 回退数据仍是窗口内仅有的数字。

## 我可以参与的点

- testing：跟进 Mike Galbraith 提出的「sleepers 在 tick 尺度存活作恶」猜想，构造 delayed dequeue + 长睡眠任务在单 runqueue 下的复现，验证 `333238da9a19` 与 DELAY_ZERO on/off 的行为。
- review：评估 Vincent「关 DELAY_ZERO 只是退回不公平旧行为」的论断，与 Tianchen 的 DELAY_ZERO 默认关建议之间的取舍，给出是否应默认关的独立判断。

## 参考链接

- lore thread（今日 Vincent 回帖）: https://lore.kernel.org/all/CAKfTPtCJVBpZNm7bVUSQZ01Q-iStNZvdz6BiNw1NN9+7y0+=mA@mail.gmail.com/
- lore thread（今日 Mike 回帖）: https://lore.kernel.org/all/f2623ff14205adfb92518ef3b7aca053384f4cf7.camel@gmx.de/
- 相关 commit: 333238da9a19（"sched: Update time before requeueing delayed entities"）

---
id: sched-20261107-003
date: '2026-11-07'
subject: "sched/eevdf: Move to a single runqueue"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/CAKfTPtCJVBpZNm7bVUSQZ01Q-iStNZvdz6BiNw1NN9+7y0+=mA@mail.gmail.com/"
authors: [Chengfeng Lin]
maintainers_involved: [Vincent Guittot]
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "DELAY_ZERO 记账语义未收敛"
    - "需证明广泛负载下无回退"
  next_action: "基于 Vincent 的 333238da9a19 澄清，就 DELAY_ZERO 默认关给出更完整论证与数据"
contribution_opportunities:
  - kind: testing
    description: "复现 Mike 提出的 sleepers 在 tick 尺度存活作恶场景，验证 333238da9a19 与 DELAY_ZERO on/off"
  - kind: review
    description: "评估 Vincent 澄清与 Tianchen 的 DELAY_ZERO 默认关建议之间的取舍"
generated_at: "2026-11-08T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261101-008, sched-20261102-015, sched-20261103-015]
tags: [eevdf, cfs, regression]
---
