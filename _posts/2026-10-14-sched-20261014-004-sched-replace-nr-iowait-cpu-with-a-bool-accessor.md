---
id: sched-20261014-004
subject: 'sched: Replace nr_iowait_cpu() with a bool accessor'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261014134745.3032405-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261014134745.3032405-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261014134745.3032405-1-christian.loehle@arm.com>
  date: 2026-10-14
  summary: nr_iowait_cpu() 改为 bool cpu_has_iowait()，nr_iowait() 直读计数，附 Coccinelle
    recipe
  review_outcome: 当日无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review；接口改名触及 s390 与 export 面
  next_action: 待维护者 review 接口命名与 Coccinelle 配方
contribution_opportunities:
- kind: review
  description: 核对 Coccinelle 覆盖全部调用点及 nr_iowait/cpu_has_iowait 语义一致性
- kind: testing
  description: s390 与 generic 配置下编译并验证 /proc/stat iowait 无漂移
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- idle
- nohz
title: 'sched: Replace nr_iowait_cpu() with a bool accessor'
layout: article
---

> **subject**：sched: Replace nr_iowait_cpu() with a bool accessor

## TL;DR
Christian Loehle 跟进同日 `sched/cputime: Preserve iowait accounting...` 线程里 Peter 对 `nr_iowait_cpu()` 误用的批评，发清理补丁：menu governor 已不再消费 per-CPU iowait 计数的大小，剩余调用方只关心「零/非零」，故把返回 `unsigned int` 的 `nr_iowait_cpu()` 改为返回 `bool` 的 `cpu_has_iowait()`，让「是否在 iowait」的语义显式化并避免误用。纯重构、无行为变更，当日无 review。

## 背景与问题
`nr_iowait_cpu()` 返回 per-CPU iowait 计数的**大小**，其唯一需要大小值的消费者是已删除的 menu governor（`38f83090f515 "cpuidle: menu: Remove iowait influence"`）。如今所有 per-CPU 调用方（generic `kcpustat_*`、s390 `arch_kcpustat_*`、`get_cpu_*_time_us`）都只做 `> 0` 的零/非零判定，却仍拿着一个「大小」接口——这正是同日 Peter 批评「用 `nr_iowait_cpu()` 是掷骰子」的温床：把聚合计数当 per-CPU 状态判据。

## 技术方案
把 `nr_iowait_cpu()`（`include/linux/sched/stat.h` + `kernel/sched/core.c`）改为 `bool cpu_has_iowait(int cpu)`，返回 `atomic_read(&cpu_rq(cpu)->nr_iowait) != 0`；`nr_iowait()` 直接 `sum += atomic_read(...)` 保留全局总量。更新 generic 与 s390 idle 记账调用方，替换过时的 menu 注释，并附 `scripts/coccinelle/api/cpu_has_iowait.cocci`（5 条 `@ definition/prototype/total/predicate/callers` 规则，`make coccicheck COCCI=... MODE=patch` 可复现转换）。改动 `arch/s390/kernel/idle.c`、`include/linux/sched/stat.h`、`kernel/sched/{core,cputime}.c` +69/−16。

## 版本演进与当前进展
v1（今日首发，`<20261014134745.3032405-1-christian.loehle@arm.com>`）。当日无 review；作者在同线程表示「若 Peter 有朝一日想退役 iowait（至少先退役 CPU 级 iowait），乐意投入时间」。

## Maintainer 意见与讨论焦点
本补丁暂无直接 review。背景意见来自同日另一线程（<a class="article-ref" href="/lkm/2026/10/14/sched-20261014-003-sched-cputime-preserve-iowait-accounting-across-waking-inter.html">sched-20261014-003</a>）的 **Peter Zijlstra**（批评 `nr_iowait_cpu()` 语义）与 **Christian Loehle** 本人（指出注释过时、该函数可重构）。无 NAK，方向与 Peter 的批评一致。

## 合入评估
*likelihood=unknown*。刚发出、无人 review；作为低风险重构，方向与维护者既有意见契合，但需 Peter 或 cputime/idle 相关维护者（Frederic 等）确认接口改名与 Coccinelle 配方的必要性。*blocking_issues*：无 review；接口改名触及 s390/export 面。*next_action*：待维护者 review；确认 `cpu_has_iowait` 命名与 `nr_iowait()` 直读计数是否被接受。

## 效果评估
纯语义重构，无性能/正确性数据。作者说明「剩余聚合 `nr_iowait` 用户为记账/上报（`/proc/stat` procs_blocked、s390 某处），难以整体移除」，故退而求其次收敛 per-CPU 接口。

## 我可以参与的点
- review：核对 Coccinelle recipe 是否覆盖全部 `nr_iowait_cpu()` 调用点（尤其 `nr_iowait()` 内直接读 `atomic_read` 后，`cpu_has_iowait` 与 `nr_iowait` 语义是否仍一致）。
- testing：在 s390 与 generic（含 `!CONFIG_IRQ_TIME_ACCOUNTING`）配置下编译并跑 `/proc/stat` iowait 相关断言，确认无行为漂移。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261014134745.3032405-1-christian.loehle@arm.com/
