---
id: sched-20261015-016
date: 2026-10-15
subject: 'sched/fair: Add push task mechanism for fair'
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
- version: v1
  msgid: null
  date: null
  summary: 首次提出 fair push 任务机制
  review_outcome: 见 related 文章
- version: v2
  msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
  date: 2026-10-02
  summary: 18 补丁系列引入 sched_push_task 静态分支；07/18 为核心 push 机制
  review_outcome: 逐补丁 review 中；今日补锁注解问题
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 18 补丁规模大、逐补丁 review 未完；thread-safety 注解需补
  next_action: 为相关函数补 __acquires/__releases 注解，继续收齐剩余补丁 review
contribution_opportunities:
- kind: review
  description: 审阅 07/18 及后续补丁的锁语义与注解完整性
generated_at: '2026-10-16T01:05:00'
source_email_count: 2
related_articles:
- sched-20261009-004
- sched-20261010-001
- sched-20261012-014
- sched-20261013-013
- sched-20261014-011
tags:
- cfs
- eevdf
- load_balance
- perf
title: 'sched/fair: Add push task mechanism for fair'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-004-improving-latency-of-short-slice-tasks.html">sched-20261009-004</a> / 20261010-001：Vincent Guittot 的 18 补丁 v2「Improving latency of short slice tasks」系列引入 fair push 任务机制（把排不上/不该在本 CPU 的任务推到更合适 CPU），短 slice 任务是首个使用者。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-014-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261012-014</a>：Shrikanth Hegde 对 07/18 提 review；Vincent 澄清「wakeup 与 push 共用同一 select 函数」，强调 `fair_check_pushable_task` 与 `select_task_rq_fair` 职责分离。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-013-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261013-013</a>：Chen Yu 确认理解并准备把 pushable 检查瘦身、选核下沉到 `select_task_rq_fair()`。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-011-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261014-011</a>：Vincent 逐条回答 Shrikanth（IBM）对 07/18 的细节疑问（调用频率、static key、skip current、变量命名）。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-016-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261015-016</a>（今天）：Shrikanth 用 clang-23 线程安全分析报告 07/18 引入的 `raw_spinlock` 未持锁释放/路径未持锁警告；Vincent 回应两个函数应补 `__releases(__rq_lockp(rq))`/`__acquires(__rq_lockp(rq))` 注解。

## 背景与问题
（承接 20261009-004 → 20261014-011）短 slice 任务在 EEVDF 下仍有时延来源，CFS 缺类似 RT 的 push 机制；系列引入默认关闭、由使用者触发的 `sched_push_task` 静态分支，设计要点是 `fair_check_pushable_task()`（轻量是否深入）与 `select_task_rq_fair()`（选目标 CPU）两段职责分离。今日为 07/18 补丁的锁注解与线程安全分析问题。

## 技术方案
（承接 20261014-011）今日无功能代码变更，是 review 收尾：
- Shrikanth 用 `clang-23 -Werror=thread-safety-analysis` 对 `kernel/sched/fair.c` 构建，报出 07/18 相关路径 `raw_spin_rq_unlock(rq)`「释放了一个未持有的锁」、以及某些路径上「持锁不完整」的告警（`raw_spin_unlock(&next_task->pi_lock)`、`rq_unlock` 等）。
- Vincent 回应：两个函数需要补 `__releases(__rq_lockp(rq))` 与 `__acquires(__rq_lockp(rq))` 注解。

## 版本演进与当前进展
- v2（18 补丁）07/18 持续 review 中；今日新增 lockdep/clang 线程安全注解问题，待作者在下一版补注解。

## Maintainer 意见与讨论焦点
Vincent Guittot（作者兼维护者）认可补注解的建议；Shrikanth 提供的 clang 告警指向锁获取/释放的静态不变量标注缺失。无 NAK，属质量收尾。

## 合入评估
*likelihood=medium*。系列庞大（18 补丁）、仍在逐补丁 review；锁注解问题已定位但需合并到后续版本。*blocking_issues*：18 补丁规模大、逐补丁 review 未完；thread-safety 注解需补。*next_action*：作者在后续版本为相关函数补 `__acquires/__releases` 注解，继续收齐剩余补丁的 review。

## 效果评估
无新的量化数据。该系列面向「短 slice 任务时延」优化，此前版本未在今日讨论引入新基准。

## 我可以参与的点
- *review*：审阅 07/18 及后续补丁的锁语义与 `__acquires/__releases` 注解是否完整；核对 `fair_check_pushable_task` 与 `select_task_rq_fair` 的职责边界。

## 参考链接
- Vincent 的注解回应：https://lore.kernel.org/all/CAKfTPtAXCmf9oqy-BKYRR-cLHFQGcgOCVPwN6s=3x7hD5Xz=hg@mail.gmail.com/
- Shrikanth 的 clang 报告：https://lore.kernel.org/all/4976fcef-29ec-43fd-8655-32874720ee73@linux.ibm.com/
