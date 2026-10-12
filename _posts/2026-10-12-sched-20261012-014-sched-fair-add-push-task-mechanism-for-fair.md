---
id: sched-20261012-014
date: '2026-10-12'
subject: 'sched/fair: Add push task mechanism for fair'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261002154415.2270586-8-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
- Shrikanth Hegde
current_version: v2
patch_series:
- version: v2
  msgid: <20261002154415.2270586-8-vincent.guittot@linaro.org>
  date: '2026-10-02'
  summary: 07/18 fair push 任务机制（把不该/排不上本 CPU 的任务推到更合适 CPU）
  review_outcome: Shrikanth 提出 static key/context_unsafe_alias/migration-disabled
    等 review 意见
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Shrikanth 的多点 review 意见待回应
  - 18 补丁系列整体仍在迭代
  next_action: Vincent 回应 Shrikanth（static key、context_unsafe_alias、migration-disabled
    路径）后发新版
contribution_opportunities:
- kind: review
  description: 核对 pushable 列表与 select_task_rq_fair 的职责拆分是否清晰（Vincent 强调的分离点）
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles:
- sched-20261010-001
tags:
- load_balance
- cfs
title: 'sched/fair: Add push task mechanism for fair'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-001-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261010-001</a>（及 20261009-004）：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 任务机制，把排不上本 CPU 或不该在本 CPU 的任务推到更合适 CPU。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-014-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261012-014</a>（今天）：Shrikanth Hegde 对 07/18 补丁提 review（是否该用 static key、需要 `context_unsafe_alias(rq)`、migration-disabled 任务不应进 pushable 列表、失败路径是否误返回 true 等）；Vincent 澄清「目标是 wakeup 与 push 事件共用同一 select 函数」，并强调 `fair_check_pushable_task` 与 `select_task_rq_fair` 的职责应分离。

## 背景与问题

（承接 20261010-001）短 slice 任务时延优化系列：EEVDF lag/slice 改进之外，新增「push 任务」机制，让任务能被主动推到更合适 CPU，而不是只依赖 wakeup 时选核。

## 技术方案

（承接 20261010-001）push 机制：`fair_check_pushable_task()` 判断任务是否值得深入决策，`select_task_rq_fair()` 选目标 CPU。今日 Vincent 澄清两个设计点：(1) 目标是让 wakeup 与 push 事件走同一 select 函数（同一事件）；(2) `fair_check_pushable_task` 里「是否加入 pushable 列表」的检查应与 `select_task_rq_fair` 里「是否选 pref_cpu」的决策分离——前者主要用来决定是否值得进入更深的 select 决策。

## 版本演进与当前进展

v2（10-02）→ 今日（10-12）Shrikanth review 07/18、Vincent 澄清设计；尚无新版。

## Maintainer 意见与讨论焦点

- **Shrikanth Hegde**：快速过了一遍 push 路径，提出 static key、`context_unsafe_alias(rq)`、migration-disabled 任务不应进 pushable 列表、列表遍历可读性、失败路径返回值等具体问题。
- **Vincent Guittot**：澄清 select 函数复用与职责分离，未逐条回绝。

## 合入评估

*likelihood=medium*。系列动机明确、维护者本人推动，但 18 补丁体量大、逐片 review 仍在进行。*blocking_issues*：Shrikanth 意见待回应、系列未收敛。*next_action*：Vincent 回应 review 并发系列新版。

## 效果评估

无新 benchmark 数字（今日为 review/澄清，未见数据）。

## 我可以参与的点

- `review`：核对 `fair_check_pushable_task` 与 `select_task_rq_fair` 的职责拆分、以及 migration-disabled 任务进入 pushable 列表的边界。

## 参考链接

- lore（Shrikanth review 07/18）: https://lore.kernel.org/all/a18e6fe1-e14e-46be-9779-3704ab8625a0@linux.ibm.com/
- lore（Vincent 澄清）: https://lore.kernel.org/all/CAKfTPtAy-n5_Dj-9x2qxcu=i7eo9DmZ2aaxig_nbyNDbP2m_Mw@mail.gmail.com/
