---
id: sched-20260909-007
date: '2026-09-09'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260909062649.469633-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v5
generated_at: '2026-09-10T00:45:00'
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Will Deacon
- K Prateek Nayak
- Vincent Guittot
- Dietmar Eggemann
- Srikar Dronamraju
patch_series:
- version: v2
  msgid: <20260904091838.3617894-1-arighi@nvidia.com>
  date: '2026-09-04'
  summary: 澄清通用改动同样覆盖 POWER7；sched_smt_asym_prefer() 简化为直接检查最低层调度域（Dietmar Eggemann）。
  review_outcome: 两条意见均已采纳。
- version: v3
  msgid: <20260907163513.4172411-1-arighi@nvidia.com>
  date: '2026-09-07'
  summary: 把 SMT 优先级调整收口到 select_idle_sibling() 中已选出 idle 候选之后；检查折进 select_idle_smt_priority()
    并直接扫调度域 span（K Prateek Nayak）。
  review_outcome: Prateek 认可收口位置，后续建议进一步整合进慢路径。
- version: v4
  msgid: <20260908082345.103087-1-arighi@nvidia.com>
  date: '2026-09-08'
  summary: 慢路径同样遵守 sibling 优先级；helper 改名 select_idle_smt_cpu()（Srikar Dronamraju）。
  review_outcome: Srikar 给出 Reviewed-by；Prateek 建议进一步用 group_asym_packing 整合进 sched_balance_find_dst_cpu()，作者以分类排序与
    local-vs-idlest 比较两处语义问题反驳。
- version: v5
  msgid: <20260909062649.469633-1-arighi@nvidia.com>
  date: '2026-09-09'
  summary: 仅删除冗余的 olympus_prefer_pe0 状态（K Prateek Nayak）。diffstat 6 files changed,
    163 insertions(+), 17 deletions(-)，含 arch/arm64 三处改动。
  review_outcome: Prateek 给出 Reviewed-by+Tested-by（4th gen EPYC 与 128C Ampere ARM
    服务器无性能影响）；Peter Zijlstra tentatively picked up 但要求 arm64 ack；Will Deacon 以 MIDR
    检测拓扑不可接受为由拒绝；Vincent Guittot 认可调度器侧但质疑新增 static key。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Will Deacon 明确 NAK 架构侧：按 MIDR 匹配判定 SMT 拓扑优先级是 non-starter，arm64 上缺少可用的启用途径
  - Peter Zijlstra 的收取前提是本系列拿到 arm64 ack，因此 1/2 的阻塞会连带卡住整组
  - Vincent Guittot 质疑为子特性新增 static key，主张要么去掉、要么改为整个 asym_packing 一个 key；作者自陈未测过该
    key 节省是否显著，此分歧当日未解决
  - '1/2（arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores）正文不在当天邮件缓存内，架构侧实现细节未获取到'
  next_action: 提出非 MIDR 的 arm64 优先级来源（固件/ACPI/DT 描述）；明确 2/2 是否可先独立进入 tip；收敛 static
    key 之争（实测唤醒路径开销或按 Vincent 建议合并为整特性 key）
contribution_opportunities:
- kind: review
  description: 给出 arm64 侧不以 MIDR 判定的 SMT 线程优先级机制（固件/ACPI PPTT 或既有属性），这是目前唯一硬阻塞且邮件里无人提出替代方案
- kind: extend
  description: 实现 Prateek 与 Andrea 都推到 later 的那条：在 group_has_spare 内以 SMT 优先级作为等价可用
    sibling 之间的 tie-breaker，并保持 local-vs-idlest 比较与 choose_idle_cpu() 语义
- kind: testing
  description: 在对称 SMT 机器上实测保留新 static key 与改用 sched_smt_active() 两种写法的唤醒路径开销，为 Vincent
    的质疑补上作者自陈缺失的那个数字
- kind: testing
  description: 补 ppc64/POWER7 或任何已有 SD_ASYM_PACKING SMT 域平台的实测，当天全部数据都来自 aarch64 Vera
    与 x86，ppc64 侧为零
- kind: discussion
  description: 就 2/2 能否在 1/2 重做期间先行合入向 Peter/Will 明确提出问题，Prateek 的 x86+ARM 无性能影响数据正是该论点的现成证据
source_email_count: 15
related_articles:
- sched-20260908-002
- sched-20260907-005
- sched-20260904-002
- sched-20260903-009
tags:
- cfs
- idle
- topology
- arm64
- hyperthreading
- perf
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

## TL;DR

本文为增量更新，v1..v4 的动机与完整代码分析见 related_articles 中的 sched-20260908-002 / sched-20260907-005 / sched-20260904-002 / sched-20260903-009。09-09 是这个系列**最接近落地也最接近卡死**的一天：Andrea Righi 在几小时内连发 v4→v5，拿到 Prateek Nayak 的 `Reviewed-by`+`Tested-by`，按 Dietmar Eggemann 的要求补上了 OpenBLAS 公开基准（+3.20% 吞吐、ST→SMT 模式切换次数 -80.5%），Peter Zijlstra 21:14 说「I tentatively picked these up」——然后 22 分钟后 Will Deacon 以「Detecting topology based on MIDR is a non-starter, sorry」把 arm64 那一半直接否掉。调度器侧现在有人背书，arm64 侧被明确拒了。

## 背景与问题

NVIDIA Olympus 的 SMT 是一个核两个对称 PE。只有一个 PE 活跃时核跑单线程模式、独占全部核资源；两个都活跃时进入双线程模式共享资源。Olympus 的特殊之处是**从双线程回到单线程不是即时的**：cover letter 引了 `293f9611ae735 ("sched/fair: Prefer fully idle cores for NOHZ balancing")` 里那段描述——在 Vera 系统上，兄弟核进入 WFI 之后还要持续空闲一个 qualification interval（10K 个 cycle）才恢复完整单线程性能。

那次改动挡住了 NOHZ 空闲负载均衡去唤醒忙 PE 的兄弟，但**普通任务放置**仍然可能选中一个空闲核的任意一个 sibling，反复切换活跃 PE 会让核停留在双线程模式，而两个 sibling 之间其实几乎没有有用的重叠。

这不是 Olympus 独有的形状：POWER7 也在共享容量的 SMT 层用 `SD_ASYM_PACKING` 给硬件线程排序，而 idle selection 从不参考这个顺序。

## 技术方案

两半。**调度器侧（2/2）**在 `select_idle_sibling()` 里加一个统一的收口点：候选 CPU 与核已经按原有的放置/容量规则选完之后，再用 `select_idle_smt_cpu()` 在该核内改指向优先级最高的可用 sibling：

```c
static inline int select_idle_smt_cpu(struct task_struct *p, int cpu)
{
	...
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

`select_idle_sibling()` 里原先五处直接 `return`（target、prev、`prev == smp_processor_id()` 的快速路径、recent_used_cpu、以及慢路径）都改成 `target = X; goto select_smt_priority;`，即所有出口统一过一遍 sibling 修正。作者明确写了两个约束：一是**必须要求两个 CPU 共享该最低层的 sched_domain span**，因为 `isolcpus` 可能把同一硬件核的两个 sibling 切进不同的调度域；二是 `SD_ASYM_CPUCAPACITY`（不同物理核之间选容量）与 `SD_ASYM_PACKING`（选定核之后挑 sibling）两条序必须相互独立，不能混在一起判。

SMT2 的 Olympus 上，这只会改变**完全空闲核**上的选择（部分空闲核本来就只剩一个可用 CPU）；在 POWER7 这类宽 SMT 上，它会在核部分繁忙时按优先级顺序填 sibling。

**架构侧（1/2，`arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores`）**给 `arch/arm64` 补 `SD_ASYM_PACKING` 的 SMT 域。补丁正文不在当天邮件缓存里（当天只收到 cover 与 2/2），但 cover 的 diffstat 显示它落在 `arch/arm64/include/asm/topology.h`（+1）、`arch/arm64/kernel/smp.c`（+1）、`arch/arm64/kernel/topology.c`（+51），而 Will Deacon 的反对意见直接点明它是**按 MIDR 匹配来判定拓扑**。

关键设计取舍：PE0 与 PE1 稳态容量相等，偏好**不是**在指认一个更快的 PE，PE0 只是两个都可用时的规范选择。一致地选中同一个 sibling → 避免唤醒时反复换 PE → PE1 能更久保持空闲 → 更多核能留在（或回到）全资源单线程模式。通用行为只在体系结构提供了带 `SD_ASYM_PACKING` 的 SMT 域时才生效。

## 版本演进与当前进展

一天之内从 v4 走到 v5：

- **v1 → v2**：澄清通用改动同样覆盖 POWER7；把 `sched_smt_asym_prefer()` 简化成直接看最低层调度域（两条都来自 Dietmar Eggemann）。
- **v2 → v3**：把 SMT 优先的调整收口到 `select_idle_sibling()` 内、在已选出 idle 候选之后做；把 asym SMT 检查折进 `select_idle_smt_priority()` 并直接扫调度域 span（两条来自 Prateek Nayak）。
- **v3 → v4**（09-08 16:23）：慢路径也要遵守 sibling 优先级；合并后的 helper 改名为 `select_idle_smt_cpu()`（两条来自 Srikar Dronamraju）。
- **v4 → v5**（09-09 14:26，`<20260909062649.469633-1-arighi@nvidia.com>`）：只删掉冗余的 `olympus_prefer_pe0` 状态（Prateek 的意见）。作者自己在 14:36 承认「My replies failed to keep up with your speed on iterations :-)」。
- v5 的 2/2 已带 `Reviewed-by: Srikar Dronamraju`；14:36 Prateek Nayak 对整系列补上 `Reviewed-by` + `Tested-by`（说明 v5 与 v4 内容一致，他已在 4 代 EPYC 与一台 128C Ampere ARM 服务器上跑过，快速路径能正确内联进 `select_task_rq_fair()`，无性能影响）。
- 20:39 作者按 Dietmar 的要求补发公开基准与 PMU 数据（见效果评估）。
- 21:14 Peter Zijlstra：tentatively picked up，但需要 arm64 ack。23:36 Will Deacon 拒绝。

## Maintainer 意见与讨论焦点

**分歧一：arm64 侧怎么识别「这台机器的 SMT 有优先级」——这是当前的硬阻塞。** Will Deacon（arm64 维护者）23:36 的措辞没有任何余地："We've had five versions of this in five minutes, but the arch code is pretty filthy tbh. Detecting topology based on MIDR is a non-starter, sorry." 这不只是要改风格，而是要求换成固件/ACPI/DT 描述或别的非 MIDR 机制。Peter 的收取前提是「需要 arm64 ack」，所以这条意见直接决定系列能否合入。此外 Will 顺带点了迭代节奏（五版），暗示下一版应当先把架构侧的方案确定下来再重发。

**分歧二：要不要为这件事新增一个 static key。** Vincent Guittot 22:42："I wonder if it's worth creating a new static key. All other pieces related to asym packing use sched_smt_active() to opt out the related code. Other than that looks good to me" ——即调度器侧他认可，只质疑 `sched_smt_asym_active()`。Andrea 23:18 的理由是把额外的 `sd` 解引用与 flag 检查挡在唤醒路径之外：对称 SMT 系统上 `sched_smt_active()` 仍然是开的，新 key 让它们直接返回；不加的话多出来的成本大约是「两次有依赖关系的 load + 几个 flag 测试与分支」，缓存命中时可以忽略，但这是热路径、一次 cache miss 就会放大。他很明确地说了「我没有测过这个节省是否显著」，并表示如果维护者认为不值得，可以去掉改用 `sched_smt_active()`。Vincent 23:42 反驳："If we start having a static key per sub part of a feature like the asym packing, that can quickly become unmanageable. In this case we should better have a static key for whole asym_packing feature instead." ——**这一条到当天结束未解决**，且给出了一个具体的折中方向（为整个 asym_packing 特性做一个 key，而不是为子部分做 key）。

**已解决的分歧：慢路径要不要用 `group_asym_packing` 分类。** Prateek 03:40 提议把偏好整合进 `sched_balance_find_dst_cpu()`，在 `update_sg_wakeup_stats()` 里对 `SD_SHARE_CPUCAPACITY | SD_ASYM_PACKING` 域置 `sgs->group_asym_packing = 1`，并在 `update_pick_idlest()` 里为该类型返回 `sched_asym_prefer(idlest->asym_prefer_cpu, group->asym_prefer_cpu)`。Andrea 04:49 用了一段相当密的反驳：`group_asym_packing` 描述的是「应当把负载从该源组移走」，把一个 idle 的 SMT 组标成这个类型会让它排在**完全忙碌的组**之后——举例，SMT2 上的 fork 会把忙的本地 PE0 分类成 `group_has_spare`/`group_fully_busy`，而 idle 的 PE1 被强制成 `group_asym_packing`，`sched_balance_find_dst_group()` 就会认为忙组是更好的目标，把新任务叠到 PE0 上；另外 `update_pick_idlest()` 返回 true 表示「该用 @group 顶替 @idlest」，所以操作数还得反着写；即使都改了，local 与 idlest 两边同为 `group_asym_packing` 时比较仍返回 NULL，因此若慢路径先落在 idle 的 PE1 而 PE0 也 idle，它并不会切到 PE0。Prateek 14:32 认错接受："Probably needs a special case in group_has_spare instead of using group_asym_packing ... but we can always work on it later."

**被满足的要求：** Dietmar 15:20 质疑内部 GEMM 不可复核，要求改用 `OpenBLAS benchmark/sgemm.goto` 并给出预期跑法（`OMP_NUM_THREADS=88` + `numactl -C XXX --membind=0`）；作者 20:39 就补齐了 OpenBLAS 与内部 NVPL 两份数据。

## 合入评估

`likelihood=medium`。

- **调度器侧（2/2）已经足够干净**：Srikar `Reviewed-by`、Prateek `Reviewed-by`+`Tested-by`、Vincent「other than that looks good to me」、Peter 已 tentatively pick up。仅剩 static key 一个风格级争议，且 Vincent 给了折中方案。
- **架构侧（1/2）被明确 NAK**，而 Peter 的收取前提正是 arm64 ack。也就是说 2/2 依赖的「体系结构提供 SD_ASYM_PACKING 的 SMT 域」目前没有任何上游途径——arm64 上没人能开启这个特性。POWER7 侧不需要新代码（本来就有序），这也是为什么 Will 的拒绝是真阻塞而不是观感问题。
- 历史上这种「一半被 tip 收下、另一半被架构维护者打回」的系列，通常做法是拆开：调度器侧可以先行（如果它对所有现有 `SD_ASYM_PACKING` 用户无行为回归，Prateek 在 x86+ARM 服务器上的零影响数据正是这个论据），arm64 启用另开一条走 ACPI/固件描述。作者是否会这样拆，邮件里还没有信号。

`next_action`：需要一个非 MIDR 的 arm64 拓扑优先级来源（固件/ACPI DT 描述，或与 Will 商量别的机制），最好同时给出「2/2 单独先行、1/2 另议」的拆分意愿；并把 static key 之争按 Vincent 的建议收敛（要么去掉、要么做成整个 asym_packing 一个 key）。

## 效果评估

有本日报少见的完整数据。**注意作者自陈「这是 NVIDIA 内部 GEMM 与 OpenBLAS 两份，内核基线 7.3.0-rc2，88 线程绑 NUMA node 0（CPU 0-87,176-263），performance governor + cppc_cpufreq，5 次重复」**：

吞吐（delta = 打补丁 / mainline - 1，越高越好）：

| 负载 | 次数 | mainline TFLOP/s | 打补丁 TFLOP/s | Delta |
|---|---|---|---|---|
| OpenBLAS | 5/5 | 7.11876 ± 0.06734 | 7.34669 ± 0.01936 | **+3.20%** |
| NVPL（内部） | 5/5 | 9.64742 ± 0.17311 | 10.29695 ± 0.01786 | **+6.73%** |

PMU 侧的模式切换抖动（越低越好），OpenBLAS：ST→SMT 完成次数/次运行 10145.6 ± 1835.2 → 1981.6 ± 94.3（**-80.47%**）；SMT→ST 10342.6 → 1946.2（-81.18%）；ST→SMT 切换速率 845.5/s → 176.9/s（-79.08%）；ST→SMT 延迟周期/次运行 15.785M → 2.477M（-84.30%）。NVPL 同向但幅度略小（ST→SMT 完成 -72.17%，延迟周期 -77.64%）。

三点值得注意：一是**方差同时塌缩**（OpenBLAS 的标准差从 0.067 降到 0.019，NVPL 从 0.173 降到 0.018），这跟「consistent 落在 PE0」的机制解释是自洽的，比单纯一个平均数更有说服力；二是这组数据把收益从「吞吐」重新表述成了「模式切换抖动下降」，正是 Dietmar 想要验证的那件事；三是 cover letter 里先前提到的 9.4 → 10.1 TFLOP/s 是内部 GEMM 的旧数字，本轮的 9.65 → 10.30 是同一负载在新基线上的重测值，两者不必互相印证。

未覆盖的部分：没有异构 SMT 上常见的小核/大核混合负载数据，也没有 POWER7 上的验证（尽管作者反复强调通用性覆盖 POWER7），Srikar 只留了 `Reviewed-by`、没有给 ppc64 的实测。

## 我可以参与的点

- `review`：这是当天最缺人的地方——**arm64 侧的非 MIDR 方案**。如果手里有 Olympus/GB300 类机器或熟悉 arm64 拓扑与 ACPI PPTT/CPPC 描述，能提出一个「固件描述 SMT 线程优先级」的具体机制（或确认上游已有可复用的属性），就直接解掉了唯一硬阻塞。这个位置目前邮件里没有任何人给出方案。
- `extend`：`group_has_spare` 里的特化。Prateek 说「probably needs a special case in group_asym_packing → group_has_spare，we can always work on it later」，Andrea 也承认更深的整合「应保留正常的 group_has_spare 分类、只用 SMT 优先级作为等价可用 sibling 之间的 tie-breaker」。这条明确被双方推到「later」，也就是现在可以认领。
- `testing`：static key 之争的结论缺一个数字——作者自己说「haven't measured whether the saving is significant」。在对称 SMT 机器（普通 x86 桌面/服务器即可）上对比「保留新 key」与「改用 `sched_smt_active()`」两种写法下的唤醒路径开销（例如 schbench / pipe 唤醒延迟 + `perf stat`），可以直接给 Vincent 的问题提供决策依据。
- `testing`：补 POWER7 或任何 `SD_ASYM_PACKING` SMT 域的 ppc64 实测。作者反复声称覆盖 POWER7，但当天所有实测都在 aarch64 Vera 与 x86 EPYC/Ampere 上，ppc64 侧一个数据都没有。
- `discussion`：如果 Will 的拒绝意味着 1/2 需要重做成固件方案，那么 2/2 是否可以先独立进入 tip 是一个值得有人明确提问的问题（现有 `SD_ASYM_PACKING` 用户不会因此改变行为，Prateek 的双架构数据正好是这个论点的证据）。

## 参考链接

- v5 cover letter（含 v1..v5 完整 changelog）: https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/
- v5 2/2（`select_idle_smt_cpu()`，标题不带 v5 前缀）: https://lore.kernel.org/all/20260909062649.469633-3-arighi@nvidia.com/
- v5 1/2（arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores）: 当天邮箱未收到该封，正文与 msgid 未获取到
- Peter Zijlstra "I tentatively picked these up": https://lore.kernel.org/all/20260909131415.GB4120091@noisy.programming.kicks-ass.net/
- Will Deacon 的 NAK（MIDR 检测拓扑不可接受）: https://lore.kernel.org/all/aqF84So9WUQCDgsz@willie-the-truck/
- Prateek Nayak 的 group_asym_packing 集成提议: https://lore.kernel.org/all/ce287aa0-0079-4cfd-b330-6b7617f49e8a@amd.com/
- Andrea Righi 对该提议的反驳: https://lore.kernel.org/all/aqB05WpYBcZfIZYQ@gpd4/
- Prateek 认错并给出 Reviewed-by/Tested-by: https://lore.kernel.org/all/2abe03fa-63a3-4196-8869-f2372a5a13e7@amd.com/
- Dietmar Eggemann 要求公开基准: https://lore.kernel.org/all/c92baaa9-1c1a-4f1e-903e-7b98ec9f694c@arm.com/
- OpenBLAS/NVPL + PMU 数据: https://lore.kernel.org/all/aqFTbqOVW8ph3Bux@gpd4/
- Vincent Guittot 的 static key 质疑: https://lore.kernel.org/all/CAKfTPtAQh6ZndkHC+njYvX0hoDafaC+PX2EBfafDumTHvvgFcg@mail.gmail.com/
- Vincent 的后续（应为整个 asym_packing 做 key）: https://lore.kernel.org/all/CAKfTPtASXty5hOOgmXokCh95w0idU0y12UDua1_vg9m8teF9Rg@mail.gmail.com/
- v4 线程（本日 2/2 讨论所在线）: https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/
- tip-bot commit: 未获取到（Peter 仅口头 tentatively picked up，当天无 tip-bot 回帖）
- stable backport: 未获取到
