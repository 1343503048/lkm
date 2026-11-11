# sched/rt: cpupri_find: Use cpumask_intersects where applicable

## TL;DR

Shrikanth Hegde（IBM）发五补丁清理系列，把「只为判断两个/三个 cpumask 是否有交集、却调用返回具体 CPU 的接口」的调用点统一改成 `cpumask_intersects`/`cpumask_intersects_and`。今日缓存只收到 patch 1/5（`sched/rt: cpupri_find`）与 patch 4/5（`cpuidle: Use cpumask_intersects_and`），其余三封不在缓存。纯微优化清理，无行为变化，刚发出、暂无回复。

## 背景与问题

`cpumask_any_and()` 内部对 `addr1[idx] & addr2[idx]` 做 `ffs`（找第一个置位并换算成 CPU 号），而 `cpumask_intersects()` 只检查这个 AND 结果是否非零；当返回值仅用于「是否 ≥ nr_cpu_ids」这类真/假判断时，`ffs` 的寻号工作是多余的。同理，`cpumask_first_and_and()` 对三路 AND 做 `ffs`，而 `cpumask_intersects_and()` 只做非零判断。作者在 `sched/rt` 的 `cpupri_find()` 与 `cpuidle` 的 coupled 路径里发现这类「返回了 CPU 却只用来判空」的调用，逐处替换。

## 技术方案

- **1/5 `sched/rt: cpupri_find: Use cpumask_intersects where applicable`**：`kernel/sched/cpupri.c` 的 `__cpupri_find()` 中，把 `if (cpumask_any_and(&p->cpus_mask, vec->mask) >= nr_cpu_ids) return 0;` 改为 `if (!cpumask_intersects(&p->cpus_mask, vec->mask)) return 0;`。
- **4/5 `cpuidle: Use cpumask_intersects_and where applicable`**：`drivers/cpuidle/coupled.c` 的 `cpuidle_coupled_any_pokes_pending()` 中，把 `return cpumask_first_and_and(cpu_online_mask, &coupled->coupled_cpus, &cpuidle_coupled_poke_pending) < nr_cpu_ids;` 改为 `return cpumask_intersects_and(...);`。
- 其余 patch（2/5、3/5、5/5）未在当日缓存，属同一清理系列在不同子系统的同类替换。

## 版本演进与当前进展

*current_version: v1（2026-11-11，cover `<20261111075945.3930230-1-sshegde@linux.ibm.com>`）*。五封补丁，当日仅收到 1/5 与 4/5。刚发出，暂无 review。

## Maintainer 意见与讨论焦点

当日无维护者回复。此类 `ffs`→`intersects` 替换是内核常见的低争议微优化，通常无分歧。

## 合入评估

*likelihood=unknown*。刚发出、无任何表态；但属于机械式清理，历史同类补丁争议极小。*blocking_issues*：无。*next_action*：等待 sched/cpuidle 维护者收取；可能需补全缺失的 2/5、3/5、5/5 以确认系列覆盖范围。

## 效果评估

暂无性能数据。收益是消除热路径上 `ffs` 寻号的多余开销（作者描述为语义等价替换），未见 benchmark。

## 我可以参与的点

- **review**：核对 `cpumask_any_and() >= nr_cpu_ids` 与 `!cpumask_intersects()` 的等价性在 cpupri 路径上是否严格成立（尤其空 mask 的边界语义）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111075945.3930230-1-sshegde@linux.ibm.com/
- patch 1/5: https://lore.kernel.org/all/20261111075945.3930230-2-sshegde@linux.ibm.com/
- patch 4/5: https://lore.kernel.org/all/20261111075945.3930230-5-sshegde@linux.ibm.com/

---
id: sched-20261111-003
date: '2026-11-11'
subject: "sched/rt: cpupri_find: Use cpumask_intersects where applicable"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261111075945.3930230-1-sshegde@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/20261111075945.3930230-1-sshegde@linux.ibm.com/"
authors: [Shrikanth Hegde]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261111075945.3930230-1-sshegde@linux.ibm.com>"
    date: '2026-11-11'
    summary: "把仅用于判空的 cpumask_any_and/first_and_and 调用改为 intersects 变体"
    review_outcome: "暂无回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等待 sched/cpuidle 维护者收取"
contribution_opportunities:
  - kind: review
    description: "核对 cpumask_any_and()>=nr_cpu_ids 与 !cpumask_intersects() 在空 mask 边界下的等价性"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [rt, idle, perf]
---
