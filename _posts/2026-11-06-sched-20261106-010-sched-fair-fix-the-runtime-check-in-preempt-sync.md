---
id: sched-20261106-010
date: 2026-11-06
subject: 'sched/fair: Fix the runtime check in preempt_sync()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261106085001.36135-1-peng_wang@linux.alibaba.com>
lore_url: https://lore.kernel.org/all/20261106085001.36135-1-peng_wang@linux.alibaba.com/
authors:
- Peng Wang
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261106085001.36135-1-peng_wang@linux.alibaba.com>
  date: 2026-11-06
  summary: 改用 sum_exec_runtime - prev_sum_exec_runtime 修复 preempt_sync 恒 0。
  review_outcome: Peter 认可修复，索要 WF_SYNC 性能数据；作者给出 hackbench/TCP_RR。
upstream_commit: null
fixes_commit: e837456fdca8
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - TCP_RR 8 客户端 -2.1% 且两次对比方向不一致，需澄清是否为噪声
  next_action: 作者澄清 TCP_RR -2.1% 或补充更稳定负载数据，等待 Peter 收取
contribution_opportunities:
- kind: testing
  description: 复跑 WF_SYNC 敏感负载验证 TCP_RR -2.1% 是噪声还是真回退
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- cfs
- preempt
title: 'sched/fair: Fix the runtime check in preempt_sync()'
layout: article
---

## TL;DR

Peng Wang（阿里）修复 `preempt_sync()` 里 NEXT_BUDDY 的 runtime 检查恒为 0 的 bug：`wakeup_preempt_fair()` 已经先调 `update_curr_fair()` 把 `se->exec_start` 更新成 `rq_clock_task()`，随后 `preempt_sync()` 用 `rq_clock_task() - se->exec_start` 算出的已运行时长永远是 0，导致 WF_SYNC wakeup 里「等当前任务跑够时间再强制 reschedule」的判定失效。修复改用 `sum_exec_runtime - prev_sum_exec_runtime`（任务被 pick 后真正跑了多久）。Peter Zijlstra 认可其正确性，并索要 WF_SYNC 的性能数据；作者给出 hackbench/TCP_RR 数据（大体中性偏正）。

## 背景与问题

`preempt_sync()` 在 NEXT_BUDDY 启用时，为 WF_SYNC（同步唤醒）的抢占设了门槛——只有当当前任务已运行足够久（`sysctl_sched_migration_cost` 阈值）才允许强制 reschedule，以避免立刻抢占刚跑起来的、缓存热的任务。但计算「已运行多久」的时间基准取错了：`wakeup_preempt_fair()` 在调用它之前已经 `update_curr_fair()`，把 `se->exec_start` 刷成了当前 `rq_clock_task()`，于是 `delta = rq_clock_task() - se->exec_start` 恒为 0，门槛形同虚设。

## 技术方案

把 `delta` 的算法从 `rq_clock_task(rq) - se->exec_start` 改为 `se->sum_exec_runtime - se->prev_sum_exec_runtime`——后者是任务自被 pick 以来的实际运行时长，不受 `update_curr_fair()` 刷写 `exec_start` 的影响。顺带删掉不再使用的 `rq` 形参（`preempt_sync()` 签名简化）。改动 +4/-4 行。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。Peter 当日认可修复方向（「Well yes」），并要求补 WF_SYNC 性能数据；作者随即回复了在 4-socket Xeon Platinum 8369HB 上跑的 hackbench 与 loopback TCP_RR 数据。

## Maintainer 意见与讨论焦点

Peter Zijlstra 认可 bug 与修法（「Well yes」），关注点转向「这个修复对 WF_SYNC 负载的实际性能影响」。无 NAK。

## 合入评估

*likelihood=medium*。修复正确性得到维护者认可、改动极小，但尚需确认性能数据不引入回退（TCP_RR 8 客户端出现 -2.1% 的波动）。*blocking_issues*：① 性能数据方向不一致（hackbench 多数小幅改善，TCP_RR 8 客户端 -2.1% 且两次对比方向相反），Peter 可能要求更稳的数据或认定噪声。*next_action*：作者澄清 TCP_RR -2.1% 是否为噪声、或补充更稳定负载的数据，等待 Peter 收取。

## 效果评估

作者数据（4-socket Xeon Platinum 8369HB，NEXT_BUDDY+HRTICK、PREEMPT_FULL、HZ=1000，A/B/A/B 共 4 boot、每 boot 3 次取中位）：

- hackbench：pipe light -0.7%、pipe heavy -3.1%、socket light -5.3%、socket heavy +0.2%、thread 系列 +0.2%～-1.7%（多数小幅改善）。
- loopback TCP_RR（1 字节、10s）：1 client -0.1%、8 clients -2.1%（两次 A/B 对比分别为 +0.33% 与 -4.46%，方向不一致）。

总体中性偏正，但 TCP_RR 8 客户端的 -2.1% 被作者自己标注为「两次对比方向不一致」。

## 我可以参与的点

- **testing**：复跑 WF_SYNC 敏感负载（如 pf/pipe 微基准、同步 RPC）对比本修复，帮助判断 TCP_RR -2.1% 是噪声还是真回退——这是 Peter 明确想要的数据。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106085001.36135-1-peng_wang@linux.alibaba.com/
- Peter 索要数据的回帖: https://lore.kernel.org/all/20261106103140.GE1779021@noisy.programming.kicks-ass.net/
