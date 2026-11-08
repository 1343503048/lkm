---
id: sched-20261108-002
date: '2026-11-08'
subject: '[BUG] sched/isolation: suspicious RCU usage with CONFIG_CPUSETS=n'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261108145931.1532447-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261108145931.1532447-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无评审
  - 非紧急，属日志噪音，可能随其它 isolation 修复收取
  next_action: 等待 sched/isolation 或 cpuset 侧确认后收取
contribution_opportunities:
- kind: testing
  description: 在 CONFIG_PROVE_RCU=y + CONFIG_CPUSETS=n + isolcpus=domain 下读写 sched_rt_runtime_us
    验证告警消失
- kind: review
  description: 核对 housekeeping_dereference_check 是否还有其它持读锁而非写锁的调用路径会误触
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cgroup
- topology
title: '[BUG] sched/isolation: suspicious RCU usage with CONFIG_CPUSETS=n'
layout: article
---

## TL;DR

Mathieu Desnoyers 报告一个 `CONFIG_CPUSETS=n` + `isolcpus=domain` 下的 lockdep 假阳性：读写 `/proc/sys/kernel/sched_rt_runtime_us` 时 `housekeeping_cpumask()` 的 `rcu_dereference_all_check()` 判定失败，打出 "suspicious RCU usage"。经分析这是误报（无 cpuset 时指针启动后不再变化），作者附了一行修复草案。低严重度、纯日志噪音问题。

## 背景与问题

`CONFIG_CPUSETS=n` 且 `isolcpus=domain`（1,2 或 1,2 均可，domain 是默认 flag）时，`cat /proc/sys/kernel/sched_rt_runtime_us` 触发 lockdep 告警，写同样触发。堆栈：`sched_rt_handler()` 每次读写都会调 `rebuild_sched_domains()`；无 CONFIG_CPUSETS 时它是 `include/linux/cpuset.h` 里的 stub，`guard(cpus_read_lock)` 后调 `partition_sched_domains(1, NULL, NULL)`。无 `doms_new` 时 `partition_sched_domains_locked()` 从 housekeeping mask 构建单个 domain：

```c
cpumask_and(doms_new[0], cpu_active_mask,
	    housekeeping_cpumask(HK_TYPE_DOMAIN));
```

`housekeeping_cpumask()` 用 `rcu_dereference_all_check()` 读 `housekeeping.cpumasks[HK_TYPE_DOMAIN]`，其检查函数 `housekeeping_dereference_check()` 三条放行条件里：`system_state` 未过调度初始化、CPU hotplug 写锁、cpuset 锁——调用方只持 `cpus_read_lock()`（读锁），无 RCU 读锁，且 cpuset 分支被编译掉，于是判定失败告警。作者确认这是误报：无 cpuset 时只有 `housekeeping_init()` 在启动时设过一次指针，之后不再变化；无 isolcpus 时 domain flag 未置，`housekeeping_cpumask()` 直接返回 `cpu_possible_mask` 不读指针，所以也无告警。

## 技术方案

修复草案（scissors 线后，`kernel/sched/isolation.c`）在 `housekeeping_dereference_check()` 里补一条「无 cpuset 即放行」的早退：

```c
 		if (system_state <= SYSTEM_SCHEDULING)
 			return true;
 
+		/* No cpuset, so the mask never changes after boot */
+		if (!IS_ENABLED(CONFIG_CPUSETS))
+			return true;
+
 		/* CPU hotplug write locked, so cpuset partition can't be overwritten */
 		if (IS_ENABLED(CONFIG_HOTPLUG_CPU) && lockdep_is_cpus_write_held())
 			return true;
```

与既有逻辑一致：该指针只在 cpuset 存在时可被 `housekeeping_update()` 改写，无 cpuset 时启动后恒定，绕过 `rcu_dereference_all_check()` 是安全的。

## 版本演进与当前进展

*current_version: null（单封 [BUG] 报告 + 内嵌修复草案）*。

- 该 check 来自 `03ff73510169`（"cpuset: Update HK_TYPE_DOMAIN cpumask from cpuset"，v7.0），tip sched/urgent 上同源。
- `666a32836c8f`（"sched/topology: Add a cpus_read_lock to rebuild_sched_domains()"，v7.3）曾修掉同一条读路径上的另一个告警——此前 stub 完全不持锁，故 v7.0–v7.2 也会告警。

## Maintainer 意见与讨论焦点

当日无维护者回帖。修复是作者（该 check 的贡献者之一）对自身代码的自纠，方向明确、无争议点；唯一可讨论的是否需要顺带把 `housekeeping_dereference_check()` 的三条放行条件进一步整理。

## 合入评估

*likelihood=medium*。假阳性定位精确、修复一行且语义安全，但当日无人评审；由于触发依赖 `CONFIG_PROVE_RCU=y` 且属日志噪音，优先级有限。*blocking_issues*：① 无评审；② 非紧急，可能随其它 isolation 修复一起收取。*next_action*：等待 sched/isolation 或 cpuset 侧确认后收取。

## 效果评估

告警为 lockdep 误报，无功能/性能影响。作者在 VM（tip sched/urgent `006991aa8997`，`CONFIG_PROVE_RCU=y` + `CONFIG_CPUSETS=n`）稳定复现，无修复后数据。

## 我可以参与的点

- **testing**：在 `CONFIG_PROVE_RCU=y` + `CONFIG_CPUSETS=n` + `isolcpus=domain` 配置下读写 `sched_rt_runtime_us`，验证修复后告警消失。
- **review**：核对 `housekeeping_dereference_check()` 是否还有其它「持 cpus_read_lock 但非写锁」的调用路径会误触。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108145931.1532447-1-mathieu.desnoyers@efficios.com/
- 相关 commit: 03ff73510169（check 来源）、666a32836c8f（同路径上一处修复）
