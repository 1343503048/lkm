---
id: sched-20261118-003
date: '2026-11-18'
subject: 'sched: Fix DL server starvation under core scheduling'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261112161548.78189-1-sieberf@amazon.com>
lore_url: https://lore.kernel.org/all/20261112161548.78189-1-sieberf@amazon.com/
authors:
- Fernand Sieber
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261112161548.78189-1-sieberf@amazon.com>
  date: '2026-11-12'
  summary: 五补丁修 core-sched 下 DL server 饥饿 + 自测
  review_outcome: Peter 认可 3/5，要求 2/5 按折叠方案改
upstream_commit: null
fixes_commit: bd9bbc96e835
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 2/5 保存 dl_server 的时序脆弱需按 Peter 方案重构
  next_action: 作者按 Peter 对 2/5 的折叠替代方案出 v2
contribution_opportunities:
- kind: review
  description: 核对 Peter 折叠 diff 与作者原实现语义等价性及 rq->lock drop 窗口
- kind: testing
  description: 在真实 core scheduling 硬件跑 cs_dl_server_test 验证份额恢复
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261113-002
tags:
- deadline
- dl_server
- core_sched
- hyperthreading
title: 'sched: Fix DL server starvation under core scheduling'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-002-sched-fix-dl-server-starvation-under-core-scheduling.html">sched-20261113-002</a>：Fernand Sieber（Amazon）发五补丁修 core scheduling 下 DL server 饥饿——fair server（50ms/1s）应预留 5% CPU，实测只拿到 0.000%；两个机制共同出错（core-wide pick 对 `rq->dl_server` 交接错误 + deferred server 被误计 forced-idle 时间），单独修任一处份额仍在 ~0%。带自测与 5s 窗口数据（tip 10/10 失败 0.000%，全系列 31/31 通过 3.99-5.19%）。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-003-sched-fix-dl-server-starvation-under-core-scheduling.html">sched-20261118-003</a>（今天）：**Peter Zijlstra 评审 2/5 与 3/5**——对 3/5（把 DL server pick 按 deadline 排序）「不喜欢但别无他法，yes」；对 2/5（保留 sibling 的 DL server link）指出 `pick_task()` 会 drop rq->lock 的窗口里保存 `rq->dl_server` 很脆弱，给出把前两补丁折叠的替代实现。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-002-sched-fix-dl-server-starvation-under-core-scheduling.html">sched-20261113-002</a>）core scheduling 下 DL server 预留的 CPU 份额几乎拿不到（实测 0.000% 而非 5%），根因之一在 core-wide 选择对 `rq->dl_server` 的交接：把 stale link 传给 idle、fast path 丢失 sibling 的 link、且在 `p->dl_server` 置位前就排序。今日收口在「如何可靠保存/复位 sibling 的 DL server link」这个并发细节上。

## 技术方案

今日为评审日、无新版本，聚焦两个补丁：

- **3/5 `Rank DL server picks as deadline in the core-wide pick`**：Peter「I don't love this, but I don't see another way either, so yes」——接受该排序方式，虽不优雅但无替代。
- **2/5 `Keep a sibling's DL server link in the core-wide pick`**：Peter 指出脆弱点——`pick_task()` 之间会 drop rq->lock（例如 SMT1 的 newidle），此时才把 `rq_0->core_dl_server = rq_0->dl_server` 保存下来会与「在 `pick_next_task()` 里按需重取」的时序打架；给出把前两补丁折叠的替代 diff：在 `pick_next_task()` 里 idle 兜底分支处 `rq_i->dl_server = NULL`，再统一 `rq_i->core_dl_server = rq_i->dl_server`（核心思路是「core 树 pick 或 idle 都不经 DL server，先把被替换 pick 留下的 link 清掉」）。

## 版本演进与当前进展

*current_version: v1（2026-11-12 发出，`<20261112161548.78189-1-sieberf@amazon.com>`，5 补丁）*。今日为评审日：Peter 对 3/5 认可、对 2/5 给出折叠替代方案，作者尚未回应。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：3/5「不喜欢但接受」；2/5 明确「在 pick_task 的 rq->lock drop 窗口里延迟保存 dl_server 很脆弱」，并给出具体替代实现（把「清 link」前移、统一赋值）。这是对 2/5 实现方式的实质意见，要求作者改或折叠。
- 无 NAK；3/5 已收敛，2/5 待作者按 Peter 的替代方案改。

## 合入评估

*likelihood=medium*。Peter 已介入并认可 3/5 方向，但 2/5 的实现需按「rq->lock drop 窗口」的脆弱性重构，作者尚未回应。*blocking_issues*：① 2/5 保存 dl_server 的时序脆弱，需按 Peter 的折叠方案改；② 补丁正文细节待下一版核实。*next_action*：作者采纳 Peter 对 2/5 的折叠替代实现后出 v2。

## 效果评估

今日无新增数据。既有（20261113-002）：5s 窗口实测 plain tip 10/10 失败（0.000%），全系列 31/31 通过（3.99-5.19% vs 预留 5%），作者 QEMU 环境自测、非独立复现。

## 我可以参与的点

- **review**：核对 Peter 给出的折叠 diff 与作者原 2/5 的语义等价性（尤其 `pick_task()` drop lock 窗口下 `core_dl_server` 是否会读到未复位的 stale link）。
- **testing**：在真实 core scheduling 硬件上跑 `cs_dl_server_test`，验证份额恢复且无 forced-idle WARN。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261112161548.78189-1-sieberf@amazon.com/
- Peter 对 2/5 的折叠替代: https://lore.kernel.org/all/20261118135052.GX1779021@noisy.programming.kicks-ass.net/
- Peter 对 3/5 的认可: https://lore.kernel.org/all/20261118135249.GY1779021@noisy.programming.kicks-ass.net/
