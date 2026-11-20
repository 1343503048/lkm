---
id: sched-20261120-005
date: '2026-11-20'
subject: 'sched/fair: Don''t let task_tick_cache() IPI dyntick CPUs'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261119203825.2732984-1-vschneid@redhat.com>
lore_url: https://lore.kernel.org/all/20261119203825.2732984-1-vschneid@redhat.com/
authors:
- Valentin Schneider
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261119203825.2732984-1-vschneid@redhat.com>
  date: '2026-11-19'
  summary: task_tick_cache() 识别远程 tick 并 bail，避免 IPI 打断 dyntick CPU
  review_outcome: Peter 质疑信号与 NUMA 路径区别对待，未收敛
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 判定条件未与 Peter 一致
  - NUMA 路径待一并处理
  next_action: 作者按 NOHZ_FULL+tick 已关信号改版并覆盖 task_tick_numa()
contribution_opportunities:
- kind: review
  description: 判断 NOHZ_FULL+tick 已关信号与 cpu_of(rq)!=smp_processor_id() 的等价性及 NUMA 适用性
- kind: testing
  description: isolcpus/NOHZ_FULL 环境复现 ipi_send_cpu 调用链并验证改版效果
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles: []
tags:
- cfs
- nohz
- idle
title: 'sched/fair: Don''t let task_tick_cache() IPI dyntick CPUs'
layout: article
---

## TL;DR

Valentin Schneider 发单补丁：在 NOHZ_FULL / isolcpus 场景下，housekeeping CPU 周期性地替 dyntick CPU 跑 `sched_tick_remote()`，从而触发 `task_tick_cache()` 的 `task_work_add()` 把纯用户态任务 IPI 踢出 userspace。补丁让 `task_tick_cache()` 识别「远程 tick」并直接 bail。Peter Zijlstra 连续追问「那 `task_tick_numa()` 怎么就不一样？」，Valentin 回应信号应是「任务在 NOHZ_FULL CPU 且 tick 已关」。方向仍在收敛。

## 背景与问题

作者在测试 CPU isolation / NOHZ_FULL 时抓到 `ipi_send_cpu` 调用链：`task_tick_fair → task_work_add → kick_process` 由 `sched_tick_remote`（housekeeping CPU 替隔离 CPU 执行的周期性远程 tick）触发。此时隔离 CPU 上跑的单个纯 userspace SCHED_OTHER 任务被 `task_cache_work()` 踢出 userspace，破坏了 dyntick 隔离的初衷——本应充分利用 dynticks 的任务被反复打断。

## 技术方案

在 `task_tick_cache()` 里加一个判断：若 `cpu_of(rq) != smp_processor_id()`（即本次 tick 是远程执行），直接 `return`，不再给 dyntick CPU 上的任务排 `task_work()` IPI。

Peter 的反问集中在「为何只挡 `task_tick_cache()` 而不挡同样由远程 tick 触发的 `task_tick_numa()`」，并给了两个方向的建议：其一给 `task_tick_numa()` 加 `sched_numa_balancing` 提前 return、把 `task_tick_core()` 前提；其二用 `!rq->rd` 判断无 root domain 则无均衡直接返回。Valentin 回应：NUMA 路径在他的 QEMU 上难以触发、但原则上同理；他倾向的信号是「任务是否在 NOHZ_FULL CPU 且 tick 已关」，若如此则什么也不做，让 LLC/RD 内其它 CPU 去均衡；若全 dyntick 则本就无事可做。

## 版本演进与当前进展

*current_version: v1（2026-11-19 发出、11-20 收件，`<20261119203825.2732984-1-vschneid@redhat.com>`，单补丁）*。今日为评审日：Peter 与 Valentin 就「正确信号是什么、NUMA 路径为何区别对待」来回讨论，无新版本。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：两条评论——「how is `task_tick_numa()` different here?」与「I'm not sure `sched_tick_remote()` is the right condition here」，并给出一段替代 diff（`task_tick_numa` 加 `sched_numa_balancing` 早退、`!rq->rd` 早退、调整 `task_tick_fair` 调用顺序）；后一条「If you have a root domain with more than 1 CPU in it, you get balancing, deal with it.」表明他不接受简单按「远程 tick」一刀切。
- **Valentin Schneider（作者）**：主张信号应为「任务在 NOHZ_FULL CPU 且 tick 已关」，并认为该原则也应覆盖 NUMA 路径。
- 无 NAK；分歧在「用什么条件判定该 skip」，未收敛。

## 合入评估

*likelihood=medium*。问题（dyntick 被 IPI 打断）真实、作者方向合理，但 Peter 明确不认可当前按 `sched_tick_remote()` 判定的实现，要求覆盖 NUMA 路径并给出更精确的信号；需作者改版。*blocking_issues*：判定条件（`sched_tick_remote()` vs 「NOHZ_FULL + tick 已关」）未与 Peter 达成一致，NUMA 路径待一并处理。*next_action*：作者按「NOHZ_FULL + tick 已关」信号改版并覆盖 `task_tick_numa()`。

## 效果评估

作者给出复现栈（`ipi_send_cpu` 由 `task_work_add` 触发），未给出量化「被打断次数/开销」数据；Peter 未要求基准。属开销/隔离正确性问题，无性能数字。

## 我可以参与的点

- **review**：判断「任务在 NOHZ_FULL CPU 且 tick 已关」这一信号在 `sched_tick_remote` 语义下是否等价于 `cpu_of(rq) != smp_processor_id()`，及对 `task_tick_numa()` 的适用性。
- **testing**：在 isolcpus/NOHZ_FULL 环境复现 `ipi_send_cpu` 调用链，验证改版后 dyntick CPU 不再被 IPI 打断。

## 参考链接

- lore thread（patch）: https://lore.kernel.org/all/20261119203825.2732984-1-vschneid@redhat.com/
