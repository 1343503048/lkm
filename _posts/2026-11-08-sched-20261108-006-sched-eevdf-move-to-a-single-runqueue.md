---
id: sched-20261108-006
date: '2026-11-08'
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/62ef3ad4ef9e32c6ce997c6c2ac3480ecd77ddd8.camel@gmx.de/
authors:
- Chengfeng Lin
maintainers_involved:
- Vincent Guittot
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - DELAY_DEQUEUE/DELAY_ZERO 记账语义未收敛
  - Mike 的 cache 热/冷 hack 未经 benchmark 验证
  next_action: 若 hack 实测兼顾短睡公平与负载均衡，可提炼为正式方案回帖
contribution_opportunities:
- kind: testing
  description: 在 627675b9c524 之上应用 Mike 的 cache 热/冷 hacklet，跑 schbench/wakeup-latency
    验证
- kind: review
  description: 评估以 sysctl_sched_migration_cost 判 cache 热冷并决定 wakelist 与否在 NUMA/异构平台的稳健性
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261107-003
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20261101-008</a>：Chengfeng Lin 的 v3 系列尝试把 EEVDF 收敛到单一 runqueue；窗口内讨论单 runqueue 下 DELAY_DEQUEUE 记账与跳过一次冗余 `update_curr_eevdf()`（15-worker -0.22%、2-worker +1.27%）。
- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-015-sched-eevdf-move-to-a-single-runqueue.html">sched-20261102-015</a>：作者与 Mike Galbraith 继续 benchmark 对话，澄清 Mike 观测的负面影响来自其 measurement 场景，作者愿意全范围重跑。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-015-sched-eevdf-move-to-a-single-runqueue.html">sched-20261103-015</a>：Tianchen Ding 报告 pipe 上下文切换回退、bisect 到 `333238da9a19`，建议 DELAY_ZERO 默认关；Chengfeng Lin 实测关闭 DELAY_ZERO 在 15-worker 场景 +13.7% 吞吐。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261107-003</a>：Vincent Guittot（sched/fair 维护者）贴长文为 `333238da9a19` 正名——证明该 commit 修复的是「delayed dequeued 任务 lag 记账错误」，并指出「关 DELAY_ZERO 只是回到过去的（同样不公平的）行为」。Mike Galbraith 肯定该 correctness 说明，并主动表示会去查「sleepers 在 tick 尺度存活作恶」的问题。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-006-sched-eevdf-move-to-a-single-runqueue.html">sched-20261108-006</a>（今天）：**Mike Galbraith 兑现承诺、拿出 Q/D hacklet**——用 `sysctl_sched_migration_cost` 作 cache 热/冷阈值，只把「仍 cache hot 的短睡 delayed 任务」走 wakelist/requeue 保留短互斥睡眠收益，把「cache cold 的长睡任务」放行迁移、回收负载均衡收益，避免被「长期不合格的睡眠者」拖累。代码 patch 挂在 Peter 的 ttwu 系列（`627675b9c524`）之上。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/01/sched-20261101-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20261101-008</a> / 20261102-015 / 20261103-015 / 20261107-003）单 runqueue 是 EEVDF 方向性重构，评审持续关注 DELAY_DEQUEUE 记账对负载均衡的影响。前日 Vincent 澄清 `333238da9a19` 的正确性之后，Mike Galbraith 在 11-07 末表示要查「sleepers 在 tick 尺度存活作恶」，今日给出首个具体方案：delayed dequeue 让一批「长期不合格的幸存者」sleepers 扎在本 runqueue，既吃不到迁移收益还拖累 balance。

## 技术方案

Mike 的 Q/D hacklet（相对 `627675b9c524`「sched: Add ttwu_queue support for delayed tasks」，改 `kernel/sched/core.c` 的 `ttwu_runnable()`）：以 `sysctl_sched_migration_cost` 为阈值，比较 `task_rq(p)->clock_task - p->se.exec_start` 判 cache 热/冷——

- **cache hot 的短睡 delayed 任务**：继续走 `ttwu_queue_wakelist()`（含 `WF_DELAYED`），保住 DELAY_DEQUEUE 最重要的「短 mutex 等睡眠」对重线程应用的公平竞争收益。
- **cache cold 的长睡任务**：不再 wakelist，改走正常 wakeup balancing 放行迁移，换取负载均衡收益。

代码中保留两处 `/* XXX */`（hack 性质明示），并留了「pinned sleeper 是否也该放行」的待决注释（`/* XXX pinned sleeper must go too if bug blocker is actually viable. */`）。属探索性原型，非正式补丁。

## 版本演进与当前进展

*current_version: v3（7 补丁系列，cover msgid 未获取到）*。今日无新版本，为 Mike Galbraith 对 DELAY_DEQUEUE 记账方向的探索性 hacklet。

## Maintainer 意见与讨论焦点

- **Mike Galbraith**：提出「只 requeue 明显更短期的 cache hot sleeper、放行长睡 cache cold sleeper」的折中，明确这是调试性（Q/D）hack、非提交候选，其中 pinned sleeper 的取舍尚待定。
- 维护者层面（Vincent Guittot、Peter/Ingo）今日未再表态；`333238da9a19` 的正名结论未被动摇。

无 NAK；方向仍属「DELAY_DEQUEUE/DELAY_ZERO 记账语义收敛中」。

## 合入评估

*likelihood=low*。单 runqueue 是调度器核心结构重构，DELAY_DEQUEUE 记账语义仍在争论；今日 Mike 的 hack 是探索而非正式补丁，未改变「尚无维护者认可整体方向」的格局。*next_action*：若 hack 在实测中证明可兼顾「短睡公平」与「负载均衡」，可提炼为正式方案回帖讨论。

## 效果评估

今日无量化数据。Mike 的 hack 未附 benchmark；此前 Chengfeng 的 +13.7%（关 DELAY_ZERO）与 Tianchen 的 pipe 回退数据仍是窗口内仅有的数字。

## 我可以参与的点

- **testing**：把 Mike 的 cache 热/冷 hacklet 应用在 `627675b9c524` 之上，跑 schbench/wakeup-latency/heavily-threaded 应用与长睡负载，验证「短睡保公平 + 长睡可迁移」是否两全。
- **review**：评估「以 `sysctl_sched_migration_cost` 判 cache 热冷并据此决定 wakelist 与否」的阈值在 NUMA/异构平台是否稳健。

## 参考链接

- lore thread（今日 Mike 回帖）: https://lore.kernel.org/all/62ef3ad4ef9e32c6ce997c6c2ac3480ecd77ddd8.camel@gmx.de/
- 基础 commit: 627675b9c524（"sched: Add ttwu_queue support for delayed tasks"）
- 相关 commit: 333238da9a19（"sched: Update time before requeueing delayed entities"）
