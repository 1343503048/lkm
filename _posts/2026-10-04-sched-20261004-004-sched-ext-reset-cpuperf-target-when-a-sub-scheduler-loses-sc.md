---
id: sched-20261004-004
date: '2026-10-04'
subject: 'sched_ext: Reset cpuperf_target when a sub-scheduler loses SCX_CAP_PERF
  or dies'
subsystem: sched_ext
type: bug
status: under_review
severity: medium
thread_root_msgid: <20261004012721.615419-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20261004012721.615419-1-cui.tao@linux.dev/
authors:
- Tao Cui
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261004012721.615419-1-cui.tao@linux.dev>
  date: '2026-10-04'
  summary: PERF 写持有者退场时恢复中性 cpuperf 基线（per-CPU irq_work 执行 reset）
  review_outcome: 当日无回帖；Tejun 后续走回调方案（见 10-08 报道）
upstream_commit: null
fixes_commit: 86094b95efcf
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 与 Tejun 的 last-writer-wins 裁决及回调方案的关系待澄清
  next_action: 跟进 ops.sub_child_ecaps_updated() 系列的落地形态
contribution_opportunities:
- kind: review
  description: 对照 Tejun 回调方案论证本 reset-sweep 方案的互补性/必要性
generated_at: '2026-10-05T01:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cpufreq
- dvfs
title: 'sched_ext: Reset cpuperf_target when a sub-scheduler loses SCX_CAP_PERF or
  dies'
layout: article
---

## TL;DR

Tao Cui（KylinOS）的单补丁修复 sched_ext 子调度器 DVFS 残留问题：持有 `SCX_CAP_PERF` 的子调度器设了一个低 cpuperf target 后退场——cap 被回收（revoke）、被 kill、detach 或 cgroup 摘除——`rq->scx.cpuperf_target` 却留在原地。`scx_bpf_sub_revoke()` 只清 pshard caps 位图（`scx_cpuperf_set()` 的写门槛挡住新写入但不复位旧值），`scx_sub_disable()` 摘走任务、解除链表也不碰 target；而读者门槛 `scx_cpuperf_target()` 只测全局 `scx_enabled()`（root 调度器还活着就为真），schedutil 每次 DVFS 更新都继续吃这个陈旧 target。**switched-all 模式下**（sugov_get_util() 不再叠加 CFS 利用率）受影响 CPU 被钉死在低频，直到 sched_ext 整体禁用重启用；root 调度器像 scx_simple 从不调 cpuperf kfunc，钉死无限期。修法：任何持有者退场时恢复 root 调度器 enable 时建立的中性基线——`scx_bpf_sub_revoke()` 对实际回收的 cid 对应 CPU 排队 reset、`scx_sub_disable()` 在解除并排干后扫该调度器的 pshard `SCX_CAP_PERF` cmasks 对每个持过 cap 的 CPU 排队 reset；reset 需要目标 rq 锁，但 revoke 路径在 pshard 锁下关中断且可能从 BPF 持另一 rq 锁进入，故经 per-CPU irq_work 在目标 CPU 上执行。VM 实测：子调度器设 target 1 后被 kill，基线下 `rq->scx.cpuperf_target` 全载停在 1，打补丁后 kill 即刻回到 `SCX_CPUPERF_ONE`。`Fixes: 86094b95efcf`（"sched_ext: Add per-shard cap delegation for sub-schedulers"）。

## 背景与问题

- 触发链条（补丁 commit message 梳理）：子调度器设低 target → 退场（cap revoke / kill / detach / cgroup removal）→ 写门槛失效但旧值残留 → `scx_cpuperf_target()` 只看全局 `scx_enabled()` → schedutil 以陈旧 target 为利用率基底做每次 DVFS 更新。
- 最坏场景：switched-all 模式 + 不调 cpuperf kfunc 的 root 调度器（如 scx_simple）——CPU 低频钉死无上限期。
- 首报版本：`Fixes:` 指向 86094b95efcf（per-shard cap delegation 引入）；sub-scheduler 机制为 sched_ext 近期大特性。

## 技术方案

单补丁（`kernel/sched/ext/sub.c` +103）：

- **中性基线恢复**：任何 PERF 写持有者退场即恢复 root enable 时的基线（`SCX_CPUPERF_ONE`）。`scx_bpf_sub_revoke()` 对实际回收 cid 的 CPU 排队 reset；`scx_sub_disable()` 在 unlink+drain 后扫 pshard PERF cmaks，对每个 CPU 排队 reset。
- **锁序约束下的执行载体**：revoke 在 pshard 锁下关中断、可能从 BPF 持另一个 rq 锁进入——reset 经 **per-CPU irq_work** 在目标 CPU 执行，避免跨 CPU rq 锁。
- **边界取舍（作者明示）**：离线 CPU 跳过（排队会触发 irq_work 离线告警、无保证执行点，残留值在 sched_ext 重启用时清除）；多调度器共享 cap 时可能 over-reset——仍持 cap 的调度器下次更新会改写自己的 target，最坏情况 CPU 暂回中性基线，有界（对比要防的无限期钉死）。

## 版本演进与当前进展

- v1（10-04，`<20261004012721.615419-1-cui.tao@linux.dev>`）发出，当日无回帖。

## Maintainer 意见与讨论焦点

- 无回帖。后续走向（据 10-08 既有报道）：Tejun Heo 对 cpuperf target 的语义裁决为 **last-writer-wins**，并在其 `ops.sub_child_ecaps_updated()` 系列里吸收本补丁的实测（见 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）；Tao Cui 另报的子调度器饥饿问题见 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-006-sched-ext-sub-scheduler-tasks-are-severely-under-scheduled-v.html">sched-20261008-006</a>。

## 合入评估

*likelihood=unknown*（本日报视角）。问题真实、VM 实测明确；但补丁刚发、sub-scheduler 子系统尚在快速演进，Tejun 后续以回调通知方案（`sub_child_ecaps_updated()`）而非本补丁的 reset-sweep 方向收敛（见 10-08 报道）。*blocking_issues*：与 Tejun 的语义裁决（last-writer-wins）与回调方案的关系待澄清。*next_action*：跟进 Tejun 的替代系列落地形态。

## 效果评估

VM 实测（补丁自带）：子调度器设 target 1 后 kill——基线下全载时 `rq->scx.cpuperf_target` 停在 1；打补丁后 kill 即刻回 `SCX_CPUPERF_ONE`。over-reset 的最坏代价（暂回中性基线）为论证性结论，未见数据。

## 我可以参与的点

- `review`：对照 Tejun 的 `ops.sub_child_ecaps_updated()` 系列（10-07 发出）评估本 reset-sweep 方案的 over-reset 语义是否仍被需要（两方案互补性论证，可回帖帮收敛）。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20261004012721.615419-1-cui.tao@linux.dev/
