# sched/core: Try to use a preferred CPU in is_cpu_allowed

## TL;DR

本文为增量更新（早期完整背景见 sched-20260810-008）。Shrikanth Hegde 的 preferred-CPU / steal-governor 系列 v11 里，`05/12` 的 `task_can_sched_on_preferred()` 要在"任务亲和 ∩ preferred 掩码 ∩ 该任务可能的 CPU 集合"三者里判断有无交集：8/28 Dietmar Eggemann 为了 32 位 EL0 任务的 `execve()` 窗口提出改用三路 `cpumask_first_and_and()`、Vincent Guittot `+1`、作者承诺放进 v12；**8/30 Yury Norov 接着提两点反对——建议换成语义更清楚的 `cpumask_intersects_and()` helper，并明确"不喜欢这个补丁玩 `likely()`"**：`possible == task_possible` 在 x86 上确实 likely，但在 aarch64 的 el0-32 任务上永远 unlikely，会导致 aarch64 上代码生成变差。这条与 cpuset/亲和性直接交叉，且涉及 cpumask helper 的收口，值得跟。

## 背景与问题

- **机制前提**（本系列引入）：任务可以带一组 preferred CPU（服务于 steal-time 驱动的 vCPU 摆放）。当任务当前 CPU 不允许它运行时，兜底选点要尽量落在 preferred CPU 上——`is_cpu_allowed()`/`select_fallback_rq()` 这条路径即为此服务。
- **本补丁要判的是**："这个任务在这组 CPU 里到底有没有一个既能跑（`task_cpu_possible_mask(p)`）、又在亲和集合内、又被标为 preferred 的 CPU"。
- **为什么 8/28 之前它是两路交集**：Dietmar 指出 arm64 上有一类任务（`allow_mismatched_32bit_el0` 下的 32 位 EL0 任务）**可能的 CPU 集合比机器小**，且 `execve()` 期间存在一个窗口——在 `arch_setup_new_exec()` 调 `force_compatible_cpus_allowed_ptr()` 收窄亲和之前，`p->cpus_ptr` 与 `task_cpu_possible_mask(p)` 不一致，只用 `cpumask_intersects(p->cpus_ptr, cpu_preferred_mask)` 会得出错误的"能跑"结论。所以要三路求交。

## 技术方案

当前（作者 8/28 承诺进 v12）的实现：

```c
static inline bool task_can_sched_on_preferred(int cpu, struct task_struct *p)
{
	if (cpu_preferred(cpu))
		return false;

	/* Only FAIR tasks honor preferred CPU state */
	if (unlikely(p->sched_class != &fair_sched_class))
		return false;

	/* Ignore preferred state if task affinity is changing */
	if (unlikely(!cpumask_test_cpu(task_cpu(p), p->cpus_ptr)))
		return false;

	return cpumask_first_and_and(p->cpus_ptr, cpu_preferred_mask,
				     task_cpu_possible_mask(p)) < nr_cpu_ids;
}
```

即：用 `cpumask_first_and_and()` 的返回值是否 `< nr_cpu_ids` 表达"三个掩码存在交集"。

**8/30 Yury Norov 的替代方案与取舍**（本日新增）：

- 认同 `cpumask_first_and_and()` 比原来的 for 循环更有效，但建议**引入新 helper 表达意图**：
  `return cpumask_intersects_and(p->cpus_ptr, cpu_preferred_mask, task_cpu_possible_mask(p));`
  理由是"我们找的是交集，就该调用一个名字里带 intersects 的函数"。
- 同时他诚实指出**自己这个方案也有代价**：仍然要（可能不必要地）遍历 `cpu_possible_mask`。
- 对 `likely()` 的使用提出反对（见下节），并给出兜底选项：如果 `task_can_sched_on_preferred()` 真是性能关键路径，可以造一个 `arch_task_can_sched_on_preferred()` 来绕开这个通用判断。

被放弃的备选：Dietmar 原来的 `cpumask_intersects(p->cpus_ptr, cpu_preferred_mask)` 两路求交（因 32 位 EL0 窗口被否）。

## 版本演进与当前进展

- 8/25：v11（12 补丁）发出，`05/12` 即本条。
- 8/28：Dietmar 提出三路交集 + 指出 arm64 el0-32 的 `execve()` 窗口并称"我再测一下"；Vincent Guittot `+1`（"This is the best way to check that there is a valid cpu"）；作者接受，给出上面的 v12 草案，并说"大概在 7.3-rc1 落地后发 v12"。
- 8/30（本日）：Yury Norov 追加 helper 命名与 `likely()` 两点意见。
- 当日无人回复 Yury；v12 尚未发出（后续 v12 于 9/3 出现，见 sched-20260903-002）。

## Maintainer 意见与讨论焦点

- **Dietmar Eggemann（arm64 视角）**：问题的提出者——三路求交是**正确性**要求（el0-32 任务可能 CPU 集合更小 + `execve()` 收窄亲和的窗口），并且他自称还要继续测。
- **Vincent Guittot**：明确站队三路求交，认为这是判断"存在有效 CPU"的最好写法。
- **Yury Norov（cpumask 侧）**：认可算法方向，但两个具体诉求——① 语义化 helper（`cpumask_intersects_and()`）；② "I don't like how this patch plays with likely() macro. Possible == task_possible condition is surely likely for x86, but is always unlikely for aarch64/el0-32 tasks. This would lead to suboptimal code generation on aarch64." 也就是**同一处 `likely()` 在两个架构上的假设相反**，写成通用 `likely` 就是拿 x86 的偏好换 aarch64 的代码生成质量。
- **未解决的分歧**：① 新 helper 要不要进 `linux/cpumask.h`（Yury 自己承认他的写法也要遍历 `cpu_possible_mask`，收益主要是可读性）；② 是否需要 `arch_task_can_sched_on_preferred()` 这个架构钩子——它会把"preferred CPU"这套语义扩散到架构代码里，属于设计取向问题，当日无人表态；③ Dietmar 说"让我再测测"的 el0-32 窗口，本日没有测试结论。

## 合入评估

**possible**。这条本身没有 NAK，且改法方向已由 Dietmar/Vincent/作者三方收敛（v12 会带三路求交），Yury 的两点属于"可接受但不阻塞"的代码质量意见；真正的风险在系列整体——这是个 12（将成 13）补丁、横跨 sched/core、fair、debug 与 steal_governor 的大系列，每轮 review 都会推动新版本，且作者自己把 v12 排在 7.3-rc1 之后。截至本日：`05/12` 无 `Reviewed-by`/`Acked-by`，未进 tip（未获取到）。

## 效果评估

无本日新增数据。系列早前给出的动机数据见 sched-20260810-008；本日的争论全部是**代码质量与架构取向**（正确性窗口、helper 命名、分支预测提示对代码生成的影响），没有人在测 `task_can_sched_on_preferred()` 的开销，Yury 关于"suboptimal code generation on aarch64"的判断也**没有给出反汇编或性能数字支撑**，属未验证的定性意见。

## 我可以参与的点

- **把 `likely()` 之争变成可测量的问题**：Yury 的说法目前无人验证。可以在 aarch64（尤其是带 el0-32 任务的配置）上对比 `likely/unlikely` 的不同放置对生成代码和 `select_fallback_rq()`/唤醒路径开销的影响，给出反汇编或微基准——这种意见最容易被直接采纳进 v12。
- **helper 归属**：`cpumask_intersects_and()` 是否值得进通用头，是 cpumask 维护者的活，但使用方的实测/需求表态会推动它；如果引入，其它子系统（如 cpuset 里多处三路求交）也是潜在受益者，可以一并提出。
- **cpuset 交叉影响值得盯**：`task_cpu_possible_mask(p)` 与 `p->cpus_ptr` 的关系，正是 cpuset 收窄亲和性时会改变的东西；`05/12` 的语义变化对"被 cpuset 限死的任务"行为有直接影响，可以在 v12 发出时按 cpuset 场景给一份 review。
- **回合判断**：本条属于系列的一个小改动，单独回合意义不大；如果 OLK-6.6 只做 preferred CPU 与亲和性交互的部分，需要先等 v12 定型与 `00/13` 封面里的整体动机被接受。

## 参考链接

- lore（8/30 Yury Norov 的两点意见）: https://lore.kernel.org/all/apMziCV_8y0xeIBT@yury/
- lore（8/28 Dietmar Eggemann 提出三路求交与 el0-32 窗口）: https://lore.kernel.org/all/8262d2f9-9f2f-4821-8497-991d7c8448a3@arm.com/
- lore（8/28 Vincent Guittot 表态 +1）: https://lore.kernel.org/all/CAKfTPtB27-eFXGG9GcXdm4=YLZy6-vQMAQqoCbHa5xZxA3YBpw@mail.gmail.com/
- lore（8/28 Shrikanth Hegde 承诺 v12 采纳）: https://lore.kernel.org/all/621386ee-7147-4110-a027-6f2f83b4f1cc@linux.ibm.com/
- lore（v11 05/12 补丁本体）: https://lore.kernel.org/all/20260825103855.721013-6-sshegde@linux.ibm.com/
- lore（v11 封面）: https://lore.kernel.org/all/20260825103855.721013-1-sshegde@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260830-004
date: '2026-08-30'
subject: "sched/core: Try to use a preferred CPU in is_cpu_allowed"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20260825103855.721013-1-sshegde@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/apMziCV_8y0xeIBT@yury/"
authors: [Shrikanth Hegde, Yury Norov, Dietmar Eggemann, Vincent Guittot]
maintainers_involved: [Dietmar Eggemann, Vincent Guittot, Yury Norov]
current_version: v11
patch_series:
  - version: v11
    msgid: "<20260825103855.721013-6-sshegde@linux.ibm.com>"
    date: 2026-08-25
    summary: "让 is_cpu_allowed()/select_fallback_rq() 在受限情况下优先挑选仍被允许的 preferred CPU；task_can_sched_on_preferred() 改为 cpus_ptr ∩ cpu_preferred_mask ∩ task_cpu_possible_mask 三路求交"
    review_outcome: "Dietmar 提出 el0-32 execve 窗口并给出三路求交、Vincent +1、作者承诺进 v12；8/30 Yury 建议改为 cpumask_intersects_and() helper 并反对补丁里对 likely() 的用法"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "v12 尚未发出（作者排在 7.3-rc1 之后），本日 Yury 的意见无人回应"
    - "是否引入 cpumask_intersects_and() 通用 helper 未定"
    - "是否需要 arch_task_can_sched_on_preferred() 架构钩子无人表态"
    - "el0-32 execve() 窗口 Dietmar 说还要继续测，无结论"
  next_action: "作者需在 v12 回应 Yury 的 helper 命名与 likely() 意见，并由社区提供 aarch64 侧的开销验证"
contribution_opportunities:
  - kind: discussion
    description: "在 aarch64 上验证 likely() 放置对 task_can_sched_on_preferred() 代码生成与开销的实际影响，回帖给出数据"
  - kind: review
    description: "从 cpuset 收窄亲和性的角度 review 三路求交语义，确认被 cpuset 限死的任务行为符合预期"
  - kind: extend
    description: "若引入 cpumask_intersects_and()，可推动其它子系统里同类三路求交一并收敛"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: [sched-20260810-008, sched-20260831-007, sched-20260903-002]
tags: [affinity, arm64]
---
