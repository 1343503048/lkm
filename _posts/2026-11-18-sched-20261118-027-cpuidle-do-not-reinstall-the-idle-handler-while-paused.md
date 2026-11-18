---
id: sched-20261118-027
date: '2026-11-18'
subject: 'cpuidle: Do not reinstall the idle handler while paused'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261117-cpuidle-pause-fix-v1-1-b2789fce4c16@gmail.com>
lore_url: https://lore.kernel.org/all/20261117-cpuidle-pause-fix-v1-1-b2789fce4c16@gmail.com/
authors:
- Wondertan
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261117-cpuidle-pause-fix-v1-1-b2789fce4c16@gmail.com>
  date: '2026-11-17'
  summary: cpuidle resume 尊重暂停状态，暂停期间不重装 idle handler
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 cpuidle/PM 维护者 review
contribution_opportunities:
- kind: testing
  description: SystemIO 深 C-state 的 ACPI 平台反复冬眠/恢复验证不再挂死
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- idle
- nohz
- hang
title: 'cpuidle: Do not reinstall the idle handler while paused'
layout: article
---

## TL;DR

Wondertan 修复 ACPI 平台冬眠（hibernation）间歇性挂死：PM core 在系统级切换时暂停 cpuidle，但 `acpi_soft_cpu_online()` 里 `acpi_processor_hotplug()` 会用 `cpuidle_resume_and_unlock()` 无条件重装 idle handler，导致第一颗 secondary CPU 上线后 cpuidle 就被实际恢复；随后上线的 CPU 进入深 ACPI C-state，`cache_aps_init()` 的 stop_machine 里 idle CPU 不回 IPI、另一 CPU soft-lock。修复让 resume 尊重暂停状态、暂停期间不重装 handler。

## 背景与问题

PM core 在系统级切换（休眠/恢复）期间通过 `pm_sleep_disable_secondary_cpus()`/`pm_sleep_enable_secondary_cpus()` 暂停 cpuidle，让 CPU 不进入 cpuidle 管理的 idle 状态。但 ACPI 下 `acpi_soft_cpu_online()` 为每颗上线的 CPU 调 `acpi_processor_hotplug()`，其内部 `cpuidle_pause_and_lock()`/`cpuidle_resume_and_unlock()` 会无条件重装 idle handler——于是第一颗 secondary CPU 上线后 cpuidle 就被实际恢复,后续 `cache_aps_init()` 跑 stop_machine 时 idle CPU 进入深 C-state、不回 IPI，另一 CPU soft-lock。`cpuidle_register_device()`/`cpuidle_switch_governor()` 同样可能解除暂停。

## 技术方案

让 cpuidle 的 resume 路径尊重暂停状态：暂停期间不重装 idle handler，直到 PM core 真正 resume。修复 Fedora 上 Framework Laptop 16（AMD Ryzen AI 9 HX 370，_CST 暴露 C2/C3 SystemIO entry）冬眠镜像已创建后间歇挂死，其中一 CPU 停在 `io_idle()` 不回 IPI、另一 CPU 在 `smp_call_function_many_cond()`（sched_cpu_activate 上线 sibling 时的 text poking）或 `multi_cpu_stop()`（cache_aps_init 的 MTRR rendezvous）soft-lock；镜像写不出、下次启动报 "PM: Image not found (code -22)"。

## 版本演进与当前进展

*current_version: v1（2026-11-17 发出，`<20261117-cpuidle-pause-fix-v1-1-b2789fce4c16@gmail.com>`）*。当日无 review。

## Maintainer 意见与讨论焦点

当日无维护者回帖。补丁附完整 soft-lockup 栈与 `power:cpu_idle` 追踪佐证，但尚无 cpuidle 维护者表态。

## 合入评估

*likelihood=medium*。复现清晰（冬眠挂死）、修复方向（尊重暂停）直接，但当日无维护者 review。*blocking_issues*：无实质分歧，等待 review。*next_action*：等 cpuidle/PM 维护者 review。

## 效果评估

作者在 6.18.59 上用 `power:cpu_idle` 追踪确认：第一颗与最后一颗 CPU_ON 之间的上线窗口里 CPU 进入 idle。属 correct 修复，无性能数据。

## 我可以参与的点

- **testing**：在 SystemIO 深 C-state 的 ACPI 平台反复冬眠/恢复，验证不再 soft-lock、镜像能写出。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261117-cpuidle-pause-fix-v1-1-b2789fce4c16@gmail.com/
