---
id: sched-20260911-011
subject: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
date: '2026-09-11'
subsystem: sched
type: fix
status: stalled
severity: low
thread_root_msgid: <20260731024417.1106503-1-luogengkun2@huawei.com>
lore_url: https://lore.kernel.org/all/20260731024417.1106503-1-luogengkun2@huawei.com/
authors:
- Luo Gengkun
maintainers_involved:
- Chen Yu
current_version: v9
patch_series:
- version: v8
  msgid: <cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com>
  date: 2026-07-27
  summary: for_each_cpu_and + visited_cpus 只扫访问过的 CPU，去掉 get_scan_cpumasks()。
  review_outcome: 并发安全疑问由 Chenyu 确认（try_cmpxchg 保证单 scanner）。
- version: v9
  msgid: <20260731024417.1106503-1-luogengkun2@huawei.com>
  date: 2026-07-31
  summary: 作者称全部意见已解决；v9 diff 未入缓存。
  review_outcome: 六周无维护者回应；09-11 作者 friendly ping 询问可否收取，仍无回应。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Tim Chen 对 ping 无回应，收取意愿未知
  - 维护者注意力被 sched/cache 0/4 修复系列与 prctl RFC 占据
  next_action: 等 Tim 回应；否则 rebase 到 sched/urgent 基线重发
contribution_opportunities:
- kind: testing
  description: 多核系统对比 v9 前后 task_cache_work 开销与亲和性效果，附独立数据
- kind: review
  description: 核对 v9 访问位维护是否覆盖全部路径
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
- sched-20260728-005
tags:
- cfs
- perf
title: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
layout: article
---

## TL;DR
Luo Gengkun（华为）当日对 v9 系列发出 friendly ping：所有 review 意见已解决、无未决问题，询问 Tim Chen 是否可以收取。该系列（task_cache_work 只扫访问过的 CPU）自 07-31 v9 发出后已沉默六周，维护者仍未表态——按当前状态归为停滞（stalled）。本文为增量更新，v8 阶段的方案与并发安全讨论见 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a>。

## 背景与问题
cache-aware scheduling 的 task_cache_work（per-task 周期性缓存统计工作）扫描全部 CPU，开销与 CPU 数成正比。方案是用 for_each_cpu_and 结合 visited_cpus 位图，只扫描实际访问过的 CPU，去掉 get_scan_cpumasks()。

## 技术方案
（承 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a> 的 v8：for_each_cpu_and + visited_cpus 只扫访问过的 CPU。）v8 阶段的关键结论：华为开发者提出的并发安全疑问由 Chenyu 确认——try_cmpxchg 保证同一时刻只有一个 scanner，并发访问位图是安全的。v9 相对 v8 的具体 diff 未入当日缓存，作者声明「All comments have been addressed and there are no outstanding issues」。

## 版本演进与当前进展
*current_version: v9（v9 root msgid `<20260731024417.1106503-1-luogengkun2@huawei.com>`，msgid 时间戳 07-31；当日入缓存为作者的 09-11 ping）*。

- v8（07-27，承 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a>）：引入 visited_cpus 扫描收敛；并发安全性经 Chenyu 确认；
- v9（07-31）：作者称吸收全部意见；
- 09-11：friendly ping——「让我知道是否可以收取（pick up），或还需要什么」；当日无维护者回应。

## Maintainer 意见与讨论焦点
- **Chenyu（intel）**：v8 阶段确认 try_cmpxchg 保证单 scanner（承 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a>）；
- **Tim Chen**：sched/cache 的核心维护者，ping 的直接对象，当日缓存内无回应。该系列等待的正是他的最终 review（07-28 文章的 next_action 已如此预判）。
- 无反对意见记录；争议点为空，问题是彻底的沉默。

## 合入评估
*likelihood=unknown*：技术讨论已收敛（作者声明无未决问题），但核心维护者六周未表态，无法评估收取意愿。*blocking_issues*：Tim Chen 未回应 ping；sched/cache 相关讨论当前由 Tim 的 0/4 修复系列与 prctl RFC 占据注意力（见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-003-sched-cache-fixes-for-cache-aware-scheduling.html">sched-20260911-003</a>、<a class="article-ref" href="/lkm/2026/09/11/sched-20260911-006-sched-cache-per-task-control-of-cache-aware-scheduling-via-p.html">sched-20260911-006</a>），本系列可能需要重发或换基线才能进入队列。*next_action*：等 Tim Chen 回应 ping；若仍无回应，考虑 rebase 到 sched/urgent 基线（0/4 系列同款）后重发。

## 效果评估
方案目标是降低 task_cache_work 的扫描开销（从全 CPU 收敛到 visited CPU），但邮件窗口内未获取到量化的开销对比数字（v8/v9 正文未入缓存）；「只扫访问过的 CPU」的收益面为作者设计主张，未见实测数据。

## 我可以参与的点
- kind=testing：在多核系统上对比 v9 前后 task_cache_work 的运行开销与 cache 亲和性效果，给 ping 帖附上独立数据，降低维护者确认成本（承 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a> 的参与点）。
- kind=review：重读 v9（lore 链接见下）核对四个更新点（enqueue/dequeue/set_delayed/clear_delayed 等价的访问位维护）是否有遗漏路径。

## 参考链接
- v9 root（msgid 取自当日 ping 的 References）：https://lore.kernel.org/all/20260731024417.1106503-1-luogengkun2@huawei.com/
- 当日 ping：https://lore.kernel.org/all/2f3b90e5-c626-4de9-84a7-ad9e25320906@huawei.com/
- v8 阶段线程（承 <a class="article-ref" href="/lkm/2026/07/28/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20260728-005</a>）：https://lore.kernel.org/all/cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com/
