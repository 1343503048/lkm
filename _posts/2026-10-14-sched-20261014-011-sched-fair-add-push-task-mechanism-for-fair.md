---
id: sched-20261014-011
subject: 'sched/fair: Add push task mechanism for fair'
date: 2026-10-14
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v2
patch_series:
- version: v2
  msgid: <20261002154415.2270586-8-vincent.guittot@linaro.org>
  date: 2026-10-02
  summary: 07/18 引入 fair push 任务机制
  review_outcome: Shrikanth 追问实现细节，Vincent 逐条澄清，v3 待落
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 未发出
  next_action: Chen Yu/Vincent 落地 v3，继续整体系列 review
contribution_opportunities:
- kind: review
  description: 跟进 v3 pushable 检查 best-effort 边界与高频调用开销
- kind: discussion
  description: 讨论 cache-aware 走 wakeup vs push 的 task bouncing 问题
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261010-001
- sched-20261012-014
- sched-20261013-013
tags:
- cfs
- load_balance
title: 'sched/fair: Add push task mechanism for fair'
layout: article
---

> **subject**：sched/fair: Add push task mechanism for fair

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-004-improving-latency-of-short-slice-tasks.html">sched-20261009-004</a> / 20261010-001：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 任务机制（把排不上本 CPU 或不该在本 CPU 的任务推到更合适 CPU），短 slice 任务是首个使用者。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-014-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261012-014</a>：Shrikanth Hegde 对 07/18 提 review；Vincent 澄清「wakeup 与 push 共用同一 select 函数」，强调 `fair_check_pushable_task` 与 `select_task_rq_fair` 职责分离。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-013-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261013-013</a>：Chen Yu 确认理解并准备把 pushable 检查瘦身、选核下沉到 `select_task_rq_fair()`。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-011-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261014-011</a>（今天）：Vincent 逐条回答 Shrikanth（IBM）对 07/18 的技术追问——`fair_check_pushable_task` 会被高频调用、static key 已先行测试、语义沿用 RT/deadline、`rq`/`new_rq` 命名用意等，review 继续在补丁细节层推进。

## 背景与问题
（承接 20261010-001/20261012-014）短 slice 任务在 EEVDF 下仍有时延来源，CFS 缺类似 RT 的 push 机制；系列引入默认关闭、由使用者触发的 `sched_push_task` 静态分支，设计要点是 `fair_check_pushable_task()`（轻量是否深入）与 `select_task_rq_fair()`（选目标 CPU）两段职责分离。今日为 07/18 补丁 review 的细节问答。

## 技术方案
（承接 20261013-013）今日无新代码，为 Vincent 对 Shrikanth 追问的逐条澄清：

- `fair_check_pushable_task` 会被相当高频调用（「can be called quite often」）。
- static key 在调用前已测过，无需在函数内重复检查。
- push 语义沿用 RT/deadline 的既有做法。
- 跳过 current 任务、继续处理下一个（「Yes, we skip the current task and continue with the next one」）。
- 澄清一个变量命名疑问：`rq` 在 `fair_push_task()` 里保持不变，用 `rq` 与 `new_rq` 区分「当前 rq」与「目标 rq」。

## 版本演进与当前进展
仍为 v2（18 补丁系列），无新版本；今日是 07/18 补丁 review 的细节问答，Chen Yu 前日认领的「pushable 检查瘦身」仍待落地 v3。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（维护者/作者）：逐条回应 Shrikanth 的技术问题，坚持 RT/deadline 式 push 语义与 `fair_check_pushable_task`/`select_task_rq_fair` 职责分离。
- **Shrikanth Hegde**（reviewer）：前日对 07/18 提多处 review，今日继续追问实现细节。
- **Chen Yu**（前日）：认领将 pushable 检查瘦身。
- 无 NAK；review 推进到「高频调用成本、static key 测试时机、变量命名」等实现级细节。

## 合入评估
*likelihood=medium*。18 补丁整体仍处 v2 修订，v3 未发出；但 review 意见正被逐条认领与澄清，无方向性分歧。*blocking_issues*：v3 未发出。*next_action*：Chen Yu/Vincent 落地 v3（pushable 检查瘦身），继续整体系列 review。

## 效果评估
暂无新增数据；本轮为 review 细节问答，无 benchmark。

## 我可以参与的点
- review：跟进 v3 中 `fair_check_pushable_task` 的瘦身是否守住「不持 pi_lock 的 best-effort」边界，以及高频调用路径的开销是否被 static key 前置充分吸收。
- discussion：讨论 cache-aware 作为 push 使用者的迁移路径（wakeup vs push）是否如 Chen Yu 所述存在 task bouncing。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- 07/18 补丁 lore：https://lore.kernel.org/all/20261002154415.2270586-8-vincent.guittot@linaro.org/
