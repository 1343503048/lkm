---
id: sched-20260904-012
date: '2026-09-04'
subject: 'sched/cputime: Add kcpustat_field_total helper'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: 20260903063240.268775-1-sshegde@linux.ibm.com
lore_url: https://lore.kernel.org/all/20260903063240.268775-2-sshegde@linux.ibm.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: '2026-09-07'
authors:
- Shrikanth Hegde
maintainers_involved:
- Frederic Weisbecker
- Yury Norov
- Mete Durlu
patch_series:
- 'sched/cputime: Add kcpustat_field_total helper'
- 'cpumask: Introduce cpumask_intersects_and'
- 'sched/docs: Document cpu_preferred_mask and Preferred CPU concept'
- 'cpumask: Introduce cpu_preferred_mask'
- 'sysfs: Add preferred CPU file'
- 'sched/core: Try to use a preferred CPU in is_cpu_allowed'
- 'sched/fair: Load balance only among preferred CPUs'
- 'sched/core: Push current task from non preferred CPU'
- 'sched/debug: Add migration stats due to non preferred CPUs'
- 'virt: Introduce steal governor driver'
- 'virt/steal_governor: Add control knobs for handling steal values'
- 'virt/steal_governor: Implement steal_governor policy loop'
- 'virt/steal_governor: Enable the driver'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 第 1 片本身标签已齐（Acked-by + 两个 Reviewed-by），但合入路径与 13 片系列绑定
  - 缓存中未见 Peter Zijlstra / Ingo Molnar 对 v12 的回应，sched/core 排队 7.4 的请求尚未有人接
  - 系列引入新的 CPU 状态并介入 wakeup/tick/load-balance 三条热路径，作者本人请求先在 tip 树跑测试周期
  - 作者承认纯 CPU-time 负载可能小幅回归
  next_action: 等 Peter/Ingo 对 v12 表态；若需推动，可补一组 cpuset 绑核与非 preferred CPU 叠加的行为验证数据回帖。
contribution_opportunities:
- 验证 cpuset 绑定与 cpu_preferred_mask 相交/不相交时的任务落点是否遵守亲和契约
- 核对 kcpustat_field_total() 在 CONFIG_VIRT_CPU_ACCOUNTING_GEN 下与原 s390 手写循环的等价性
- 在 KVM/SPLPAR guest 上复现 steal 驱动的收缩-扩张行为并给出回归数据
- 排查内部树中 for_each_cpu 手工累加/求交模式，评估引用本 helper 与 cpumask_intersects_and 的可行性
source_email_count: 1
related_articles:
- sched-20260903-002
tags:
- sched/core
- sched/fair
- sched/cache
- topology
title: 'sched/cputime: Add kcpustat_field_total helper'
layout: article
---

## TL;DR

Shrikanth Hegde 的 steal_governor v12（13 补丁）第 1 片在 `include/linux/kernel_stat.h` 加了一个 `kcpustat_field_total(usage, cpus)`，把「按 cpumask 累加某类 cpu_usage_stat」这件事收成一个 inline，并立即替换 `arch/s390/kernel/hiperdispatch.c` 与 `fs/proc/uptime.c` 里两处手写循环；后续 steal governor 算 steal time 用的正是同一模式。本日 cputime 侧的 Frederic Weisbecker 给出 `Acked-by`，此前该片已有 Yury Norov 与 Mete Durlu 两个 `Reviewed-by`，1 号补丁本身已无门槛，剩下的问题是整个系列能否进 7.4。

## 背景与问题

系列的目标场景是超卖虚拟化：主机 pCPU 争抢时 hypervisor 会抢占 vCPU，若被抢占时正持锁或在 irq-off 段，前进性会整体塌陷，还有 cache/TLB 未命中与宿主机调度开销等隐藏成本。作者的做法是 guest 侧协作式「收缩」——把负载折到更少的 vCPU 上，从而降低对 pCPU 的需求。争抢程度用 guest 看到的 steal time 量化，而 steal time 的读取方式就是「在一组 CPU 上累加 `CPUTIME_STEAL`」。

这类累加在内核里已经至少手写实现了两处，模式完全相同：
- `arch/s390/kernel/hiperdispatch.c` 的 `hd_calculate_steal_percentage()`：`for_each_cpu(cpu, &hd_vmvl_cpumask) { steal += kcpustat_cpu(cpu).cpustat[CPUTIME_STEAL]; cpus++; }`
- `fs/proc/uptime.c`：`for_each_possible_cpu(i) idle_nsec += kcpustat_field(CPUTIME_IDLE, i);`

所以第 1 片不是新功能，而是把重复模式提取为公共 helper，让后续 patch 直接复用（commit message：`"This allows the caller's code to be simpler and avoids duplication. For example, subsequent patch in the steal governor use this exact same pattern when calculating steal time."`）。这一片是 `Suggested-by: Yury Norov`，最早在 v9→v10 的 changelog 里作为一条独立改动引入。

## 技术方案

- 在 `include/linux/kernel_stat.h` 新增：

```
static inline u64 kcpustat_field_total(enum cpu_usage_stat usage, const struct cpumask *cpus)
{
	u64 total = 0;
	int cpu;

	for_each_cpu(cpu, cpus)
		total += kcpustat_field(usage, cpu);

	return total;
}
```

- 累加走已有的 `kcpustat_field()` 逐 CPU 接口，而不是像 s390 旧代码那样直接取 `kcpustat_cpu(cpu).cpustat[...]`；helper 放在 `#endif /* !CONFIG_VIRT_CPU_ACCOUNTING_GEN */` 之后，因此在所有配置下都可见（`kcpustat_cpu_fetch()` 那类受配置门控的接口只在其之前）。
- 两个调用点改写：`hd_calculate_steal_percentage()` 变成 `steal = kcpustat_field_total(CPUTIME_STEAL, &hd_vmvl_cpumask)` + `cpus = cpumask_weight(&hd_vmvl_cpumask)`（计数与求和分开，循环里不再顺手 `cpus++`）；`fs/proc/uptime.c` 变成 `idle_nsec = kcpustat_field_total(CPUTIME_IDLE, cpu_possible_mask)`。
- 规模：3 文件 15 增 12 删（`kernel_stat.h +11`、s390 `+3/-7`、proc/uptime `+1/-5`），无行为变化。

## 版本演进与当前进展

- v9→v10：`"Introduce kcpustat_field_total helper. (Yury Norov)"` —— 本片首次出现。
- v10（08-13/08-14）：Yury Norov 给 `Reviewed-by`，Mete Durlu 给 `Reviewed-by`（原话 `"FWIW, feel free to add my r-b to this patch"`）。此时 diffstat 为 14 增 11 删，s390 侧仍保留 `int cpus, cpu;`。
- v11（08-25）：changelog 记 `"Collected tags for patch 1"`，s390 改写为用 `cpumask_weight()` 计数，规模变为 15 增 12 删，此后未再变。
- v12（09-03，13 补丁）：本片的两个 `Reviewed-by` 已带在 commit message 中；v11→v12 的改动集中在别处（arm64 32-bit 任务 `p->cpus_ptr` 含架构上不可能 CPU 的情形简化、为此引入 `cpumask_intersects_and`、暂不做 arch Kconfig 门控）。
- 09-04 00:26 Frederic Weisbecker 在该片上给出 `Acked-by`。本日按 subject 匹配到 1 封邮件。

## Maintainer 意见与讨论焦点

**Frederic Weisbecker（cputime/vtime 侧维护者，09-04 00:26）**：整封正文只有一行 `"Acked-by: Frederic Weisbecker <frederic@kernel.org>"` —— 无条件通过，没有附带任何修改要求。对第 1 片来说这就是它需要的子系统放行票。

**Yury Norov**：既是需求来源（`Suggested-by: yury.norov@gmail.com`）也是评审人（`Reviewed-by: ynorov@nvidia.com`，v10 起）。**Mete Durlu**：`Reviewed-by`（v10 起）。

**讨论焦点**：本片的争议面已经为零，真正的门在系列层。封面直接对 Peter Zijlstra / Ingo Molnar 提出：`"Could this series be considered for queuing in sched/core, targeting inclusion in 7.4?"`，并主动请求 `"The feature could also benefit from a good testing cycle in the tip tree."`；作者自评已收敛（`"I believe the series has now converged and is ready for merge consideration"`），同时承认存在回归面（`"It may regress slightly for pure CPU-time workloads"`）。也就是说，第 1 片能否落地取决于调度器核心维护者是否接受这套 `cpu_preferred_mask` 机制——它引入一个新的 CPU 状态（严格作为 `cpu_active_mask` 子集）、在三条路径上生效（wakeup 的 `is_cpu_allowed()` → `select_fallback_rq`、`sched_tick()` 里用 stopper 把当前任务推走、`sched_balance_rq` 把 domain span 限制到 preferred mask），外加一个新驱动 `drivers/virt/steal_governor.c`（296 行）与 sysfs ABI。

## 合入评估

likelihood: **likely**。

依据（就第 1 片本身）：三个必要标签齐了——cputime 维护者 `Acked-by`、两名 reviewer `Reviewed-by`、且它是纯提取（+15/-12，无行为改变），同时还顺手简化了 s390 与 `/proc/uptime` 两处既有代码；这类基础 helper 通常不会被打回。

卡点：
- 本片的实际合入路径与系列绑定：作者请求把它作为 13 片系列的第一片排进 `sched/core` 面向 7.4，缓存中未见 Peter Zijlstra 或 Ingo Molnar 对 v12 的任何回应，因此「helper 单独先走」这条更短路径没有任何邮件证据支持。
- 系列层的不确定性会传导：新 CPU 状态介入 wakeup / tick / load balance 三条热路径，加上新驱动与 ABI，需要调度器核心维护者的明确接纳；作者自己也把「好的测试周期」当作请求项提了出来。
- v12 之前已经走了 12 轮，封面列出的合入后待办（arch 特定接口、测试框架）说明设计上仍有未定项。

## 效果评估

第 1 片本身在邮件中未提供效果数据，也不需要——它是等价替换，作者给的唯一收益是「caller's code to be simpler and avoids duplication」，规模上净增 3 行换掉两处手写循环。性能数据属于整个系列，且只在封面出现：PowerPC SPLPAR（50 核 SMT8、两台 VM 跑同一负载、默认参数 1000ms / 低阈 200 / 高阈 500）的 hackbench 表格随负载组数增大收益变大，x86（cascade-lake）与 s390（z16）以 ΔRPS 表格给出，正负都有；作者自述结论是 `"It performs well for real-life workloads on PowerPC, and earlier KVM testing also showed improvements on s390 and x86"`、`"Overhead of steal_governor looks minimal when there is no steal time"`、以及 `"Pure CPU-time workloads may see a small regression"`。封面表格的列含义（baseline / steal_governor disabled / enabled）与百分比基准未逐字解释，引用具体百分比前需再核对。

## 我可以参与的点

- **与 cpuset/cgroup 最直接的接口**：Layer A 的设计约束原文是 `"The scheduler strictly respects user affinities. If a task is pinned exclusively to non-preferred CPUs, it will remain there."` 但同一套机制会在 `is_cpu_allowed()` 里因为 CPU 非 preferred 而走 `select_fallback_rq`，还会在 `sched_tick()` 里用 stopper 把当前任务推走。cpuset 绑定与 preferred 子集相交/不相交时的实际行为、以及 `cpu_preferred_mask ⊂ cpu_active_mask` 与 cpuset 的 `cpuset.cpu_exclusive`、isolcpus/nohz_full 的叠加语义，正是该系列最值得被 review 的地方，也是作者明确请求「在 tip 树上跑一轮测试」的靶心。这是可以直接转化为一次带数据的回帖的方向（在 SPLPAR 或 KVM guest 上跑一组绑核/非绑核混合负载，观察是否有任务被留在非 preferred CPU 上）。
- **helper 语义的一个待核对点**：累加改走 `kcpustat_field()` 而 s390 旧代码用 `kcpustat_cpu().cpustat[]`，两者在 `CONFIG_VIRT_CPU_ACCOUNTING_GEN` 下的等价性本邮件未展开；header 里 helper 恰好被放在 `#endif /* !CONFIG_VIRT_CPU_ACCOUNTING_GEN */` 之后，说明它要依赖 `kcpustat_field()` 在全部配置下可用。这是一条只看头文件就能核实、且核实后如有问题可直接回帖的低门槛参与点。
- **抽象本身的延伸空间**：`cpumask_intersects_and`（v12 新增，Yury Norov 提）与本 helper 都指向同一件事——「cpumask 聚合运算」的标准库化。若内部树有大量 `for_each_cpu` + 累加/求交的开放编码，这两个补丁是可引用的上游判例。
- **回合判断**：第 1 片对 OLK-6.6 是独立可回合的小改动（只碰 `include/linux/kernel_stat.h` 与两个调用点），价值在于为内部 steal-time 相关策略提供统一入口；但 Layer A 的 preferred CPU 机制牵动 wakeup/tick/load-balance 三处热路径，属结构性变更，不建议在系列未合入主线前自行预回合。

## 参考链接

- 邮件线程：
  - v12 00/13 封面（steal_governor 系列）: <https://lore.kernel.org/all/20260903063240.268775-1-sshegde@linux.ibm.com/>
  - v12 01/13 本片: <https://lore.kernel.org/all/20260903063240.268775-2-sshegde@linux.ibm.com/>
  - Frederic Weisbecker 的 Acked-by: <https://lore.kernel.org/all/apmfne3iBct7oNTp@localhost.localdomain/>
  - v11 01/12（标签首次收集）: <https://lore.kernel.org/all/20260825103855.721013-2-sshegde@linux.ibm.com/>
- 相关文章/系列：
  - [[sched-20260903-002]] steal_governor v12 偏好 CPU + vCPU 回退。
- 相关代码/commit：
  - `include/linux/kernel_stat.h` `kcpustat_field_total()` / `kcpustat_field()`
  - `arch/s390/kernel/hiperdispatch.c` `hd_calculate_steal_percentage()`
  - `fs/proc/uptime.c` `uptime_proc_show()`
