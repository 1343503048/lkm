# [BUG] cpuset: empty sched domain with isolcpus=domain, panic at CPU offline

## TL;DR

Mathieu Desnoyers 报告一个可复现的 panic：`isolcpus=domain` 启动时，cpuset 分区可以把所有 housekeeping CPU 拿走，顶层 cpuset 只剩启动时隔离的 CPU、生成空调度域，随后对 CPU 执行 offline 触发 `partition_sched_domains()` 越界读 `cpu_rq(NR_CPUS)->sd`，直接内核 panic。他附了根因分析与首行 scissors 线后的修复草案。游离在 `kernel/sched` 之外但与调度域强相关的 cpuset 边界缺陷，值得关注。

## 背景与问题

`isolcpus=domain` 启动时，某些 CPU 在启动时被隔离（HK_TYPE_DOMAIN_BOOT 之外）。cpuset 分区允许子分区的 root cpuset 把这些 housekeeping CPU 全部占走，顶层 cpuset 只剩下启动时隔离的 CPU。`generate_sched_domains()` 只按「effective_cpus 是否非空」决定是否保留 partition root，于是顶层 cpuset 用自己那份不含隔离 CPU 的 effective_cpus 参与 `cpumask_and`，得到一个**空调度域**：`build_sched_domains()` 在 `kernel/sched/topology.c:3111` 打 WARNING 却不构建任何 domain，但 `partition_sched_domains_locked()` 仍把这个空 mask 记进 `doms_cur`。到下一次 CPU offline，`cpuset_update_active_cpus()` 再次传入该空 domain，与 `doms_cur` 里的空 mask 匹配、走到 reuse 分支：

```c
int cpu = cpumask_first(doms_cur[j]);
guard(rcu)();
sd = rcu_dereference(cpu_rq(cpu)->sd);
```

空 mask 上 `cpumask_first()` 返回 `NR_CPUS`（本机 NR_CPUS=64），`cpu_rq(64)` 越界读到 `__per_cpu_offset[]` 末尾之后，`rq->sd` 加载触发 page fault，内核 panic（`cpuhp/2`，`partition_sched_domains+0x5ee`）。

复现（v7.4-rc1 与 tip sched/urgent `006991aa8997` 同源）：5 核 QEMU，`isolcpus=domain,0,1` 启动，cgroup v2 下把 CPU 4 放入 P（root 分区）、CPU 2-3 放入 Q（root 分区），再 `echo 0 > /sys/devices/system/cpu/cpu2/online` 即 panic。

## 技术方案

修复草案（scissors 线后，`kernel/cgroup/cpuset.c`）把「保留 partition root」的判据从「effective_cpus 非空」收紧为「effective_cpus 与 housekeeping mask 有交集」：

```c
 		if ((cp->partition_root_state == PRS_ROOT) &&
-		    !cpumask_empty(cp->effective_cpus))
+		    cpumask_intersects(cp->effective_cpus,
+				       housekeeping_cpumask(HK_TYPE_DOMAIN_BOOT)))
 			csa[ndoms++] = cp;
```

即只有 effective_cpus 里还留着 housekeeping CPU 的 partition root 才进入 `csa[]`，顶层 cpuset 若只剩隔离 CPU 就不为其构建（也是空的）调度域，从源头消除空 mask 进入 `doms_cur` 的可能。作者在分析中指明既有分区校验都拦不住该场景：`tasks_nocpu_error()` 看的是顶层 cpuset 仍持有 CPU 0、1 的 effective_cpus，`prstate_housekeeping_conflict()` 只把启动隔离 CPU 挡在 root 分区之外，没有任何一处要求顶层 cpuset 保留一个 housekeeping CPU。

## 版本演进与当前进展

*current_version: null（单封 [BUG] 报告 + 内嵌修复草案，无版本化补丁系列）*。

- 空 domain 源自 `9b496a8bbed9`（"cgroup/cpuset: Prevent leakage of isolated CPUs into sched domains"，v6.13）。
- reuse 越界分支源自 `a7660ce1590f`（"sched/cache: Fix has_multi_llcs iff at least one partition has multiple LLCs"，v7.2）。
- 当日刚发出，未获评审。

## Maintainer 意见与讨论焦点

当日无维护者回帖。作者是 housekeeping/cpuset 隔离这条线的资深贡献者，报告本身即附带根因与修复草案，且明确「The series does not change it」（与其 SCHED_DEADLINE 系列无关，是他测试该系列时撞上的独立问题）。潜在争议点：修复只堵住 `generate_sched_domains()` 的空 domain 生成，reuse 分支对空 mask 的 `cpumask_first()` 越界并未加防御——是否应当一并加固是后续讨论空间。

## 合入评估

*likelihood=medium*。根因清晰、复现可靠、修复最小，但当日无人评审，且改动落在 `kernel/cgroup/cpuset.c`（cpuset/cgroup 维护者 Waiman Long 的评审判定最终归属）。*blocking_issues*：① 无评审；② cpuset 分区与调度域重建的交互需 Waiman / sched 侧确认。*next_action*：等待 Waiman Long 与 sched 侧审阅，作者可考虑同步加 reuse 分支空 mask 防御。

## 效果评估

panic 为作者一次性实测触发（「I hit it once」），后续分析基于读代码，无修复后回归验证数据。`WARNING: kernel/sched/topology.c:3111` 与 `Oops: 0000 [#1] SMP NOPTI` 崩溃栈完整保留。

## 我可以参与的点

- **testing**：在 `isolcpus=domain` 平台（尤其 NR_CPUS ≤ BITS_PER_LONG 的配置）复跑 cpuset 分区抢占 housekeeping CPU + CPU offline 循环，验证修复后无空 domain、不 panic。
- **review**：核对「只查 `cpumask_intersects`」是否覆盖所有空 domain 生成路径（如 hotplug 路径 `top_cpuset_sd_nocpu` 相关），并判断 reuse 分支是否还需对空 mask 加防御性处理。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108145744.1532128-1-mathieu.desnoyers@efficios.com/
- 相关 commit: 9b496a8bbed9（空 domain 来源）、a7660ce1590f（reuse 越界分支）

---
id: sched-20261108-001
date: '2026-11-08'
subject: "[BUG] cpuset: empty sched domain with isolcpus=domain, panic at CPU offline"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<20261108145744.1532128-1-mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/20261108145744.1532128-1-mathieu.desnoyers@efficios.com/"
authors: ["Mathieu Desnoyers"]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "无评审"
    - "cpuset 与调度域重建交互需 Waiman / sched 侧确认"
  next_action: "等待 Waiman Long 与 sched 侧审阅，作者可考虑加固 reuse 分支空 mask 防御"
contribution_opportunities:
  - kind: testing
    description: "在 isolcpus=domain 平台复跑 cpuset 分区抢占 housekeeping CPU + CPU offline 循环，验证修复后不 panic"
  - kind: review
    description: "核对 cpumask_intersects 判据是否覆盖所有空 domain 生成路径，并评估 reuse 分支是否需要空 mask 防御"
generated_at: "2026-11-09T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [cgroup, topology, crash]
---