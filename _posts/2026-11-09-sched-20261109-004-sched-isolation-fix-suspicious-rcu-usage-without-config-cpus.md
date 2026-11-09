---
id: sched-20261109-004
date: '2026-11-09'
subject: 'sched/isolation: Fix suspicious RCU usage without CONFIG_CPUSETS'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261108185129.1549419-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261108185129.1549419-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Waiman Long
current_version: v1
patch_series:
- version: v1
  msgid: <20261108185129.1549419-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-09'
  summary: 无 CONFIG_CPUSETS 时 housekeeping_dereference_check() 放行所有读者
  review_outcome: Waiman Long Reviewed-by
upstream_commit: null
fixes_commit: 03ff73510169
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 sched/isolation 侧收取
contribution_opportunities:
- kind: testing
  description: 在 CONFIG_PROVE_RCU=y + CONFIG_CPUSETS=n + isolcpus=domain 配置下验证告警消失
- kind: review
  description: 核对 housekeeping_dereference_check() 是否还有其它会误触的调用路径
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261108-002
tags:
- affinity
- cgroup
- topology
title: 'sched/isolation: Fix suspicious RCU usage without CONFIG_CPUSETS'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-002-bug-sched-isolation-suspicious-rcu-usage-with-config-cpusets.html">sched-20261108-002</a>：Mathieu Desnoyers 报告 `CONFIG_CPUSETS=n` + `isolcpus=domain` 下读写 `/proc/sys/kernel/sched_rt_runtime_us` 触发 "suspicious RCU usage" lockdep 假阳性（误报），并附一行修复草案。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-004-sched-isolation-fix-suspicious-rcu-usage-without-config-cpus.html">sched-20261109-004</a>（今天）：**作者把草案落成正式补丁** `[PATCH] sched/isolation: Fix suspicious RCU usage without CONFIG_CPUSETS`——`Fixes: 03ff73510169`，无 CONFIG_CPUSETS 时 `housekeeping_dereference_check()` 放行所有读者；Waiman Long 已给 Reviewed-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-002-bug-sched-isolation-suspicious-rcu-usage-with-config-cpusets.html">sched-20261108-002</a>）自 `03ff73510169`（"cpuset: Update HK_TYPE_DOMAIN cpumask from cpuset"）起 cpuset 可在运行时改 HK_TYPE_DOMAIN mask，读者用 RCU，`housekeeping_dereference_check()` 只放行「持 CPU hotplug 写锁或 cpuset_mutex 的读者」。但 `CONFIG_CPUSETS=n` 时 mask 启动后不再变化，`rebuild_sched_domains()` 却只持 `cpus_read_lock()`，于是 `sched_rt_handler()` 每次读写 `sched_rt_period_us`/`sched_rt_runtime_us` 都打出 "suspicious RCU usage"（`kernel/sched/isolation.c:62`）。这是误报——仅需 `CONFIG_PROVE_RCU` + `isolcpus=domain`，属日志噪音，但会干扰「检查内核日志里 lockdep 报告」的测试。

## 技术方案

正式补丁把草案落地：在 `housekeeping_dereference_check()` 里加一条「无 cpuset 即放行」的早退——`!IS_ENABLED(CONFIG_CPUSETS)` 时直接返回 true，绕过 `rcu_dereference_all_check()`。语义安全依据：该指针仅在 cpuset 存在时能被 `housekeeping_update()` 改写，无 cpuset 时启动后恒定。补丁带完整 WARNING 堆栈、`Fixes: 03ff73510169`、Link 指向此前的 BUG 报告，并注明「developed with assistance from an LLM」。

## 版本演进与当前进展

*current_version: v1（2026-11-09，`<20261108185129.1549419-1-mathieu.desnoyers@efficios.com>`）*。作者将 20261108 的草案正式化为 v1 补丁，Waiman Long 给 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Waiman Long（cpuset/cgroup 维护者）**：Reviewed-by，无异议。
- 无 NAK、无未解决分歧。该 check 的贡献者（Mathieu）对自身代码的自纠，方向明确。

## 合入评估

*likelihood=high*。假阳性定位精确、修复一行且语义安全、已获 cpuset 维护者 Reviewed-by。*blocking_issues*：无阻塞项；因触发依赖 `CONFIG_PROVE_RCU=y` 且属日志噪音，优先级有限，可能随其它 isolation 修复一起收取。*next_action*：等 sched/isolation 侧（Peter/Ingo）收取。

## 效果评估

告警为 lockdep 误报，无功能/性能影响。作者在 VM（tip sched/urgent `006991aa8997`，`CONFIG_PROVE_RCU=y` + `CONFIG_CPUSETS=n`）稳定复现；无修复后量化数据。

## 我可以参与的点

- **testing**：在 `CONFIG_PROVE_RCU=y` + `CONFIG_CPUSETS=n` + `isolcpus=domain` 配置下读写 `sched_rt_runtime_us`，验证补丁后告警消失。
- **review**：核对 `housekeeping_dereference_check()` 是否还有其它「持 cpus_read_lock 但非写锁」的调用路径会误触。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108185129.1549419-1-mathieu.desnoyers@efficios.com/
