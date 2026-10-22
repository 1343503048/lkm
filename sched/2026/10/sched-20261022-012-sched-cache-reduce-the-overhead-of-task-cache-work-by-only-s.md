# sched/cache: Reduce the overhead of task_cache_work by only scan the visisted cpus

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20260911-011：Luo Gengkun（华为）对 v9 系列友好 ping——所有 review 意见已解决，询问 Tim Chen 是否可收取；该系列（task_cache_work 只扫访问过的 CPU）自 07-31 v9 后沉默，维护者未表态。
- sched-20261021-010：系列推进到 v10（2 补丁，20261009 发出）；K Prateek Nayak 评审 1/2，在 4 代 EPYC 上实测后给 Tested-by（hackbench/tbench/stream/netperf/schbench 无超方差回退），并建议把 cover 的 benchmark 数字放进 commit message。
- sched-20261022-012（今天）：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench（4 LLC/node、重点压 LLC 饱和下 visit_cpu mask 争抢），无回退、有轻微提升，给出 Reviewed-by + Tested-by，并认为该改动能铺垫 Jianyong 的「多 preferred LLC/node」工作；Tim Chen 仅提两处注释/死代码小 nit。

## 背景与问题
（承接 sched-20260911-011）cache-aware scheduling 的 `task_cache_work`（per-task 周期性缓存统计）扫描全部 CPU，开销与 CPU 数成正比；方案用 `for_each_cpu_and` 结合 `visited_cpus` 位图只扫实际访问过的 CPU，去掉 `get_scan_cpumasks()`。今日无背景新增，进展集中在「再获陈宇实测背书 + 只剩注释级 nit」。

## 技术方案
（承接 sched-20260911-011 的 v8/v9）核心仍是 `for_each_cpu_and` + `visited_cpus` 只扫访问过的 CPU，并发安全由 `try_cmpxchg` 保证同一时刻只有一个 scanner。今日 Tim Chen 提两点小 nit：注释措辞（该处不只 skip 还清了 visited 位）、并指出某处 `continue` 无意义（occ 为 0 时后续累加/比较自然为空）。

## 版本演进与当前进展
*current_version: v10*（`<20261009032943.95091-2-luogengkun@huaweicloud.com>`）。当日无新版本，为评审背书与新 nit。

## Maintainer 意见与讨论焦点
Chen Yu（Intel）实测后给出 Reviewed-by + Tested-by，认为「从代码设计角度是个减少潜在开销的好优化，也为 Jianyong 的多 preferred LLC/node 工作铺路」。Tim Chen（Intel）仅提注释与死代码两处小 nit，未提实质异议。

## 合入评估
*likelihood=high*。已累计 K Prateek Nayak 与 Chen Yu 两个 Tested-by、Chen Yu 的 Reviewed-by，只剩注释级 nit；*blocking_issues*：无实质卡点；*next_action*：作者按 Tim Chen 的 nit 微调后待 Tim Chen/维护者收取。

## 效果评估
Chen Yu 今日 hackbench 数据（BASE: cas_on_base vs TEST: cas_on_visit，均无回退、有提升）：process 1×4 +8.21%、threads 2×16 +3.18%、threads 2×20 +7.43%、threads 4×8 +8.60%。此前 K Prateek 在 EPYC 上亦无超方差回退。

## 我可以参与的点
- *kind: review*：审读 Tim Chen 提出的注释与 `continue` 死代码两处 nit 的处理。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261009032943.95091-1-luogengkun@huaweicloud.com/
- Chen Yu 今日回帖：https://lore.kernel.org/all/20261009032943.95091-2-luogengkun@huaweicloud.com/
- Tim Chen 今日回帖：https://lore.kernel.org/all/995dc27d9bd27276c1fbf729ed88b7e6c91172f7.camel@linux.intel.com/

---
id: sched-20261022-012
date: 2026-10-22
subject: "sched/cache: Reduce the overhead of task_cache_work by only scan the visisted cpus"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261009032943.95091-1-luogengkun@huaweicloud.com>"
lore_url: "https://lore.kernel.org/all/20261009032943.95091-2-luogengkun@huaweicloud.com/"
authors: ["Luo Gengkun"]
maintainers_involved: []
current_version: v10
patch_series:
  - version: v10
    msgid: "<20261009032943.95091-2-luogengkun@huaweicloud.com>"
    date: 2026-10-09
    summary: "for_each_cpu_and + visited_cpus 只扫访问过的 CPU"
    review_outcome: "Chen Yu Reviewed+Tested（hackbench 无回退）；Tim Chen 提注释/nit"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "作者按 Tim Chen 的 nit 微调后待收取"
contribution_opportunities:
  - kind: review
    description: "审读注释与 continue 死代码两处 nit 的处理"
generated_at: "2026-10-23T01:20:00"
source_email_count: 2
related_articles: ["sched-20261021-010"]
tags: [cfs, numa_balancing]
---