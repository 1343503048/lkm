---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261102135420.244745-1-parri.andrea@gmail.com>
authors:
- Andrea Parri
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261102135420.244745-1-parri.andrea@gmail.com>
  date: '2026-11-02'
  summary: 将 __sched_setscheduler() 的 root-domain 判断从 p->cpus_ptr 改为 p->cpus_mask
  review_outcome: Aaron Tomlin 询问能否并入其系列并要求补 LLM Assisted-by 标签
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 尚无调度维护者确认 p->cpus_mask 替换不影响 DL bandwidth 记账
  next_action: 作者回应 Aaron 的并入提议与 LLM 声明后，等 sched 维护者确认
contribution_opportunities:
- kind: testing
  description: 在 PREEMPT_RT/非 RT、多种 CPU 拓扑下复跑 reproducer 验证拒绝率归零
- kind: review
  description: 审阅 cpus_ptr→cpus_mask 对 DL bandwidth 记账与 root domain 判断的影响
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 2
related_articles: []
tags:
- deadline
- cgroup
- affinity
- rt
id: sched-20261102-001
subject: 'sched/deadline: Fix spurious -EPERM for migration-disabled tasks'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched/deadline: Fix spurious -EPERM for migration-disabled tasks'
layout: article
---

## TL;DR

Andrea Parri 修复 `sched_setattr(SCHED_DEADLINE)` 在任务处于 `migrate_disable()` 段内时被误判为「affinity 未覆盖 root domain」而返回 -EPERM 的问题，根因是 `__sched_setscheduler()` 检查了 `p->cpus_ptr`（会被 `migrate_disable_switch()` 临时指向当前 CPU）而非真正的 affinity `p->cpus_mask`。附带复现程序与实测数据（PREEMPT_RT 上请求被拒率最高 55%）。Aaron Tomlin 回帖询问能否把该补丁并入其系列，尚未有维护者表态。

## 背景与问题

`sched_setattr()` 在任务被调度出去、处于 `migrate_disable()` 段内时，`migrate_disable_switch()` 会把 `p->cpus_ptr` 指向当前 CPU 直到 `migrate_enable()`；而 `__sched_setscheduler()` 用 `p->cpus_ptr` 判断某任务能否进入 SCHED_DEADLINE（要求 affinity 覆盖整个 root domain）。于是即便任务真实 affinity 覆盖 root domain，也会被错误地以 -EPERM 拒绝，且报错把责任归到一个任务其实并不具备的 affinity 上。PREEMPT_RT 上每个 `spinlock_t` 持有者都在这样的段内，普通内核工作即可打开该窗口；seccomp filter 也在其中运行。作者程序（root 运行）在一台 4-CPU PREEMPT_RT guest 上 100 万次请求中被拒 553679/453720/424623 次，无 PREEMPT_RT 时为 236182/217174/237183 次；应用补丁后归 0（含 lockdep）。

## 技术方案

改为测试 `p->cpus_mask`（这才是任务真实 affinity，也是 `sched_getaffinity()` 报告的来源）。安全性论证：已准入任务其 `cpus_mask` 覆盖 root domain，故 `migrate_enable()` 恢复 `p->cpus_ptr` 时 `set_cpus_allowed_dl()` 无需移动带宽。

## 版本演进与当前进展

v1 刚发出（2026-11-02），暂无维护者 review。Aaron Tomlin 回帖：能否把该补丁并入他的系列（lore 20261030151307.768523-1-atomlin@atomlin.com），并按 `Documentation/process/coding-assistants.rst` 要求标注 `Assisted-by:` 使用的 LLM。

## Maintainer 意见与讨论焦点

尚无调度维护者表态；唯一回帖是 Aaron Tomlin（非维护者）提出并入其系列的意向，同时提醒作者补充 coding-assistants 规定的 LLM `Assisted-by:` 标签。真正的合入门槛（Peter/Juri 是否认可 `cpus_ptr`→`cpus_mask` 的替换、是否会影响 bandwidth 记账）尚未触及。

## 合入评估

likelihood=medium。判定替换 `cpus_ptr` 为 `cpus_mask` 在语义上正确且影响面小，但尚无维护者确认；作者需先回应 Aaron 的并入提议与 coding-assistants 声明，再等 sched 维护者（Peter Zijlstra / Juri Lelli）确认 bandwidth 迁移不受影响。

## 效果评估

作者实测：4-CPU PREEMPT_RT guest 被拒率 55.4%/45.4%/42.5%，无 RT 时 23.6%/21.7%/23.7%，应用补丁后 0（含 lockdep），且 pin 到单 CPU 的任务仍被正确拒绝。

## 我可以参与的点

- testing：在 PREEMPT_RT / 无 RT、不同 CPU 数（含非 pow2）下复跑作者的 reproducer，确认拒绝率归零且带宽记账一致。
- review：审阅 `p->cpus_ptr` 改 `p->cpus_mask` 对 SCHED_DEADLINE bandwidth（`set_cpus_allowed_dl()`）与 root domain 判断的边界影响。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102135420.244745-1-parri.andrea@gmail.com/
