---
id: sched-20260928-002
date: '2026-09-28'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260922165445.943315-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- John Stultz
current_version: v14
patch_series:
- version: v14
  msgid: <20260922165445.943315-1-arighi@nvidia.com>
  date: '2026-09-22'
  summary: 重做 donor 确认机制（SNT_CONFIRM）、删 scx_proxy_donor_start()，hrtick v4 前置
  review_outcome: 09-28 Peter 将 5 枚 core/hook 预备补丁应用到 tip/sched/core
upstream_commit: null
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues:
  - sched_ext 功能实现（填充 hook）尚未落地，待 Tejun 侧 apply
  next_action: 跟踪 Tejun 对 sched_ext 功能补丁的应用与合入通知
contribution_opportunities:
- kind: testing
  description: sched_ext + proxy execution 组合下跑互斥锁竞争压力测试并回帖实测
- kind: review
  description: 评估即将落地的 sched_ext 功能实现中 SNT_CONFIRM hook 的职责耦合
generated_at: '2026-09-29T01:00:00'
source_email_count: 5
related_articles:
- sched-20260927-004
- sched-20260925-011
- sched-20260924-007
tags:
- sched_ext
- proxy_execution
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。本系列的目标是让 proxy execution 与 sched_ext 可扩展调度类兼容——proxy execution 把阻塞在互斥量上的任务（donor）的调度上下文借给锁持有者运行，sched_ext 需要一组 hook 才能在这一机制下正确记账。

- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-011-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260925-011</a>：Peter 表态「I'll apply your patches as is」并问 Tejun 分区方式；前一天卡住的「Tejun 未回复分区问题」随后解除。
- <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-004-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260927-004</a>：Tejun 回复「I can pull from sched/core and then apply sched_ext parts on top」，分区敲定——Peter 收 core 侧、Tejun 收 sched_ext 侧。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-002-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260928-002</a>（今天）：Peter Zijlstra 把本系列 5 枚 core/hook 预备补丁（含空的 sched_ext hooks）全部应用到 tip/sched/core（5 个 tip-bot2 合入通知）。core 侧与 hook 骨架已落地，sched_ext 功能实现（填充 hook）仍待 Tejun 侧跟进。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-011-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260925-011</a> / <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-004-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260927-004</a>）proxy execution 让阻塞任务把执行上下文「借」给锁持有者运行。sched_ext 作为可扩展调度类，其 donor 记账、tick 归属、限流语义都与 core 调度路径强耦合，需要一组 sched_ext 侧 hook 才能在 proxy execution 下正确工作。核心张力：Peter 不喜欢 sched_ext 专属 hook，但也不喜欢把 sched_ext 逻辑塞进 core。今天背景无新增，进展是 core/hook 预备补丁实际落地。

## 技术方案

（承接）本系列在 `__schedule()` 三个点位暴露 sched_ext 观察点：`scx_allow_proxy_exec()`（是否允许 blocked EXT 任务作为 donor 留在运行队列）、`scx_proxy_donor_start()`（donor 的调度上下文开始驱动锁持有者）、`scx_proxy_reenqueue_retry()`（proxy 关系解除后重试被阻塞的 deferred reenqueue）。这些 hook 在系列内实现为空，`SCHED_PROXY_EXEC` 仍 `depends on !SCHED_CLASS_EXT`，编译出与否取决于 `CONFIG_SCHED_CLASS_EXT`。今天无新代码，5 枚补丁共同完成「把 sched_ext 兼容所需的 core 侧改动集中在前置补丁里」。

## 版本演进与当前进展

*current_version: v14*（core/hook 预备部分已合入 tip/sched/core）。9 月 28 日 Peter 一次性应用 5 枚补丁（均带其 Signed-off-by）：`sched/core: Drop mutex locks before proxy rescheduling`（313b652837d0）、`sched/core: Dequeue waking proxy donors before reset`（8f8c0417e973）、`sched/core: Mark wakeups completed through ttwu_runnable()`（a49653d0abeb）、`sched: Add helper to block retained proxy donors`（57c75e3ae38c）、`sched: Add sched_ext hooks for proxy execution`（be100c77178e）。sched_ext 功能实现（填充 hook）不在本系列，仍待 Tejun 侧。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（维护者）：5 枚补丁全部由其收取合入，兑现了前一日「照单全收」的承诺；「化简 hook」的疑虑被后置，不构成合入障碍。
- **John Stultz**：ack 了 `sched: Add helper to block retained proxy donors`（proxy execution 长期贡献者背书）。
- 无 NAK。剩余讨论点在代码组织（hook 职责耦合），作者自己也觉得「looks a bit confusing」，但不构成障碍。

## 合入评估

*likelihood=merged*（就本系列的 core/hook 预备部分而言）。5 枚补丁已进入 tip/sched/core。*blocking_issues*：sched_ext 功能实现（填充 `scx_allow_proxy_exec()` 等 hook）尚未落地，需 Tejun 侧在 sched/core 之上 apply。*next_action*：跟踪 Tejun 对 sched_ext 功能补丁的应用与合入通知。

## 效果评估

作者此前自述「passed all my scx proxy exec tests」，未附 benchmark 数字；正确性由自测背书，暂无量化性能数据。

## 我可以参与的点

- `testing`：在 sched_ext + proxy execution 组合下跑互斥锁竞争压力测试（scx 示例调度器 + 锁竞争负载），验证 donor 确认/tick 记账路径，回帖补充实测。
- `review`：关注即将由 Tejun 侧落地的 sched_ext 功能实现（填 hook），评估 `SNT_CONFIRM` 一个 hook 塞两件事（idle tick 记账 + reenqueue retry）的耦合是否值得拆。

## 参考链接

- v14 封面: https://lore.kernel.org/all/20260922165445.943315-1-arighi@nvidia.com/
- 合入 commit（sched: Add sched_ext hooks for proxy execution）be100c77178e: https://git.kernel.org/tip/be100c77178ef2299a080eb698720832a870248b
- 合入 commit（sched/core: Drop mutex locks before proxy rescheduling）313b652837d0: https://git.kernel.org/tip/313b652837d0541684680a7d07a95c5560441d4f
