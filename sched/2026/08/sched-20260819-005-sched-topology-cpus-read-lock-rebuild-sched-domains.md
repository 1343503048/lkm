# Sebastian Siewior 修复 `CONFIG_CPUSETS=n` 下读 `sched_rt_runtime_us` 因缺 `cpu_hotp...


## TL;DR
Sebastian Siewior 修复 `CONFIG_CPUSETS=n` 下读 `sched_rt_runtime_us` 因缺 `cpu_hotplug_lock` 触发的 backtrace，v2 把 `cpus_read_lock` 上移到 `rebuild_sched_domains()`。同时顺带修好 EAS 在 CPUfreq governor 切换时的同类问题。

## 背景与问题
读 `/proc/sys/kernel/sched_rt_runtime_us` 在 `CONFIG_CPUSETS=n` 下触发 backtrace：调用链 `sched_rt_handler() -> partition_sched_domains() -> sched_cache_set() -> static_key_enable_cpuslocked(&sched_cache_present)`，而 `cpuslocked` 系列函数要求持有 `cpu_hotplug_lock`。`CONFIG_CPUSETS=y` 时另一版 `rebuild_sched_domains()` 会自取该锁，故仅 =n 受影响。该回归由 commit `a7660ce1590fc`（sched/cache 多 LLC 修复）引入。

## 技术方案
v2 把 `guard(cpus_read_lock)()` 从 `partition_sched_domains()` 上移到 `rebuild_sched_domains()` 内部（仅 `CONFIG_CPUSETS=n` 分支），因为这是唯一受影响路径。回复者补充：该修复也覆盖 EAS 的 `rebuild_sched_domains_energy()` 场景——在 CPUfreq governor 从 schedutil 切到其他（如 ondemand）时会触发同样的锁缺失。

## 版本演进与当前进展
- v1：在 `partition_sched_domains()` 内加锁。
- v2（8/19）：按 Yu C Chen / Tim Chen 意见，把锁上移到 `rebuild_sched_domains()`，仅覆盖 CONFIG_CPUSETS=n，避免扩大加锁范围。

## Maintainer 意见与讨论焦点
无 NAK。讨论聚焦加锁范围的精确性：v2 已收窄到最小受影响路径；并确认 EAS 能量重建路径一并受益。

## 合入评估
合入可能性 high：精准、局部的锁修复，有明确 Fixes 标签和回归 commit，且 v2 已按 reviewer 意见收窄范围。

## 效果评估
无性能数据，属正确性/锁序修复。验证方式应为读 `sched_rt_runtime_us` 不再 backtrace。

## 我可以参与的点
- 在 CONFIG_CPUSETS=n 内核测试读接口与 EAS governor 切换，回帖确认警告消失。

## 参考链接
- lore thread: 未获取到
- Fixes: a7660ce1590fc

---
id: sched-20260819-005
date: 2026-08-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Sebastian Andrzej Siewior]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Dietmar Eggemann]
current_version: v2
patch_series:
  - version: v2
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "读 /proc/sys/kernel/sched_rt_runtime_us 在 CONFIG_CPUSETS=n 下因缺少 cpu_hotplug_lock 触发 backtrace（调用链 sched_rt_handler -> partition_sched_domains -> sched_cache_set -> static_key_enable_cpuslocked）。v2 把 guard(cpus_read_lock)() 从 partition_sched_domains() 上移到 rebuild_sched_domains()（仅 CONFIG_CPUSETS=n 受影响路径），由 Yu C Chen / Tim Chen 指出。"
    review_outcome: "v2 相对 v1 缩小加锁范围，仅覆盖 CONFIG_CPUSETS=n 的 rebuild_sched_domains()；回复者指出该修复同时覆盖 EAS 的 rebuild_sched_domains_energy() 场景（CPUfreq governor 切换 schedutil<->ondemand 时）。"
upstream_commit: null
fixes_commit: "a7660ce1590fc (\"sched/cache: Fix has_multi_llcs iff at least one partition has multiple LLCs\")"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需确认 CONFIG_CPUSETS=y 路径不受影响（该路径自带 hotplug 锁）"]
  next_action: "等待 maintainer 收下 v2。"
contribution_opportunities:
  - kind: testing
    description: "在 CONFIG_CPUSETS=n 内核上读 sched_rt_runtime_us 验证 backtrace 消失；并在 schedutil<->ondemand 切换时确认 EAS 重建不再触发锁警告。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 1
related_articles: []
tags: [sched/core, topology, rt, sched/cache]
---
