---
id: sched-20261009-003
date: '2026-10-09'
subject: 'cpufreq: Don''t track pressure if policy->max equals top of freq_table'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: <20261009082928.21847-1-ggherdovich@suse.cz>
lore_url: https://lore.kernel.org/all/20261009082928.21847-1-ggherdovich@suse.cz/
authors:
- Giovanni Gherdovich
maintainers_involved:
- Christian Loehle
current_version: v1
patch_series:
- version: v1
  msgid: <20261009082928.21847-1-ggherdovich@suse.cz>
  date: '2026-10-09'
  summary: policy->max 达到 freq_table 顶时 pressure 置零
  review_outcome: Christian Loehle 指出 f341dc4d934a 已修复；作者确认并放弃
upstream_commit: f341dc4d934a
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 问题已被 f341dc4d934a 修复，补丁为重复劳动
  next_action: 无，系列终结
contribution_opportunities: []
generated_at: '2026-10-10T01:30:00'
source_email_count: 3
related_articles: []
tags:
- cpufreq
- psi
- x86
title: 'cpufreq: Don''t track pressure if policy->max equals top of freq_table'
layout: article
---

## TL;DR
Giovanni Gherdovich（SUSE）发补丁，解决 acpi-cpufreq 上 `cpufreq_pressure` 在标称条件下虚高、导致任务迁移加剧/局部性丢失的性能回退。但 Christian Loehle 指出该问题已被 `f341dc4d934a`（"cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()"）修复，作者当日确认「Yes that fixes it」，补丁被放弃。

## 背景与问题
acpi-cpufreq 把非 boost 频率存进 `policy->freq_table`，但 `policy->cpuinfo.max_freq` 含最大 boost 频率；`policy->max` 至多等于 freq_table 最大值。于是标称条件下 `policy->max` 显著低于 `cpuinfo.max_freq`，导致所有 CPU 无端出现很大的 `cpufreq_pressure`（32%）。后果是「用有限 CPU 数的计算/内存密集 benchmark 出现明显性能回退——任务迁移更多、局部性丢失」。作者用 NAS Parallel Benchmarks（限 1/4 CPU）复现。一个具体例子（AMD EPYC Naples + acpi-cpufreq）：freq_table = 1200/1700/2200 MHz，`policy->max`=2200，`cpuinfo.max_freq`=3200（max boost）→ 变更前 pressure=320（32%），预期应为 0。

## 技术方案
作者方案：当 `policy->max` 等于（或高于）freq_table 最大值时，把 `cpufreq_pressure` 置零。在 `cpufreq_update_pressure()` 加一个 `else if` 分支（`policy->freq_table && policy->max_table_freq && policy->max_table_freq <= capped_freq` 时 pressure=0），并在 `freq_table.c` 加 `max_table_freq` 字段、`cpufreq.h` 加成员。+5 行。作者还特意在正文列出相关维护者名单（Mario Limonciello、Huang Rui、Vincent Guittot、Ricardo Neri、Pierre Gondois），因为 cpufreq_pressure 与调度负载均衡有交叉。

## 版本演进与当前进展
v1 首发（`<20261009082928.21847-1-ggherdovich@suse.cz>`）。当日即被指出已被上游修复，补丁作废。

## Maintainer 意见与讨论焦点
- **Christian Loehle（ARM）**：提示该补丁是否基于 `f341dc4d934a`（"cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()"），若不是请在其上重试。
- **Giovanni Gherdovich（作者）**：确认「Ah! Yes that fixes it」——标称条件下 acpi-cpufreq 的 pressure 已为零，因为该 commit 把 pressure 跟踪条件设为依赖驱动实现 `.scale_freq`。

关键结论：问题已被既有 upstream 修复覆盖，本补丁为重复劳动。

## 合入评估
*likelihood=rejected*。作者已确认 `f341dc4d934a` 解决了同一问题，补丁不再必要。*next_action*：无，系列终结。

## 效果评估
无独立 benchmark（问题本身被上游 commit 修复）。作者描述的「32% 虚假 pressure → 任务迁移加剧/局部性丢失」的现象是真实动机，但修复路径已由上游承担。

## 我可以参与的点
当前阶段暂无明显参与空间，问题已由上游修复、补丁被放弃。可留意 `f341dc4d934a` 是否覆盖 acpi-cpufreq 之外的其它非 `.scale_freq` 驱动的同类情况。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261009082928.21847-1-ggherdovich@suse.cz/
- Christian Loehle 回复: https://lore.kernel.org/all/32a250e5-0c56-43ce-ab80-8c4375542b59@arm.com/
- 作者确认: https://lore.kernel.org/all/f15bb2b4-f11e-4e44-959d-11055720d99b@suse.cz/
