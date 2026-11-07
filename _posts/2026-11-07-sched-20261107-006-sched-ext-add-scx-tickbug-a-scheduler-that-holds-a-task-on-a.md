---
id: sched-20261107-006
date: '2026-11-07'
subject: 'sched_ext: Add scx_tickbug, a scheduler that holds a task on an idle CPU'
subsystem: sched
type: feature
status: superseded
severity: none
thread_root_msgid: <20261105200205.1178097-2-radu.m.toader@gmail.com>
lore_url: https://lore.kernel.org/all/au4HhnJoKvJ6GPJT@slm.duckdns.org/
authors:
- Radu Toader
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261105200205.1178097-2-radu.m.toader@gmail.com>
  date: '2026-11-06'
  summary: 新增 scx_tickbug 测试调度器，可控时长持有 idle-loop-带任务状态
  review_outcome: Tejun 认为一次性调试代码不宜进树；作者决定从 v2 移除，保留一行修复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 示例调度器被维护者否决进树
  - selftest 回归护栏是否值得做待社区确认
  next_action: 作者单独发一行修复；如被需要再发 selftest 回归护栏
contribution_opportunities:
- kind: testing
  description: 用归档的 scx_tickbug 实测 tick_irq_exit idle gate 影响，产出数据回帖
- kind: discussion
  description: 参与是否值得为这一状态加 nohz_tick 风格 selftest 的讨论
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261106-016
tags:
- sched_ext
- idle
title: 'sched_ext: Add scx_tickbug, a scheduler that holds a task on an idle CPU'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-016-sched-ext-add-scx-tickbug-a-scheduler-that-holds-a-task-on-a.html">sched-20261106-016</a>：Radu Toader 为 sched_ext 新增测试用调度器 `scx_tickbug`（tools/sched_ext，系列 1/2）：让一个任务在「runqueue 非空、CPU 在 idle loop」状态下保持可控时长，从而可测量 `tick_irq_exit()` 里 idle gate 在中断落入该状态时跳过 idle-time 记账的影响（sched_clock 失同步、下一次 tick 把整段 idle 时长记到任务头上）。纯工具、非策略。当日无评审。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-006-sched-ext-add-scx-tickbug-a-scheduler-that-holds-a-task-on-a.html">sched-20261107-006</a>（今天）：**Tejun Heo 表态「这类一次性调试代码我不确定想把它留在树里，也许放 github gist、从 fix 补丁里指过去」**。Radu Toader 接受并从 v2 里移除该调度器（v2 只保留一行修复），同时提出「可改为 nohz_tick 风格的 selftest 作为回归护栏」、并把 CI 发现的复现器自身 bug（pinned 任务饿死直至 sched_ext watchdog 卸载调度器）记录在案供后人参考。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-016-sched-ext-add-scx-tickbug-a-scheduler-that-holds-a-task-on-a.html">sched-20261106-016</a>）`enqueue_task_scx()` 先抬高 `rq->nr_running` 再调 `ops.enqueue()`，一个把任务 stash 到 map、不给 CPU 可 pick 之物的调度器会让任务保持 runnable 且计在该 CPU 上——CPU 进 idle loop 又不空，`idle_cpu()` false 而 `is_idle_task(current)` true，`tick_irq_exit()` 的 gate 因而跳过 `tick_nohz_irq_exit()` 与 `sched_clock_idle_wakeup_event()`。作者想测量这一 gate 的行为，但没有现成工具能长时间持有该状态。

今日转折是「这个工具该不该进树」的取舍：Tejun 认为它是一次性调试代码，不适合作为 tools/sched_ext 的常驻示例调度器。

## 技术方案

（承接）`scx_tickbug` 本身的设计未变（`is_tagged()` 任务进 `hold_q`、刻意不 kick、per-CPU kthread 走本地 DSQ 带抢占、释放定时器只在实际持有时 kick）。今日的关键结论：

- **作为示例调度器被移除**：v2 只保留一行修复。工具改由 v1 归档链接供后人取用（`https://lore.kernel.org/lkml/20261106094343.174905-2-radu.m.toader@gmail.com/`），不加任何第三方托管依赖。
- **CI 发现的复现器自身 bug**：`tickbug_enqueue()` 只把 `PF_KTHREAD && nr_cpus_allowed == 1` 的任务路由到本地 DSQ，用 taskset 固定的用户任务会落到 SHARED_DSQ；`task_allowed_on_cpu()` 阻止其它 CPU 取走它，而 `tickbug_dispatch()` 在 `nr_held_now` 非零时不回迁 SHARED_DSQ——固定到目标 CPU 的任务会被饿死直到 5s watchdog 卸载调度器。修复思路：凡 `nr_cpus_allowed == 1` 一律派发到本地 DSQ（作者已在 v2 采用）。
- **selftest 提议**：`tools/testing/selftests/sched_ext` 已有 nohz_tick（断言有限 slice EXT 任务在 NOHZ_FULL CPU 空闲后重启调度 tick），本调度器持有的状态可作为回归护栏断言进 selftest 而非示例调度器目录；作者愿单独发，等社区确认是否需要。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出，patch 1/2）→ 从 v2 移除*。今日 Tejun 表态后，作者决定 v2 只保留一行修复，scx_tickbug 示例调度器不再随系列携带。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：「Thanks for catching the bug. However, this scheduler is more of an one-off debug code and I'm not sure we want to carry this in tree. Maybe put it in a github gist or sth and point to it from the fix patch?」——不否定发现的 bug 价值，但不接受调试工具进树。
- **bot+bpf-ci**：AI 评审给出三点「task 固定到目标 CPU 可能饿死直到 watchdog 卸载」「调试调度器是否该进树存疑」「README 时态与可睡眠注释 nit」。
- **Radu Toader**（作者）：接受移除，指出饿死是真实 bug 非理论；愿意把状态断言改造成 selftest 单独提交。

无对抗，方向「工具转 selftest / 归档、只留修复」是共识结果。

## 合入评估

*likelihood=low*。scx_tickbug 作为示例调度器已确定不进树（status 记为 superseded）。修复本身（v2 一行修复，方向另见相关补丁）与可能的 selftest 是后续独立路径。*blocking_issues*：① 示例调度器被维护者否决进树；② selftest 是否值得做待社区确认。*next_action*：作者按约定单独发一行修复；如被需要再发 selftest 回归护栏。

## 效果评估

无量化性能数据。工具本身是测量装置；其「效果假设」（idle gate 跳过后 sched_clock 失同步、整段 idle 时长记到下一任务头上）仍无实测数字回帖。CI 评审确认其复现器存在真实饿死 bug。

## 我可以参与的点

- **testing**：若对 `tick_irq_exit()` idle gate 的影响有兴趣，可用归档的 scx_tickbug（v1 链接）在不稳定 sched_clock 系统上实测 exec_start 陈旧/整段 idle 记账的影响，产出数据——这正是该工具原本想推动的测量。
- **review/discussion**：就「是否值得为这一状态加 nohz_tick 风格 selftest 回归护栏」参与讨论，帮助作者判断有无必要单独提交。

## 参考链接

- lore thread（Tejun 回复）: https://lore.kernel.org/all/au4HhnJoKvJ6GPJT@slm.duckdns.org/
- lore thread（作者 v2 说明）: https://lore.kernel.org/all/20261107021509.968928-1-radu.m.toader@gmail.com/
- v1 归档（作者指回的固定链接）: https://lore.kernel.org/lkml/20261106094343.174905-2-radu.m.toader@gmail.com/
