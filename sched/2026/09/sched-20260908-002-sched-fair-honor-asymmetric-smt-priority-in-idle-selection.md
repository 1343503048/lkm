# sched/fair: Honor asymmetric SMT priority in idle selection

## TL;DR

本文为增量更新，完整背景见 related_articles 中的 sched-20260907-005 / sched-20260904-002 / sched-20260903-009。09-08 这一天该系列连出两版：凌晨 00:30 的 v3 落实了 Prateek Nayak 的「收口到 `select_idle_sibling()`」建议，下午 16:23 的 v4 又按 Srikar Dronamraju 的意见补上唤醒慢路径并把 helper 改名为 `select_idle_smt_cpu()`，同时拿到 Srikar 的 `Reviewed-by`。一天两版且评审意见全部被吸收，推进速度很快；仍未解决的是 IBM 侧关于 SMT4 兄弟核 IPC 次序的追问和 arm64 拓扑侧的表态。

## 背景与问题

NVIDIA Olympus（Vera 平台）用两个对称 PE 实现 SMT：只有一个 PE 活跃时核心工作在单线程模式、该 PE 独占整核资源；两个 PE 都活跃时进入双线程模式共享资源。问题在于 Olympus 对「短暂唤醒兄弟 PE」特别敏感——按 cover 引用的 `293f9611ae735 ("sched/fair: Prefer fully idle cores for NOHZ balancing")`，ILB 结束、CPU 进入 WFI 之后，兄弟 PE 还要空闲一个 qualification interval（在实测 Vera 上是 10 Ki cycles）才恢复单线程满性能。`293f9611ae735` 只挡住了 NOHZ 空闲负载均衡唤醒兄弟，普通任务放置仍可能选到空闲核的任一兄弟，反复切换活跃 PE 会把核心长期钉在双线程模式。

POWER7 是同一类用户：`SD_ASYM_PACKING` 已在共享容量的 SMT 层给出硬件线程排序，但 idle CPU 选择从不参考它，任务可以落在任意兄弟上，直到负载均衡才纠正——而这个初始选择本身就足以让核心进不了偏好的低线程资源模式，造成"large and persistent performance loss"。

## 技术方案

两件事：arm64 侧把 PE0 标成 Olympus 的首选兄弟（通过 `SD_ASYM_PACKING`），sched 侧让 idle 选择路径尊重这个优先级。

v4 的收口方式是在 `select_idle_sibling()` 尾部加一个统一出口，所有能返回候选的分支都改成 `target = X; goto select_smt_priority;`：

```c
static inline int select_idle_smt_cpu(struct task_struct *p, int cpu)
{
	struct sched_domain *sd;
	int best = cpu;
	int sibling;

	if (!sched_smt_asym_active())
		return cpu;

	sd = rcu_dereference_all(cpu_rq(cpu)->sd);
	if (!sd || !(sd->flags & SD_SHARE_CPUCAPACITY) ||
	    !(sd->flags & SD_ASYM_PACKING))
		return cpu;

	for_each_cpu_and(sibling, sched_domain_span(sd), p->cpus_ptr) {
		if (sibling == best || !choose_idle_cpu(sibling, p))
			continue;

		if (sched_asym_prefer(sibling, best))
			best = sibling;
	}

	return best;
}
```

关键设计取舍：

- **只在核心已被选中之后重排兄弟**，不改物理核容量选择。commit log 明确"`SD_ASYM_CPUCAPACITY` 先在容量不同的核之间选，然后 `SD_ASYM_PACKING` 在选中的核内挑首选兄弟"，PE0/PE1 稳态容量相等，偏好不代表更快的 PE，只是把「同一核总落在同一兄弟」变成规范选择。
- **用 lowest sched domain 直接判**（v2 起按 Dietmar Eggemann 意见简化 `sched_smt_asym_prefer()`），但要求两个 CPU 共享该 domain 的 span，因为 `isolcpus` 可能把硬件兄弟拆到不同调度域。
- **用 static key 做零成本门控**：新增 `sched_smt_asym_packing`，在 `build_sched_domains()` 里靠新的 `has_asym_smt_domain()` 逐 CPU 探测后置位、在 `detach_destroy_domains()` 里对应递减——即只有架构真的提供带 `SD_ASYM_PACKING` 的 SMT 域才会走这段代码。
- v4 相对 v3 新增的位置是 `select_task_rq_fair()` 慢路径：

```c
	/* Slow path */
	if (unlikely(sd)) {
		new_cpu = sched_balance_find_dst_cpu(sd, p, cpu, prev_cpu, sd_flag);
		return select_idle_smt_cpu(p, new_cpu);
	}
```

## 版本演进与当前进展

- v1 2026-08-31 21:18（`<20260831181800.1668646-1-arighi@nvidia.com>`）；v2 2026-09-04（`<20260904091838.3617894-1-arighi@nvidia.com>`，按 Eggemann 意见简化判断并说明也覆盖 POWER7）。
- **09-08 00:30 v3**（`<20260907163513.4172411-1-arighi@nvidia.com>`）：把 SMT 优先级调整合并到 `select_idle_sibling()` 里、在选出 idle 候选之后统一处理；不对称 SMT 检查折进 `select_idle_smt_priority()` 并直接扫调度域 span（两条都是 Prateek Nayak 的意见）。fair.c 改动 79 行、整体 `+170/-15`。
- 09-08 00:48 Shrikanth Hegde 回帖（自述"我还没细看补丁"）：据他所记 POWER 四兄弟的 IPC 是 CPU0 > CPU1 > CPU2 > CPU4，不论忙闲——即"最高优先级兄弟"与"最快兄弟"是否等价这件事在宽 SMT 上需要证据。
- 09-08 13:37 Srikar Dronamraju 对 v2 的 2/2 给出实质意见并附 `Reviewed-by`：慢路径也要改（引他自己 2025-12-04 的 `<20251204175405.1511340-2-srikar@linux.ibm.com>`）；nit ①`__select_idle_smt_cpu()` 只有一处调用，就地内联；nit ②`select_idle_smt_priority` 直接叫 `select_idle_smt_cpu()`。"Otherwise looks good to me"。
- 09-08 14:12 Andrea 逐条接受，承诺 v4 内联并改名。
- **09-08 16:23 v4**（`<20260908082345.103087-1-arighi@nvidia.com>`）：Changes in v4 只列两条，都署 Srikar——慢路径（`WF_FORK`/`WF_EXEC` 一并覆盖）与改名。helper 已折叠（v4 中不再有 `__select_idle_smt_cpu`），fair.c 增到 85 行、整体 `+174/-17`，2/2 头部带 `Reviewed-by: Srikar Dronamraju <srikar@linux.ibm.com>`。
- 本日无 tip-bot、无 stable 回帖。

## Maintainer 意见与讨论焦点

- **Srikar Dronamraju（IBM，已给 RB）**：唯一提出功能性缺漏的人——慢路径漏改。他给出的参考是自己去年那版补丁，说明这条路径在 POWER 上确实会被走到；作者当日就采纳。剩余两条是风格 nit。
- **Shrikanth Hegde（IBM，问题未闭环）**：他提的是这套「按 `SD_ASYM_PACKING` 选首选兄弟」在 SMT4/SMT8 上的语义正确性前提。作者的模型是「PE0 与 PE1 等速，偏好只是规范化选择」，但 Shrikanth 指出的 POWER 上存在真实速度差，这两件事是否冲突、按 priority 选是否会系统性挑到更慢的兄弟，v3/v4 的 changelog 与正文都没有回应，v4 也没为此改任何东西。
- **K Prateek Nayak / Dietmar Eggemann**：本轮（09-08）没有新表态，他们 v2/v3 的意见均已被吸收。
- 无人 NAK；争议集中在「除 Olympus 单平台之外的收益与代价」，而不是实现正确性。

## 合入评估

`likelihood=medium`。有利面：一天两版且所有评审意见当场落地，IBM 侧（`SD_ASYM_PACKING` 的历史用户 POWER7）已经拿到一个 `Reviewed-by`，通用侧改动被 static key 完全门控、非 asym-SMT 平台零风险。卡点：其一，1/2 落在 `arch/arm64/{include/asm/topology.h,kernel/smp.c,kernel/topology.c}`，至今没有 arm64 拓扑维护者（Will Deacon / Sudeep Holla 等）表态，合入路由（sched 树还是 arm64 树）未定；其二，作者自报的收益仍是同一份数据（88 线程 SP GEMM，9.4 → 10.1 TFLOP/s），SMT4/SMT8 上多出来的兄弟扫描开销与收益无人量化，Shrikanth 的追问还挂着。`next_action`：需要 v5 或在 v4 线程里回应宽 SMT 的实测与 IPC 次序问题，并拉 arm64 侧对 `topology` 改动确认。

## 效果评估

- 邮件里唯一的量化数据仍是作者自报：两台两节点 Vera，88 线程单精度 GEMM 跑在 NUMA node 0 的 88 个物理核上，允许任务自由选择任一兄弟时，吞吐从基线约 **9.4 TFLOP/s** 提升到约 **10.1 TFLOP/s**（+7.4%），且重复运行更稳定——负载一致地落在 PE0、PE1 保持静默。该数据在 v3、v4 的 cover 中逐字重复，09-08 没有任何新增测量。
- Shrikanth 的 IPC 次序是"据我所记"（IIRC）的经验陈述，非测试数据；Srikar 的 RB 也未附带任何数字。
- 结论：收益目前只有单平台、单 workload、作者自测支撑，宽 SMT 下的额外 `for_each_cpu_and` 扫描开销无数据（属未验证）。

## 我可以参与的点

- `testing`：v4 缺的正是宽 SMT 数据。POWER SMT8（Shrikanth/Srikar 都在 IBM）或任何 `SD_ASYM_PACKING` SMT 域平台上，跑一组 wake-placement 类负载（pthread hackbench、多任务 ping-pong）对比 v4 前后，并记录 `perf stat -e ...` 或 IPC 分布，可直接回答 Shrikanth 的追问。
- `review`：v3 起内联后的候选集合从「扫描掩码」变成 `for_each_cpu_and(sibling, sched_domain_span(sd), p->cpus_ptr)` 且用 `choose_idle_cpu()` 过滤，与旧的 `select_idle_smt()` 语义是否严格等价值得逐条核对；另外 `detach_destroy_domains()` 里新增的 `has_asym_smt_domain()` 循环是在 `rcu_read_lock()` 下扫 `cpu_map`，与 `cpu_attach_domain()` 拆域时的 key 递减是否严格配对（尤其 `isolcpus`/分区改写调度域时），是可以独立提意见的点。
- `new_patch`：arm64 侧 1/2（`arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores`，+62 行在 `arch/arm64/kernel/topology.c`）如果自家有 arm64 平台需要同类偏好，可以基于它扩到别的 SoC 匹配表；回合到内部分支时注意 `Fixes` 要写自家 commit。

## 参考链接

- v3 cover: https://lore.kernel.org/all/20260907163513.4172411-1-arighi@nvidia.com/
- v3 2/2: https://lore.kernel.org/all/20260907163513.4172411-3-arighi@nvidia.com/
- v4 cover: https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/
- v4 2/2（带 Srikar Reviewed-by）: https://lore.kernel.org/all/20260908082345.103087-3-arighi@nvidia.com/
- Srikar Dronamraju 的评审与 RB: https://lore.kernel.org/all/ap-fELvfw5w51vbG@linux.ibm.com/
- Andrea 逐条回应: https://lore.kernel.org/all/ap-nQp-8zrOJQY4-@gpd4/
- Shrikanth Hegde 的 IPC 追问: https://lore.kernel.org/all/d75f3181-868b-442d-9f2a-b979af0833d4@linux.ibm.com/
- Srikar 去年 referenced 的慢路径补丁: https://lore.kernel.org/all/20251204175405.1511340-2-srikar@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260908-002
date: '2026-09-08'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260908082345.103087-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v4
generated_at: "2026-09-09T00:35:00"
authors:
- Andrea Righi
maintainers_involved:
- Srikar Dronamraju
- Shrikanth Hegde
patch_series:
- version: v1
  msgid: <20260831181800.1668646-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 初版：arm64 侧把 Olympus PE0 标为偏好兄弟，sched 侧在 idle 选择中引入 SD_ASYM_PACKING 排序。
  review_outcome: K Prateek Nayak 建议收口到单一位置，Dietmar Eggemann 要求简化判断并说明也覆盖 POWER7。
- version: v2
  msgid: <20260904091838.3617894-1-arighi@nvidia.com>
  date: '2026-09-04'
  summary: 按 Eggemann 意见直接检查最低调度域简化 sched_smt_asym_prefer()，并在 cover 中说明通用改动同样覆盖 POWER7。
  review_outcome: Srikar Dronamraju 指出 select_task_rq_fair() 慢路径未覆盖，并提两条命名/内联 nit，同时给出 Reviewed-by。
- version: v3
  msgid: <20260907163513.4172411-1-arighi@nvidia.com>
  date: '2026-09-08'
  summary: 把 SMT 优先级调整合并到 select_idle_sibling() 末尾统一出口，非对称检查折进 select_idle_smt_priority() 并直接扫调度域 span；fair.c 79 行、整体 +170/-15。
  review_outcome: '09-08 当天 Shrikanth Hegde 追问 SMT4 各兄弟 IPC 次序（CPU0>CPU1>CPU2>CPU4，自述未细看补丁）；Srikar 补提慢路径与改名/内联意见。'
- version: v4
  msgid: <20260908082345.103087-1-arighi@nvidia.com>
  date: '2026-09-08'
  summary: 按 Srikar 意见在唤醒慢路径也套用兄弟优先级（select_idle_smt_cpu() 包住 sched_balance_find_dst_cpu()），并把 helper 改名为 select_idle_smt_cpu()、内联 __select_idle_smt_cpu()；fair.c 85 行、整体 +174/-17。
  review_outcome: '2/2 携带 Reviewed-by: Srikar Dronamraju；Shrikanth 的宽 SMT IPC 问题仍未回应。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 1/2 落在 arch/arm64 拓扑代码，至今无 arm64 维护者表态，合入路由未定
  - 收益仍是作者单平台单 workload 自测（9.4 → 10.1 TFLOP/s），SMT4/SMT8 的额外兄弟扫描开销无数据
  - Shrikanth Hegde 关于最高优先级兄弟与最快兄弟是否等价的追问在 v3/v4 中都未回应
  next_action: 在 v4 线程回应宽 SMT 实测与 IPC 次序问题，并拉 arm64 拓扑维护者确认 1/2
contribution_opportunities:
- kind: testing
  description: 在 POWER SMT8 或任意带 SD_ASYM_PACKING SMT 域的平台跑 wake-placement 负载，量化 v4 前后放置稳定性与 IPC 分布，回答 Shrikanth 的未闭环问题
- kind: review
  description: 核对内联后候选集合改用 sched_domain_span(sd) ∩ p->cpus_ptr 是否与原 select_idle_smt() 严格等价，以及 detach_destroy_domains() 中新增 static key 递减与 build_sched_domains() 置位是否在所有域重建路径上配对
- kind: new_patch
  description: 基于 1/2 的 arm64 拓扑偏好机制，为其它需要规范选择同一 SMT 兄弟的平台扩展匹配表
source_email_count: 7
related_articles:
- sched-20260907-005
- sched-20260904-002
- sched-20260903-009
tags:
- cfs
- idle
- hyperthreading
- topology
- perf
- arm64
---
