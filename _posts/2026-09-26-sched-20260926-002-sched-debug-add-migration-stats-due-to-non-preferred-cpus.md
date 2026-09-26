---
id: sched-20260926-002
date: 2026-09-26
subject: 'sched/debug: Add migration stats due to non preferred CPUs'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <eb2369f7-a17c-434c-801f-1a8afaac4cad@linux.ibm.com>
lore_url: https://lore.kernel.org/all/eb2369f7-a17c-434c-801f-1a8afaac4cad@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-27T01:20:00'
authors:
- Shrikanth Hegde
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v13
  msgid: <20260909135617.871006-10-sshegde@linux.ibm.com>
  date: 2026-09-09
  summary: 新增 nr_migrations_cpu_non_preferred 迁移统计，经 /proc/<pid>/sched 暴露
  review_outcome: 09-25 Peter 提 changelog 语义 + schedstat 版本两条；09-26 Shrikanth 澄清无需
    bump 版本
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 系列层入队 sched/core、目标 7.4 未获 Peter 表态
  - 跨子系统 ack 仍空白
  next_action: Shrikanth 改 changelog 后随 v14 重发；等待 Peter 对系列整体拍板
contribution_opportunities:
- kind: review
  description: 核对迁移计数递增点是否覆盖唤醒路径与 tick 推走路径两类非 preferred 迁移，避免漏计/重复计数
- kind: discussion
  description: 确认 perf sched stat 及后续 schedstat 解析工具在新增字段后是否需适配格式
- kind: testing
  description: v14 发出后跑绑核混配负载，观测计数与 steal 收缩行为是否一致
source_email_count: 1
related_articles:
- sched-20260925-010
- sched-20260909-010
tags:
- sched_debug
- load_balance
- affinity
title: 'sched/debug: Add migration stats due to non preferred CPUs'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles（steal_governor v13 系列）。

- <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260909-010</a>：Shrikanth Hegde 发出 steal_governor v13（13 补丁），本片（09/13）在 sched/debug 侧新增因「非 preferred CPU」引起的迁移统计。
- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>：Peter Zijlstra 首次逐枚细读，对 09/13 提两条——迁移计数的语义需在 changelog 写清、以及「改了输出格式是否该 bump schedstat 版本」。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-002-sched-debug-add-migration-stats-due-to-non-preferred-cpus.html">sched-20260926-002</a>（今天）：Shrikanth 回帖回答 schedstat 版本问题——这个改动动的是 `/proc/<pid>/sched` 而非 `/proc/schedstat`，前者没有版本号可 bump，`perf sched stat` 也不读 `/proc/<pid>/sched`，所以无需升版本。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>）steal_governor 系列引入 preferred CPU 机制后，任务会因 CPU 非 preferred 而被调度器从该 CPU 上推走或在唤醒时避开。这类「因非 preferred CPU 导致的迁移」此前没有独立统计口径，难以观测机制真实触发的频率与分布。本片在 sched/debug 统计里补一个 `nr_migrations_cpu_non_preferred` 计数，专门记录这类迁移。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-010-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html">sched-20260925-010</a>）在 sched/debug 的 per-task 统计里新增迁移计数，随任务被非 preferred CPU 场景迁移时递增，并通过 `/proc/<pid>/sched` 暴露。统计口径是「push 迁移次数」这一子集，而非全部迁移。今天讨论的是该统计的**输出通道**：它落在 `/proc/<pid>/sched`（不带版本号），不落在带版本语义的 `/proc/schedstat`，因此不触发任何版本 bump 义务。

## 版本演进与当前进展

- v13（09-09）：本片随系列发版。
- 09-25：Peter 对 09/13 提两条意见（changelog 语义写全 + schedstat 版本问题），Shrikanth 已接受前一条、准备 v14。
- 09-26：Shrikanth 回复（`<eb2369f7-a17c-434c-801f-1a8afaac4cad@linux.ibm.com>`）澄清 schedstat 版本不用改，并引用 2026-01 的 Swapnil Sapkal 补丁佐证 `/proc/<pid>/sched` 无版本语义。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（09-25）：语义问题（只读出 push 迁移次数、不完整）+ 输出格式变化是否要 bump schedstat 版本（`<20260925154540.GO2009045@noisy.programming.kicks-ass.net>`）。
- **Shrikanth Hegde**（09-26）：回答版本问题——不改 `/proc/schedstat`、`perf sched stat` 不依赖 `/proc/<pid>/sched`，无需升版本。无 NAK，changelog 部分作者已承诺改。

## 合入评估

*likelihood=medium*。本片自身的两个 review 点都已收敛（changelog 会改、版本不用 bump）；仍卡在系列层——Peter 未对「入队 sched/core、目标 7.4」表态、跨子系统 ack 空白。*blocking_issues*：系列层入队时点未定；跨子系统确认仍缺。*next_action*：Shrikanth 改 changelog 后随 v14 重发，等待 Peter 对系列整体拍板。

## 效果评估

无 benchmark 数据；本片为可观测性统计新增，效果体现在能定位「preferred CPU 机制实际触发多少次迁移」，尚无可量化数据。

## 我可以参与的点

- `review`：核对 `nr_migrations_cpu_non_preferred` 的递增点是否覆盖「唤醒路径 + tick 推走路径」两类非 preferred 迁移，避免漏计或重复计数。
- `discussion`：确认 `perf sched stat`（以及后续可能出现的 schedstat 解析工具）在系列引入新字段后是否需适配格式（Peter 自己存疑），可给结论或适配 patch。
- `testing`：v14 发出后跑一组绑核混配负载，观测该计数是否与「ΔRPS / steal time 收缩行为」一致。

## 参考链接

- Shrikanth 今日回复: https://lore.kernel.org/all/eb2369f7-a17c-434c-801f-1a8afaac4cad@linux.ibm.com/
- Peter 的 schedstat 版本问题: https://lore.kernel.org/all/20260925154540.GO2009045@noisy.programming.kicks-ass.net/
- v13 封面: https://lore.kernel.org/all/20260909135617.871006-1-sshegde@linux.ibm.com/
