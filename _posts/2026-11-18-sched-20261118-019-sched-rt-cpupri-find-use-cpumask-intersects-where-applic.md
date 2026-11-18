---
id: sched-20261118-019
date: '2026-11-18'
subject: 'sched/rt: cpupri_find: Use cpumask_intersects where applicable'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20261111075945.3930230-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261111075945.3930230-1-sshegde@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261111075945.3930230-1-sshegde@linux.ibm.com>
  date: '2026-11-11'
  summary: 把判空调用点改成 cpumask_intersects
  review_outcome: 两枚合入 tip/sched/core
upstream_commit: fda7fb5adda6c71be96f5836498d4b207c0811fc
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 观察系列其余补丁是否陆续合入
contribution_opportunities:
- kind: review
  description: 核对 cpumask_any_and>=nr_cpu_ids 与 !cpumask_intersects 的边界等价性
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261111-003
tags:
- rt
- topology
title: 'sched/rt: cpupri_find: Use cpumask_intersects where applicable'
layout: article
---

## TL;DR

Shrikanth Hegde（IBM）的 `cpumask_intersects` 清理系列**今日两枚被合入 tip/sched/core**：`sched/rt: cpupri_find`（commit `fda7fb5adda6`）与 `cpu/hotplug`（commit `69465ca8f6b5`），Committer Peter Zijlstra。把「只为判空却调用返回具体 CPU 的接口」的调用点改成 `cpumask_intersects`（`cpumask_any_and` 做 ffs 寻号、`cpumask_intersects` 只判 AND 非零），消除热路径多余寻号。纯微优化，无行为变化。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-003-sched-rt-cpupri-find-use-cpumask-intersects-where-applicable.html">sched-20261111-003</a>）`cpumask_any_and()` 对 `addr1[idx] & addr2[idx]` 做 `ffs`（换算成 CPU 号），`cpumask_intersects()` 只检查 AND 结果非零。当返回值仅用于「是否 ≥ nr_cpu_ids」的真/假判断时，ffs 的寻号是多余的。作者在 `sched/rt` 的 `cpupri_find()` 与 `cpu/hotplug` 的 `_cpu_down()` 里发现这类「返回了 CPU 却只用来判空」的调用并逐处替换。

## 技术方案

- `kernel/sched/cpupri.c`：`__cpupri_find()` 里 `if (cpumask_any_and(&p->cpus_mask, vec->mask) >= nr_cpu_ids) return 0;` → `if (!cpumask_intersects(&p->cpus_mask, vec->mask)) return 0;`（+1/-1）。
- `kernel/cpu.c`：`_cpu_down()` 里保持至少一个 housekeeping CPU 的判空改 `!cpumask_intersects(...)`（+1/-2）。

## 版本演进与当前进展

*current_version: v1（2026-11-11 发出，cover `<20261111075945.3930230-1-sshegde@linux.ibm.com>`，5 补丁）*。今日：其中两枚（cpupri_find、cpu/hotplug）合入 tip/sched/core。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：作为 Committer 合入两枚。
- 无 NAK；机械式清理低争议。

## 合入评估

*likelihood=merged*。两枚已合入 tip/sched/core（`fda7fb5adda6`、`69465ca8f6b5`）。*blocking_issues*：无。*next_action*：观察系列其余补丁（cpuidle 等）是否陆续合入。

## 效果评估

无性能数据；语义等价替换，消除热路径 ffs 寻号（作者描述为等价替换）。

## 我可以参与的点

- **review**：核对 `cpumask_any_and() >= nr_cpu_ids` 与 `!cpumask_intersects()` 在空 mask 边界下的严格等价性（尤其 cpupri 路径）。

## 参考链接

- tip 合入（cpupri_find）: https://git.kernel.org/tip/fda7fb5adda6c71be96f5836498d4b207c0811fc
- tip 合入（cpu/hotplug）: https://git.kernel.org/tip/69465ca8f6b5d332e7996643664442a93be254b6
- lore thread: https://lore.kernel.org/all/20261111075945.3930230-1-sshegde@linux.ibm.com/
