---
id: sched-20260919-001
date: '2026-09-19'
subject: 'sched/deadline: Fix zero-CPU DL bandwidth handling'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260919153150.2618403-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260919153150.2618403-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260812123252.2355986-3-sh_def@163.com>
  date: '2026-08-12'
  summary: 仅在 DL server 参数更新路径兜底除零
  review_outcome: 见 sched-20260827-016
- version: v2
  msgid: <20260919153150.2618403-1-sh_def@163.com>
  date: '2026-09-19'
  summary: 在 __dl_sub()/__dl_add() 统一处理 cpus==0，debugfs 收紧为 cpu_active()，拆为 2 patch
  review_outcome: 回应 Mikhail 建议；本日发出，尚无维护者 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 刚发出，等待 deadline 维护者 review 与 ack
  next_action: Juri/Daniel review v2 的拆分与 helper 守卫，确认 stable backport 范围后收取
contribution_opportunities:
- kind: testing
  description: 在热插拔/offline 场景复现 dl_bw_cpus()==0 窗口，验证覆盖全部调用者
- kind: review
  description: 审查 cpu_online() 收紧为 cpu_active() 后是否有合法用例受影响
generated_at: '2026-09-20T09:00:00'
source_email_count: 5
related_articles:
- sched-20260827-016
tags:
- deadline
- dl_server
- crash
title: 'sched/deadline: Fix zero-CPU DL bandwidth handling'
layout: article
---

## TL;DR
增量更新：Hui Su 的 SCHED_DEADLINE 除零修复推出 v2——把 v1 只修 debugfs DL server 路径的做法，推广为在公共 helper `__dl_sub()`/`__dl_add()` 里统一处理 `cpus == 0`，覆盖 sched_setscheduler() 等更多调用点；并把 debugfs 的 `cpu_online()` 检查收紧为 `cpu_active()`，另拆成独立补丁。触发点是在 CPU hot-unplug 期间，CPU 先从 `cpu_active_mask` 摘除、尚未 offline 的窗口里 `dl_bw_cpus()` 返回 0，导致除零 panic。v2 刚发出（本日 23:31），尚无维护者 review。

## 背景与问题
背景见 sched-20260827-016（v1）：CPU 热卸载时，CPU 在变为 offline 之前先从 `cpu_active_mask` 摘除；若它是 root domain 里最后一个 active CPU，`dl_bw_cpus()` 会返回 0，而相关路径仍可到达，从而在向 active runqueue 分发带宽更新时发生除零。v1 只在 DL server 参数更新路径上兜底。

本日 Mikhail Zaslonko（IBM s390x）回报了同一问题的更一般形态：从 `sched_setscheduler()` 系统调用路径同样触发除零——`task_non_contending()` 把 `dl_bw_cpus(task_cpu(p))` 返回的 0 传给 `__dl_sub()`。栈显示 `dsgr %r4,%r2`（除指令）崩溃，`panic_on_oops` 直接 panic；panic 前 11 秒有 `select_fallback_rq` 与 "no longer affine to cpu118/cpu122" 的 CPU offlining 并发日志。Mikhail 还指出 `__dl_sub()`/`__dl_add()` 有多个其他调用者。

## 技术方案
v2 把零 CPU 处理下沉到公共 helper，而不是继续在调用点打补丁：

- 1/2（`sched/deadline: Fix divide-by-zero in DL bandwidth accounting`）：在 `__dl_sub()`/`__dl_add()` 里对 `cpus == 0` 时跳过 `__dl_update()`，但仍保留 `dl_bw::total_bw` 的更新（没有 active runqueue 需要接收 extra_bw 调整）。改动 6 行，覆盖所有调用者。`Fixes: daec57983670`（"Reclaim bandwidth not used by dl tasks"），Cc stable。
- 2/2（`sched/deadline: Reject debugfs dl_server writes for inactive CPUs`）：把 `sched_server_write_common()` 里的 `!cpu_online(cpu_of(rq))` 改为 `!cpu_active(cpu_of(rq))`，在 CPU 一旦变为 inactive（而非等其 offline）即拒绝 per-CPU DL server 写。`Fixes: d741f297bcea`（"sched/fair: Fair server interface"），Cc stable。

拆分理由（作者在回帖中说明）：helper 问题早于 DL server debugfs 接口出现，把通用修复单独成 patch 能让 review 与 stable backport 范围各自清晰。

## 版本演进与当前进展
- v1（2026-08-12，`<20260812123252.2355986-3-sh_def@163.com>`）：仅在 DL server 参数更新路径修复（见 sched-20260827-016）。
- 本日 Mikhail Zaslonko（`<c52c9e8c-260e-49a4-a88e-229e0795d07b@linux.ibm.com>`）报 sched_setscheduler 路径同款除零，并建议在 `__dl_sub()`/`__dl_add()` 统一处理。
- 作者 Hui Su 回帖（`<6dbd08d0d0ca288b77dfc7c393898d86.sh_def@163.com>`）认可该方向，说明将拆成两 patch 并给出测试矩阵。
- v2（2026-09-19，`<20260919153150.2618403-1-sh_def@163.com>`）：按上述拆分为 2 patch 发出。base-commit `f259f446f5198d98e13756d2cd531812a0ad3064`。

## Maintainer 意见与讨论焦点
本日无 sched/deadline 维护者（Juri Lelli / Daniel Bristot de Oliveira）直接表态。Mikhail 的开场问候是 "Hello Hui, Juri"，但 Juri 未在本窗口回帖。当前讨论事实：

- **Mikhail Zaslonko**：给出 s390x 崩溃栈与并发 offlining 证据，明确建议在公共 helper 处理 `cpus == 0`（作者已采纳）。
- 分歧/未决：暂无实质分歧；两个 patch 各自配了不同 `Fixes:` 与 stable Cc，backport 范围是否合理需维护者确认。

## 合入评估
*likelihood=medium*。修复方向明确、有真实崩溃报告支撑、Cc stable，且 v2 已按 reviewer 建议重构；但 v2 刚发出（本日 23:31），尚无 deadline 维护者的 review/ack。*blocking_issues*：等待 Juri/Daniel 对 v2 拆分与 `__dl_sub()`/`__dl_add()` 守卫方式的确认。*next_action*：deadline 维护者 review v2，确认两个 Fixes 与 stable backport 范围后收取。

## 效果评估
作者在 x86_64 上自测：cpus=0/1/2/4 的 DL bandwidth 记账、`task_non_contending()`/`inactive_task_timer()` 零 CPU 路径、100 轮 root-domain 重建/offline-online 循环、200 次跨 root-domain SCHED_DEADLINE cpuset 迁移、SCHED_FLAG_RECLAIM 策略切换、并发 SCHED_DEADLINE/SCHED_OTHER 切换 + CPU hotplug、100 轮 CPU hotplug/debugfs 更新，全部通过；并做了 inactive-but-online debugfs 窗口的 A/B 验证（仅 patch 1 时写被接受、两 patch 后写被拒且 runtime 不变）。Mikhail 的 s390x 崩溃栈为最直接的效果证据。

## 我可以参与的点
- kind=testing：在自身关注的热插拔/离线场景（如 s390x、或大规模 cpuset 重建）复现 `dl_bw_cpus()==0` 窗口，验证 v2 是否彻底覆盖 `__dl_sub()`/`__dl_add()` 的所有调用者。
- kind=review：审查 2/2 把 `cpu_online()` 收紧为 `cpu_active()` 后，是否存在仍应在 offline 前允许写 DL server 的合法用例。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260919153150.2618403-1-sh_def@163.com/
- lore（Mikhail 报告）: https://lore.kernel.org/all/c52c9e8c-260e-49a4-a88e-229e0795d07b@linux.ibm.com/
