---
id: sched-20261012-004
date: '2026-10-12'
subject: 'sched_ext: idle: Respect task affinity in restricted CPU selection'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261011173100.2090211-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261011173100.2090211-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Andrea Righi
current_version: v3
patch_series:
- version: v2
  msgid: <20261011131700.1351541-1-sh_def@163.com>
  date: '2026-10-11'
  summary: 从任务状态推导候选 CPU 并校验 p->cpus_ptr 与 @allowed
  review_outcome: Andrea 指出需保留 SCX_PICK_IDLE_IN_NODE 约束
- version: v3
  msgid: <20261011173100.2090211-1-sh_def@163.com>
  date: '2026-10-11'
  summary: 因子化成 select_cpu_restricted()，补跨 NUMA 校验，Preserve SCX_PICK_IDLE_IN_NODE
  review_outcome: Andrea Righi 给出 Reviewed-by
fixes_commit: 683d2d0faba1
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 已获 Andrea Reviewed-by，等纳入 sched_ext 分支（Cc stable）
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles:
- sched-20261011-003
tags:
- sched_ext
title: 'sched_ext: idle: Respect task affinity in restricted CPU selection'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-003-sched-ext-idle-respect-task-affinity-in-restricted-cpu-selec.html">sched-20261011-003</a>：Hui Su 修 sched_ext restricted `select_cpu` kfunc 路径在单 CPU / migration-disabled 任务上可能返回「不在 `p->cpus_ptr` 内」的空闲 CPU 的问题；经 Andrea Righi review 后 v2 改为从任务状态推导候选 CPU。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-004-sched-ext-idle-respect-task-affinity-in-restricted-cpu-selec.html">sched-20261012-004</a>（今天）：作者发 v3——因子化成 `select_cpu_restricted()`、补 `SCX_PICK_IDLE_IN_NODE` 跨 NUMA 校验；Andrea Righi 已给 `Reviewed-by`，合入阻力清除。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-003-sched-ext-idle-respect-task-affinity-in-restricted-cpu-selec.html">sched-20261011-003</a>）restricted `select_cpu` kfunc 路径为单 CPU / migration-disabled 任务直接以 `prev_cpu` 为候选，但 `prev_cpu` 只是提示、亲和性变更后可能已不可用，加上 caller 提供的 `@allowed` 掩码，可能返回「不在 `p->cpus_ptr` 内」的空闲 CPU。v2 已改为按任务状态推导候选，但漏了 `SCX_PICK_IDLE_IN_NODE` 的跨节点约束。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-003-sched-ext-idle-respect-task-affinity-in-restricted-cpu-selec.html">sched-20261011-003</a>）v3 把受限路径因子化成 `select_cpu_restricted()`：单 CPU 任务用 `cpumask_first(p->cpus_ptr)`、migration-disabled 任务用 `task_cpu(p)`；依次校验 `p->cpus_ptr`、caller 的 `@allowed` 掩码、再在 `flags & SCX_PICK_IDLE_IN_NODE` 时校验候选与 `prev_cpu` 同 NUMA 节点（跨节点返回 `-EBUSY`），全部通过后才 `scx_idle_test_and_clear_cpu()`（避免清位失败后消耗 idle 位）。

## 版本演进与当前进展

- v2（10-11）：从任务状态推导候选 + 校验 `p->cpus_ptr`/`@allowed`；Andrea 提醒需保留 `SCX_PICK_IDLE_IN_NODE`（「Good catch」），作者回帖「会把 restricted 路径因子化 + 补跨节点校验，SCX_PICK_IDLE_CORE 单独做 follow-up」。
- v3（10-11/12）：落实上述改动，作者自测（x86_64 KVM/QEMU）覆盖 affinity、stale-prev_cpu、caller-mask、跨 NUMA 四类用例，v2 跨节点返回 CPU2 而 v3 返回 -EBUSY；build 覆盖 `CONFIG_PREEMPT_RCU`/`CONFIG_SMP` 组合。
- 10-12：Andrea Righi 回帖 `Reviewed-by: Andrea Righi`。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者之一）已 `Reviewed-by`，从 v2 的跨节点缺陷提示到 v3 的正式背书，无遗留分歧。`Fixes: 683d2d0faba1` + `Cc: stable`。

## 合入评估

*likelihood=high*。获得维护者 `Reviewed-by`、正确性修复 + 自测，`Cc: stable` 表明会走 stable 回合。*blocking_issues*：无。*next_action*：等纳入 sched_ext 分支收取（scrollable）。

## 效果评估

作者自测：跨 NUMA 用例 v2 错误返回 CPU2、v3 正确返回 -EBUSY；build 覆盖多 config。无性能数字（正确性修复）。

## 我可以参与的点

已获 R-b、无争议，当前阶段暂无明显参与空间。

## 参考链接

- lore（v3）: https://lore.kernel.org/all/20261011173100.2090211-1-sh_def@163.com/
- lore（Andrea Reviewed-by）: https://lore.kernel.org/all/asvT3st3qtn05dur@gpd4/
