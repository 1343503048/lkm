# sched/deadline, cpuset: total_bw corrupted by a sleeping DL task's cpuset move

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261101-007：Weiheng Qiu 报告睡眠态 SCHED_DEADLINE 任务在 root cpuset 与 exclusive partition 间来回移动（未运行）会漏记带宽、导致超额准入与退出时下溢，附复现程序，尚无 fix。
- sched-20261102（今天）：Juri Lelli 给出 inline 修复——`set_cpus_allowed_dl()` 里不再用陈旧的 `task_rq(p)->rd`，改用新 helper `dl_task_root_domain_cpu()`（按 `p->cpus_ptr` 与 `cpu_active_mask` 定位真实 root domain），并请作者确认。

## 背景与问题

（承接）`set_cpus_allowed_dl()` 用 `task_rq(p)->rd` 决定带宽迁移源；睡眠任务 affinity 变化时不迁移、`task_rq(p)` 仍指上次运行的旧 CPU，导致「移回 root」方向既不贷记 root 也不借记 partition。

## 技术方案

Juri 修复（`kernel/sched/deadline.c`，+22/−7）：新增 `dl_task_root_domain_cpu(p)`，用 `cpumask_first_and(p->cpus_ptr, cpu_active_mask)` 定位带宽当前实际记账的 root domain；`set_cpus_allowed_dl()` 的源 `src_dl_b = &cpu_rq(src_cpu)->rd->dl_bw` 据此取。

## 版本演进与当前进展

维护者今日首次给出 fix 草案，待报告者确认。

## Maintainer 意见与讨论焦点

Juri 直接给出方案并请作者验证；无分歧暴露。潜在关注点是 `BUG_ON(cpu >= nr_cpu_ids)` 在热插拔边界下是否稳健。

## 合入评估

likelihood=high。维护者给出针对性修复，方向明确。

## 效果评估

（承接）作者此前复现：移回 root 后 root/partition 均不再变化、root 误多准入 28 个 0.1-CPU 任务、退出后 `total_bw` 下溢到 -0.350。

## 我可以参与的点

- testing：用作者 `cpuset_blocked_move.c` 验证 Juri 修复后 total_bw 归零。
- review：审阅 `dl_task_root_domain_cpu()` 在 CPU offline 边界的 `BUG_ON` 稳妥性。

## 参考链接

- lore thread: https://lore.kernel.org/all/14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com/

---
type: bug
status: under_review
severity: high
thread_root_msgid: <14508cb2-805f-41ac-9f6b-bfd7c3d7cb1c@gmail.com>
authors:
- Weiheng Qiu
maintainers_involved:
- Juri Lelli
current_version: v1
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需作者确认修复、关注热插拔边界 BUG_ON 稳健性
  next_action: 报告者验证后由 Juri 正式提交
contribution_opportunities:
- kind: testing
  description: 用 cpuset_blocked_move.c 验证 total_bw 归零
- kind: review
  description: 审阅 dl_task_root_domain_cpu 的 offline 边界
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20261101-007
tags:
- deadline
- cgroup
id: sched-20261102-014
subject: 'sched/deadline, cpuset: total_bw corrupted by a sleeping DL task''s cpuset
  move'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
