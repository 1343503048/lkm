---
id: sched-20260926-003
date: 2026-09-26
subject: 'sched/cputime: Add kcpustat_field_total helper'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <20260926073147.140907-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20260926073147.140907-1-kayracizmeci@gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-27T01:20:00'
authors:
- Shrikanth Hegde
maintainers_involved: []
patch_series:
- version: v13
  msgid: <20260909135617.871006-2-sshegde@linux.ibm.com>
  date: 2026-09-09
  summary: kcpustat_field_total helper；s390 计数改用 cpumask_weight()
  review_outcome: 09-26 Kayra Cizmeci nit：cpumask_weight() 改动未写进 commit message
merge_assessment:
  likelihood: high
  blocking_issues:
  - commit message 需补记 cpumask_weight() 改动
  - 合入与 13 片系列绑定，系列层入队 sched/core 未获 Peter 表态
  next_action: 作者在 v14 commit message 补一行说明即可
contribution_opportunities:
- kind: review
  description: 核对 helper 在 CONFIG_VIRT_CPU_ACCOUNTING_GEN 下与 s390 旧手写循环的等价性
source_email_count: 1
related_articles:
- sched-20260904-012
tags: []
title: 'sched/cputime: Add kcpustat_field_total helper'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles（steal_governor v13 系列第 1 片）。

- <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-012-sched-cputime-add-kcpustat-field-total-helper.html">sched-20260904-012</a>：Shrikanth Hegde 在 `include/linux/kernel_stat.h` 加 `kcpustat_field_total(usage, cpus)`，把「按 cpumask 累加某类 cpu_usage_stat」收成 inline，替换 s390 hiperdispatch 与 fs/proc/uptime.c 两处手写循环；已集齐 Frederic Weisbecker 的 Acked-by 与 Yury Norov、Mete Durlu 两个 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/09/26/sched-20260926-003-sched-cputime-add-kcpustat-field-total-helper.html">sched-20260926-003</a>（今天）：Kayra Cizmeci 提出一条 nit——v13 里改用 `cpumask_weight()` 计数的改动没有写进 commit message。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-012-sched-cputime-add-kcpustat-field-total-helper.html">sched-20260904-012</a>）steal_governor 的目标场景是超卖虚拟化的 vCPU 争抢：用 guest 看到的 steal time 量化争抢程度，而 steal time 的读取就是「在一组 CPU 上累加 `CPUTIME_STEAL`」。这类累加在内核里已手写两处（s390 `hd_calculate_steal_percentage()`、fs/proc/uptime.c），本片把重复模式提成公共 helper 供后续 patch 复用。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-012-sched-cputime-add-kcpustat-field-total-helper.html">sched-20260904-012</a>）`kcpustat_field_total()` 内部走既有 `kcpustat_field()` 逐 CPU 接口，`for_each_cpu` 累加；两个调用点改写——s390 侧 `steal = kcpustat_field_total(CPUTIME_STEAL, &hd_vmvl_cpumask)` + `cpus = cpumask_weight(&hd_vmvl_cpumask)`（计数与求和分开，不再顺手 `cpus++`），uptime 侧 `idle_nsec = kcpustat_field_total(CPUTIME_IDLE, cpu_possible_mask)`。v13 里 s390 计数从逐 CPU 自增改为 `cpumask_weight()` 是今天 nit 的对象。

## 版本演进与当前进展

- v9→v10：本片首次出现（Yury Norov 建议）。
- v11：s390 侧改用 `cpumask_weight()` 计数，规模 15 增 12 删，标签（两个 Reviewed-by）已带进 commit message。
- v12/v13：本片逻辑未再变。
- 09-26：Kayra Cizmeci（`<20260926073147.140907-1-kayracizmeci@gmail.com>`）指出「The cpumask_weight() change is not mentioned in the commit message」。

## Maintainer 意见与讨论焦点

今天唯一回帖来自 reviewer 而非维护者：**Kayra Cizmeci** 的 nit 只有一句话，要求 commit message 补记 `cpumask_weight()` 改动。无 NAK，此前 cputime 维护者 Frederic Weisbecker 的 Acked-by 与两个 Reviewed-by 仍有效。

## 合入评估

*likelihood=high*。本片是纯提取（+15/-12，无行为变化），三个标签（Acked-by + 两个 Reviewed-by）已齐，唯一新增项是一条 commit message 补记 nit。*blocking_issues*：commit message 需补记 `cpumask_weight()` 改动；合入仍与 13 片系列绑定（系列层入队 sched/core 未获 Peter 表态）。*next_action*：作者在 v14 的 commit message 补一行即可，无实质性障碍。

## 效果评估

无性能数据；等价替换，收益是「caller's code to be simpler and avoids duplication」，净增 3 行换掉两处手写循环。

## 我可以参与的点

- `review`：核对 `kcpustat_field_total()` 在 `CONFIG_VIRT_CPU_ACCOUNTING_GEN` 下与 s390 旧手写循环（`kcpustat_cpu().cpustat[]`）的等价性——这条只在头文件层面就能核实，发现不一致可直接回帖。

## 参考链接

- Kayra 的 nit: https://lore.kernel.org/all/20260926073147.140907-1-kayracizmeci@gmail.com/
- v13 本片 (01/13): https://lore.kernel.org/all/20260909135617.871006-2-sshegde@linux.ibm.com/
- 前文分析: https://lore.kernel.org/all/20260903063240.268775-2-sshegde@linux.ibm.com/
