---
id: sched-20261012-015
date: '2026-10-12'
subject: 'sched/fair: Add force push task mechanism for fair'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v2
patch_series:
- version: v2
  msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
  date: '2026-10-02'
  summary: 10/18 v2 force push 机制（put_prev 与 tick 上的 push，用于 misfit/EAS/cache-aware）
  review_outcome: Kayra 质疑 tick-push 是否死代码，Vincent 澄清为通用机制预留
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Kayra 对 tick-push 路径实际是否生效的疑问已澄清但需再核对
  - 系列整体未收敛
  next_action: 继续逐片 review，等待系列新版
contribution_opportunities:
- kind: review
  description: 核对 tick_pushable_task() 里 nr_running>1 早退后，check_pushable_short_task
    的 h_nr_runnable<=1 判断是否真的恒 false（Kayra 之疑）
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles:
- sched-20261010-001
tags:
- load_balance
- cfs
title: 'sched/fair: Add force push task mechanism for fair'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-001-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261010-001</a>（及 20261009-004）：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 机制（07/18），其中 10/18 是「force push」变体。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-015-sched-fair-add-force-push-task-mechanism-for-fair.html">sched-20261012-015</a>（今天）：Kayra 质疑 10/18 v2 的 tick-push 路径像是「有意不生效」——`tick_pushable_task()` 先 `if (rq->nr_running > 1) return false`，后面对 `fair_check_pushable_task(next=NULL)` 只剩 `check_pushable_short_task()` 能返回 true，而它又要求 `h_nr_runnable <= 1` 才能返回 false（即永远到不了 true）；Vincent 澄清 push 机制是通用件（put_prev 上的 push + tick 上的 push），短 slice 任务独自在 CPU 上没必要 tick-push，tick-push 留给 misfit/EAS/cache-aware 等未来用例。

## 背景与问题

（承接 20261010-001）force push 是 push 机制的增强：在 put_prev 与 tick 两个时机把「该被推走」的任务强制推走，服务于 misfit、EAS、cache-aware 等后续场景。

## 技术方案

（承接 20261010-001）今日澄清：push 机制通用部分含「put_prev 上的 push」与「tick 上的 push」；对短 slice 任务不用 tick-push（独自占 CPU 的短 slice 任务没理由被推），tick-push 预留给 misfit/EAS/cache-aware（这些不在本补丁里）。

## 版本演进与当前进展

v2（10-02）→ 今日（10-12）Kayra 提问、Vincent 澄清；Kayra 回「Thanks for clarifying!」，疑点解除。

## Maintainer 意见与讨论焦点

Kayra Cizmeci 指出 tick-push 路径在 `nr_running<=1` 且 `next=NULL` 约束下 `fair_check_pushable_task()` 几乎恒 false（疑死代码）；Vincent 解释这是为未来 misfit/EAS/cache-aware 预留的通用件、当前短 slice 场景本就不走 tick-push。无 NAK。

## 合入评估

*likelihood=medium*。疑点已澄清，但属 18 补丁大系列、逐片 review 未完。*blocking_issues*：系列未收敛。*next_action*：继续 review，等系列新版。

## 效果评估

无 benchmark 数字（今日为机制澄清，未见数据）。

## 我可以参与的点

- `review`：严格走一遍 `tick_pushable_task()`→`fair_check_pushable_task()`→`check_pushable_short_task()` 的约束链，确认 tick-push 在「misfit/EAS/cache-aware 接入后」能真正触发。

## 参考链接

- lore（Kayra 质疑）: https://lore.kernel.org/all/20261011174038.5334-1-kayracizmeci@gmail.com/
- lore（Vincent 澄清）: https://lore.kernel.org/all/CAKfTPtBDcfk+TEEjD07RBLpCAusKqa0K4AWuFrcCtdw9uGsXCQ@mail.gmail.com/
