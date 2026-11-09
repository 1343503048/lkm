---
id: sched-20261109-015
date: '2026-11-09'
subject: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <0cb3d965-1eb0-41fe-8abd-67292bc2cfeb@huaweicloud.com>
lore_url: https://lore.kernel.org/all/0cb3d965-1eb0-41fe-8abd-67292bc2cfeb@huaweicloud.com/
authors:
- Luo Gengkun
maintainers_involved: []
current_version: v10
patch_series:
- version: v10
  msgid: null
  date: '2026-10-09'
  summary: 2 补丁：task_cache_work 只扫访问过的 CPU
  review_outcome: Prateek + Chen Yu 双 Tested-by，Chen Yu Reviewed-by，Tim 两处 nit
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v11 尚未发出；无维护者最终表态
  next_action: 作者出 v11，等 Tim/Peter 收取
contribution_opportunities:
- kind: review
  description: 审查 v11 commit message 并入的 benchmark 数字是否完整可复核
- kind: testing
  description: 在 NUMA 多 LLC 平台复跑验证 visit_cpu 扫描省开销无回退
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261021-010
- sched-20261022-012
tags:
- load_balance
- cfs
- topology
title: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-010-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261021-010</a>：Luo Gengkun（华为）的系列（task_cache_work 只扫访问过的 CPU）推进到 v10；K Prateek Nayak 在 4 代 EPYC 上实测给 Tested-by（hackbench/tbench/stream/netperf/schbench 无超方差回退），并建议把 benchmark 数字放进 commit message。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-012-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261022-012</a>：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench 后给 Reviewed-by + Tested-by；Tim Chen 提两处注释/死代码 nit。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-015-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261109-015</a>（今天）：**作者出差归来，逐条回应三位 reviewer**——接受 Tim 的注释与「删冗余 continue」建议、感谢 Chen Yu 复跑 hackbench、承诺把 Prateek 的性能数字写进 commit message 并加其 Tested-by；v11 在望。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-010-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261021-010</a> / 20261022-012）`task_cache_work()` 周期性扫描 CPU 维护 cache 感知聚合的 footprint，v10 只扫描「访问过的 CPU」以降开销。该系列自 07-31 v9 后推进到 v10，已获 Prateek（EPYC）与 Chen Yu（Xeon 多 LLC）双 Tested-by + Chen Yu Reviewed-by，正等维护者收取。

## 技术方案

今日无新代码，为评审收尾：作者回应 Tim Chen（更新注释、删冗余 `continue` 简化逻辑）、回应 Chen Yu（致谢其多 LLC hackbench 测试）、回应 Prateek（把性能数字并入 commit message、加 Tested-by tag）。这些是 v11 的具体修改清单，无机制性改动。

## 版本演进与当前进展

*current_version: v10（2026-10-09 发出，2 补丁）*。今日：作者出差归来集中回应三位 reviewer，确认 v11 将更新注释、删冗余 `continue`、把 benchmark 并入 commit message、加 Prateek Tested-by。

## Maintainer 意见与讨论焦点

- **Tim Chen**：两处注释/死代码小 nit（作者已接受）。
- **Chen Yu**：Reviewed-by + Tested-by（作者致谢）。
- **K Prateek Nayak**：Tested-by + 建议把性能数字存档进 commit（作者已接受）。
- 无 NAK；三位 reviewer 均已给 Tested-by/Reviewed-by，方向一致。

## 合入评估

*likelihood=high*。双 Tested-by（Prateek + Chen Yu）+ Chen Yu Reviewed-by，仅剩注释/commit message 收尾，作者已确认 v11 落地。*blocking_issues*：① v11 尚未发出；② 仍无维护者（Peter/Tim 作为 intel 侧）最终表态。*next_action*：作者出 v11（含上述修改），等 Tim/Peter 收取。

## 效果评估

既有数据：Prateek 在 4 代 EPYC（2×128C/256T）上 hackbench/tbench/stream/netperf/schbench 整体无超 run-to-run 方差回退、有小的提升；Chen Yu 在多 LLC/node Xeon 上重点压 LLC 饱和下 visit_cpu mask 争抢，无回退、有轻微提升。今日无新增数据。

## 我可以参与的点

- **review**：审查 v11 的 commit message 中并入的 benchmark 数字是否完整可复核。
- **testing**：在 NUMA 多 LLC 的其它平台（如 AMD）复跑，验证 visit_cpu 扫描省开销无回退。

## 参考链接

- 作者回应 Tim 的建议: https://lore.kernel.org/all/8a494e8f-c30b-4cfa-af08-a0a641bdd6a5@huaweicloud.com/
- 作者回应 Prateek: https://lore.kernel.org/all/0cb3d965-1eb0-41fe-8abd-67292bc2cfeb@huaweicloud.com/
