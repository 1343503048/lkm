# sched/deadline, cpuset: total_bw corrupted by a sleeping DL task's cpuset move

## TL;DR

Weiheng Qiu 报告：把处于睡眠态的 SCHED_DEADLINE 任务在 root cpuset 与 exclusive partition 之间来回移动（且中途未运行），会让 root domain 的 `total_bw` 少记该任务带宽，导致超额准入、任务退出时 `total_bw` 下溢——小 DL 请求 -EBUSY、大请求在 `__dl_overflow()` 中回绕被误准入。附带完整复现程序，尚无 fix。

## 背景与问题

`cpuset_can_attach()` 与 `set_cpus_allowed_dl()` 都通过 `dl_task_needs_bw_move()` 决定是否做带宽迁移，该函数检查 `task_rq(p)->rd`。睡眠任务在 affinity 改变时不会被迁移，`task_rq(p)` 仍指向它上次运行的 CPU；因此「移入 partition 再从 partition 移回 root」这第二个方向既不重新贷记 root domain、也不借记 partition。作者在 mainline `c339f4010dea`（4 CPU）复现：移入 partition 时 root -0.500 / partition +0.500，移回 root 时两者均不再变化（预期均回到 0），随后 root domain 误多准入 28 个 0.1-CPU 任务；这些任务退出后 DL 任务再退出时 root `total_bw` 下溢到 -0.350。

## 技术方案

未给出补丁。根因定位：带宽迁移判定依赖 `task_rq(p)->rd`，对未运行的睡眠任务这是陈旧的 rq 指针；移回方向因「仍在原 rd」而跳过记账。作者提供复现程序（`cpuset_blocked_move.c`，cgroup v2 + cpuset controller + debugfs，需把最后一颗 CPU 设为 partition，建议测试 VM）。

## 版本演进与当前进展

v1：单一 bug 报告 + 复现程序，本窗口内无回复。

## Maintainer 意见与讨论焦点

未获取到（无人回复）。

## 合入评估

未知（unknown）。刚发出的 bug 报告，无人认领。阻塞项：无维护者确认。修复方向（如基于实际 affinity/cpuset 归属而非 `task_rq(p)` 判定带宽迁移）尚未讨论。

## 效果评估

作者复现数据（mainline `c339f4010dea`，0.5 CPU 的睡眠 DL 任务）：移入 partition 后 root 由 0.650 降到 0.150、partition 由 0.050 升到 0.550；移回 root 时两者不变（预期回到 0.650/0.050）。root 随即多准入 28 个 0.1-CPU 任务（0.650 + 2.8 = 3.450 CPU，超 3.000 CPU 上限）；任务退出后 DL 任务退出导致 root 下溢到 -0.350；重建 root domain 后恢复为 root 0.150 / partition 0.050。

## 我可以参与的点

- new_patch：修复 `dl_task_needs_bw_move()`/`set_cpus_allowed_dl()` 的迁移判定，使睡眠任务的 cpuset 迁移正确迁移带宽（或在其醒来时重算）。
- testing：在 NUMA/多 partition 拓扑上复现并验证修复后的 `total_bw` 一致性。

## 参考链接

- lore thread: https://lore.kernel.org/all/14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com/

---
id: sched-20261101-007
subject: "sched/deadline, cpuset: total_bw corrupted by a sleeping DL task's cpuset move"
date: 2026-11-01
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: "<14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com>"
lore_url: "https://lore.kernel.org/all/14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com/"
authors: [Weiheng Qiu]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com>"
    date: 2026-11-01
    summary: "bug 报告 + 复现程序（cpuset_blocked_move.c）"
    review_outcome: "无人回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "无维护者/社区成员确认与诊断"
  next_action: "需要 sched/deadline 与 cpuset 维护者确认根因并确定修复方向"
contribution_opportunities:
  - kind: new_patch
    description: "修复 dl_task_needs_bw_move()/set_cpus_allowed_dl() 对睡眠任务 cpuset 迁移的带宽迁移判定"
  - kind: testing
    description: "在 NUMA/多 partition 拓扑上复现并验证修复后 total_bw 一致性"
generated_at: "2026-11-02T09:00:00"
source_email_count: 1
related_articles: []
tags: [deadline, cgroup]
---