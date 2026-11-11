---
id: sched-20261111-009
date: '2026-11-11'
subject: 'sched/fair: Add push task mechanism for fair'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
  date: '2026-11-06'
  summary: 20 补丁改进短 slice 任务延迟：正 lag 衰减、选 CPU 考虑 slice、fair push 回调
  review_outcome: Peter 要求 08/20 限界并质疑 plist；K Prateek 补 DEQUEUE_CLASS 问题
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08/20 遍历限界与数据结构取舍待落定
  - 02/20 的 DEQUEUE_CLASS 覆盖待确认
  next_action: Vincent 按 Peter 建议改 08/20、回应 02/20 后发 v4
contribution_opportunities:
- kind: testing
  description: 在大量任务同时唤醒的压力场景验证 08/20 限界后的 push 疏散效果与遍历成本
- kind: review
  description: 复核 02/20 是否遗漏 DEQUEUE_CLASS 换类路径
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261106-002
- sched-20261107-004
- sched-20261109-002
- sched-20261110-010
tags:
- eevdf
- cfs
title: 'sched/fair: Add push task mechanism for fair'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>：Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）改进短 slice 任务调度延迟：正 lag 衰减、选 CPU 考虑 slice、fair 类新增 push 回调、feec() 按 cost+slice 选 CPU、修复多任务同时醒来堆叠同一 idle CPU。dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-004-improving-latency-of-short-slice-tasks.html">sched-20261107-004</a>：Kayra Cizmeci 评审 patch 02–06/20，对 03/04/05 给 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-002-improving-latency-of-short-slice-tasks.html">sched-20261109-002</a>：Peter Zijlstra 评审——08/20 质疑「为何新增列表 + plist」，02/20 判定「无 WRITE_ONCE 可行但 KCSAN 告警」，06/20 指出 `READ_ONCE` 应为 `rcu_dereference_all()`。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-010-improving-latency-of-short-slice-tasks.html">sched-20261110-010</a>：Vincent 逐条收口——02 补注释并实测 WRITE_ONCE 代价、06 顺带修 `set_idle_cores`、08 解释坚持独立小列表 + 复用 plist 的动机。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-009-sched-fair-add-push-task-mechanism-for-fair.html">sched-20261111-009</a>（今天）：**Peter 继续对 08/20 提出限界建议**——「最坏情况下大量任务被唤醒后全进这个列表，得全遍历一遍；要限界不如学 `detach_one_task()`，只考虑从尾部第一个合适的任务」；并明确「plist 对 RT 有意义，对 fair/DL 没意义（DL 用的是 RB 树），从尾部取一个就停」。K Prateek Nayak 对 02/20 追问「是否还要考虑 `DEQUEUE_CLASS`（任务换类离开 fair、rq 变 idle 的情况）」。Peter 对 02/20 的 WRITE_ONCE 补一句「它只是挡了编译器优化，这里本来就要 store，不影响」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a> / 20261107-004 / 20261109-002 / 20261110-010）短 slice 任务在 EEVDF 下因 slice 短、lag 反复累积而排不上队，多任务同时醒来堆叠同一 idle CPU；Vincent 的 v3 20 补丁用「正 lag 衰减 + 选 CPU 考虑 slice + fair 类 push 回调」解决。今日继续收尾评审：Peter 对 08/20 的 push 列表限界与数据结构选择给出方向性意见，K Prateek 对 02/20 补一个 DEQUEUE_CLASS 边角问题。

## 技术方案

今日无新代码，为评审收口，焦点在两个补丁：

- **08/20 `Add push task mechanism for fair`**：Peter 两条实质意见——(a) 最坏情况（大量任务被唤醒、全进 push 候选列表）需要遍历全部，建议仿 `detach_one_task()` 限界：只考虑「从尾部第一个合适」的任务，取一个就停。(b) 数据结构上，「plist 对 RT 有意义，对 fair/DL 没意义；DL 的 pushable 是用 RB 树维护的」，所以 fair 侧的 plist 复用站不住脚，应简化。
- **02/20 `Reset lag at wakeup when prev CPU has been idle`**：K Prateek 追加问题——是否还需覆盖 `DEQUEUE_CLASS`（`setscheduler` 换类时以 `DEQUEUE_SAVE` 把任务移出 fair、留下 idle rq）这一路径；Peter 对 WRITE_ONCE 补充「这里本来就要 store，WRITE_ONCE 只是挡掉了无关紧要的编译器优化，影响可忽略」。

## 版本演进与当前进展

*current_version: v3（2026-11-06，`<20261106151947.3991524-1-vincent.guittot@linaro.org>`）*。仍是 v3 评审阶段，Peter 的 08/20 限界建议与 02/20 的 DEQUEUE_CLASS 问题预计会在下一版体现，尚未发 v4。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched 维护者）**：持续指导——08/20 要限界（仿 `detach_one_task()` 只取尾部一个）并质疑 fair 侧用 plist 的必要性（「plist 对 RT 有意义，对 fair/DL 没有」）；02/20 的 WRITE_ONCE 顾虑被他自己定调为「影响可忽略」。
- **K Prateek Nayak（AMD）**：02/20 补一条 `DEQUEUE_CLASS` 覆盖缺口。
- 无 NAK。分歧集中在 08/20 的 push 候选数据结构（作者想复用 plist 保持列表小，Peter 认为 fair 用不到 plist 且应限界）。

## 合入评估

*likelihood=medium*。作者是 fair 维护者本身、系列方向无异议，但尚需按 Peter 的意见（限界 + 数据结构）再改一版，并回应 K Prateek 的 DEQUEUE_CLASS 问题。*blocking_issues*：08/20 的遍历限界与 plist 取舍待落定；02/20 的 DEQUEUE_CLASS 覆盖待确认。*next_action*：Vincent 按 Peter 建议改 08/20（限界 + 数据结构）、回应 02/20 的 DEQUEUE_CLASS，发 v4。

## 效果评估

无今日新增数据。系列此前数据（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>）：dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%。

## 我可以参与的点

- **testing**：在「大量任务同时唤醒」的压力场景验证 08/20 加限界后 push 是否仍能把任务及时疏散到空闲 CPU，并对比遍历成本。
- **review**：评估 02/20 是否遗漏 `DEQUEUE_CLASS`（换类导致 rq 变 idle）路径——K Prateek 提出的这条是具体可复核的点。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- Peter 对 08/20 的限界建议: https://lore.kernel.org/all/20261111090155.GF2668564@noisy.programming.kicks-ass.net/
- K Prateek 对 02/20 的问题: https://lore.kernel.org/all/f0bdf36b-4453-4d2f-b82c-85d1d62c5f78@amd.com/
