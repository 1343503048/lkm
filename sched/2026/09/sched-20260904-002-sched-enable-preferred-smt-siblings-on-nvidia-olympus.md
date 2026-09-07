# sched: Enable preferred SMT siblings on NVIDIA Olympus

## TL;DR

NVIDIA Olympus/Vera 用两个对称 PE 实现 SMT2，短暂激活空闲 sibling 会让核退回两线程模式，且回到单线程模式并非即时。Andrea Righi 的 v2（2 补丁）把 PE0 标成 preferred sibling（`SD_ASYM_PACKING`），并让 fair 调度器的全部空闲 CPU 选择路径尊重这个优先级，在 Vera 的 88 核 GEMM 上把约 9.4 TFLOP/s 提到约 10.1 TFLOP/s。Dietmar Eggemann 对 v1 的三条意见本日已逐条答复并发出 v2，等待下一轮 review。

## 背景与问题

Olympus 以两个对称 PE 实现 SMT：只有一个 PE 活跃时核运行在单线程模式、该 PE 可用全部核资源；两个 PE 都活跃则共享资源。问题在于 sibling 变空闲后，核不会立刻回到单线程模式——封面引用了 `293f9611ae735`（"sched/fair: Prefer fully idle cores for NOHZ balancing"）中的实测描述：ILB 退出、CPU 进 WFI 后，要等一个 qualification interval（在受测 Vera 上是 10 Ki cycles）才恢复完整单线程性能。`293f9611ae735` 只挡住了 NOHZ 空闲负载均衡器去唤醒 busy PE 的 sibling，普通任务放置仍可能选中一个空闲核的任一 sibling，反复切换活跃 PE 会把核长期留在两线程模式，而两个 sibling 之间几乎没有有效重叠。

需要澄清的是机制语义：PE0 与 PE1 稳态容量相同，偏好并不是在挑「更快的 PE」，只是在两个都可用时取一个规范化的固定选择，从而让 PE1 更长时间保持空闲、让更多核留在（或回到）满资源单线程模式。

同类问题并非 Olympus 独有：POWER7 也在 SMT 层使用 `SD_ASYM_PACKING` 排序硬件线程，这是 v2 明确扩大的适用范围。

## 技术方案

- 补丁 1/2 `arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores`：`arch/arm64/include/asm/topology.h`、`arch/arm64/kernel/smp.c`、`arch/arm64/kernel/topology.c`（+62 行）为 Olympus 拓扑设置 SMT 层 `SD_ASYM_PACKING` 优先级。
- 补丁 2/2 `sched/fair: Honor asymmetric SMT priority in idle selection`：新增 `sched_smt_asym_prefer()`、`__select_idle_smt_cpu()`、`select_idle_smt_cpu()`（由 `sched_smt_asym_active()` 静态分支门控）与 `select_idle_smt_priority()`；在已选中的空闲核内再挑最高优先级的可用 sibling。
- 接入点覆盖 `select_idle_core()`、`select_idle_smt()`、`select_idle_cpu()`（含 `__select_idle_cpu()` 命中后的两处）、`select_idle_capacity()`（`preferred_core` 快路径与最终 `best_cpu` 两处）、`select_idle_sibling()` 的 target / prev / `prev_aff` 三条快路径。
- 两个正确性约束：`sched_smt_asym_prefer()` 直接看最低层调度域（SMT 必为最低 SD，无需 `for_each_domain()`），但要求 `other` 落在 `sched_domain_span(sd)` 内，因为 `isolcpus` 可能把硬件 sibling 拆到不同调度域（与 `select_idle_smt()` 已有的同名检查同理）；物理核容量选择与 SMT sibling 排序解耦——`SD_ASYM_CPUCAPACITY` 先在不同最大容量的核之间选，`SD_ASYM_PACKING` 再在被选核内部选 sibling。
- 通用行为只在体系结构提供带 `SD_ASYM_PACKING` 的 SMT 域时生效。总规模 6 文件、176 行新增 / 9 行删除。

## 版本演进与当前进展

- v1（08-31，`20260831181800.1668646-1-arighi@nvidia.com`）：封面 + 2 补丁，未附 `arm64` 偏好的独立说明。
- 09-03 Dietmar Eggemann（ARM）复 v1 2/2，提三点意见（见下节）。
- v2（本日）：只有封面 `20260904091838.3617894-1-arighi@nvidia.com` 带 `[PATCH v2]` 标签，两个补丁仍以 `[PATCH 2/2]` 形式发出。Changes in v2 记两条：明确通用改动同样覆盖 POWER7；简化 `sched_smt_asym_prefer()` 为直接查最低调度域。第三条（`select_idle_smt()` 的 hook 对 SMT2 无意义）作者未删除，而是用 POWER7 SMT4 的场景论证保留。
- 本日匹配 3 封邮件：v2 封面、v2 2/2、作者对 Dietmar 的逐条回复。Dietmar 与 `arm64` 侧维护者对 v2 的再确认、以及 `select_idle_smt()` hook 是否保留的结论，缓存中尚未获取到。

## Maintainer 意见与讨论焦点

**Dietmar Eggemann（ARM，v1 的唯一实质 reviewer，09-03）**
1. 适用范围："I assume this sentence refers to Olympus/Vera and Power7?" —— 要求把描述里的影响面写清楚。
2. 实现：指出 `other` 似乎总在 mask 内，且 "SMT will always the lowest SD, so for_each_domain() is not necessary"，直接给出只用 `cpu_rq(cpu)->sd` + `(SD_SHARE_CPUCAPACITY | SD_ASYM_PACKING)` 判定后再调 `sched_asym_prefer()` 的简化版本。
3. 一处 hook 无意义："This one is weird for SMT2. AFAICS, select_idle_smt() is called when there are no idle cores. So if you find an idle CPU this is what you will return anyway. I guess your tests on Olympus/Vera do wakeups via select_idle_capacity() so you haven't touched this one."

**Andrea Righi（作者，本日 13:59 逐条答复）**
- 确认平台范围："Olympus/Vera is the platform motivating this series, but this is affecting POWER7 as well"，同意改写描述。
- 接受简化："Agreed, walking the domain hierarchy is unnecessary. I'll use the lowest domain directly."
- 但坚持保留 `sched_domain_span()` 检查，理由正是 isolcpus 可拆分 sibling，`select_idle_smt()` 已因同一原因有该检查。
- 对第 3 点：承认 "Correcdt for SMT2"（核部分空闲时只剩一个空闲 sibling，优先级查找返回同一 CPU），但论证 hook 仍有价值——POWER7 是 SMT4 + SMT 层 `SD_ASYM_PACKING`，核部分空闲时仍有多个空闲线程，否则 `select_idle_smt()` 会返回第一个空闲线程而非最高优先级的那个。
- 并直接确认测试路径假设成立："Vera also has SD_ASYM_CPUCAPACITY, so the scan path used by these tests is select_idle_capacity()."

**讨论焦点**：本系列真正的取舍不在 Olympus（SMT2 只在「全空闲核」上改变选择），而在 `SD_ASYM_PACKING` + 宽 SMT 平台（POWER7 SMT4）上的填充顺序；以及 `select_idle_sibling()` 三条快路径都插入一次 sibling 掩码遍历是否值得。缓存中未出现 Peter Zijlstra / Vincent Guittot 的表态。

## 合入评估

likelihood: **possible**。

依据：v2 已完整吸收 v1 唯一 reviewer（Dietmar Eggemann，ARM 拓扑侧）的意见并逐条回复，说明文字与实现都被修正；有明确的 Vera 实测收益数据；通用路径全部由 `sched_smt_asym_active()` / `SD_ASYM_PACKING` 门控，非对称 packing 平台零影响，回归风险可控。

卡点：
- v2 尚未拿到任何 Acked-by/Reviewed-by（本日缓存中无）；Dietmar 是否接受「SMT2 下无意义但为 POWER7 SMT4 保留 hook」这一论证还未见回帖。
- 需要 arm64 拓扑侧（Will Deacon / Catalin Marinas 方向）对 `arch/arm64/kernel/topology.c` 的 +62 行认可，缓存中未获取到任何 arm64 维护者回复。
- 改动横跨 `select_idle_*` 全部热路径，调度器维护者通常会要求额外的非对称容量平台（含小/big 混合）数据，目前只给了一个 GEMM 点位。

## 效果评估

邮件正文给出了具体数据（v2 封面）：在两台节点组成的 Vera 系统上，对 NUMA node 0 的 88 个物理核跑 88 线程单精度 GEMM。允许 workload 使用每个核的任一 sibling 时，吞吐从基线内核的约 9.4 TFLOP/s 提升到打上本系列后的约 10.1 TFLOP/s；重复运行的可预测性也变好，因为 workload 稳定落在 PE0、PE1 保持安静。

此外封面引用了 `293f9611ae735` 中的既有测量：受测 Vera 上 sibling 空闲后需 10 Ki cycles 的 qualification interval 才恢复完整单线程性能——这是本系列的动机量化依据。

未提供的数据：非 GEMM 负载（例如纯 CPU 时间型或带宽敏感型）的潜在代价、SMT4 平台（POWER7）上的实测、以及 `select_idle_*` 增加 sibling 遍历后的调度开销。

## 我可以参与的点

- **cpuset / isolcpus 交叉验证**：`select_idle_smt_priority()` 以 `p->cpus_ptr` 为可用掩码，`sched_smt_asym_prefer()` 又以 `sched_domain_span(sd)` 为界。cpuset 只放出一个核的一个 sibling、或使用 `isolcpus`/`cpuset` 把 sibling 拆到不同调度域时，正是这套边界条件所在。建议在「每核只放一个 sibling 进 cpuset」「整核独占」「isolcpus + 非对称 packing」三种配置下跑一轮 placement 断言，回帖给出结果——这是本系列里最容易由 cpuset 方向贡献的验证。
- **补非对称宽 SMT 数据**：Dietmar 与作者争论的 hook 只在 SMT4 以上有意义。若有 POWER 类环境，用 `select_idle_smt()` 可命中的负载（核部分空闲 + 多空闲线程）验证该分支是否真的改变放置，可直接结束这条争论。
- **补性能覆盖面**：GEMM 是高 FP 吞吐点。帮忙跑一组对 sibling 交替不敏感、但对调度开销敏感的基准（如 hackbench、单线程 spec），确认没有回退，会显著提高合入信心。
- **回合评估**：OLK-6.6 若尚未回合 `select_idle_capacity()` 的 `preferred_core` / `ASYM_IDLE_COMPLETE_MISFIT` 逻辑，本系列的接入点需重排；`sched_smt_asym_active()` 静态分支与 `cpu_ll_asym_core_lookup()` 类接口（`kernel/sched/topology.c` +36 行）是回合时的主要依赖，可先做依赖梳理。

## 参考链接

- 邮件线程：
  - v2 cover letter: <https://lore.kernel.org/all/20260904091838.3617894-1-arighi@nvidia.com/>
  - v2 2/2 `sched/fair: Honor asymmetric SMT priority in idle selection`: <https://lore.kernel.org/all/20260904091838.3617894-3-arighi@nvidia.com/>
  - 作者对 Dietmar Eggemann 的逐条回复: <https://lore.kernel.org/all/appeWCqxApU8NmuP@gpd4/>
  - v1 cover letter: <https://lore.kernel.org/all/20260831181800.1668646-1-arighi@nvidia.com/>
  - v1 2/2 补丁: <https://lore.kernel.org/all/20260831181800.1668646-3-arighi@nvidia.com/>
  - Dietmar Eggemann 对 v1 2/2 的评审: <https://lore.kernel.org/all/0d02e284-9a07-4f54-bf63-8edaa5e224e5@arm.com/>
- 相关文章/系列：
  - [[sched-20260903-009]] sched/fair 空闲选择尊重非对称 SMT 优先级（v1）。
- 相关代码/commit：
  - `kernel/sched/fair.c` `select_idle_core()` / `select_idle_smt()` / `select_idle_cpu()` / `select_idle_capacity()` / `select_idle_sibling()`
  - `kernel/sched/topology.c` `SD_ASYM_PACKING` 优先级查询
  - `293f9611ae735` ("sched/fair: Prefer fully idle cores for NOHZ balancing")

---
id: sched-20260904-002
date: '2026-09-04'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: 20260904091838.3617894-1-arighi@nvidia.com
lore_url: https://lore.kernel.org/all/20260904091838.3617894-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Andrea Righi
maintainers_involved:
- Dietmar Eggemann
patch_series:
- 'arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores'
- 'sched/fair: Honor asymmetric SMT priority in idle selection'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 尚未获得任何 Acked-by/Reviewed-by
  - Dietmar Eggemann 未确认 select_idle_smt() hook 为 POWER7 SMT4 保留的论证
  - 缓存中无 arm64 拓扑侧维护者对 arch/arm64/kernel/topology.c 改动的表态
  - 仅有一个 GEMM 性能点位，缺非对称容量平台的额外数据
  next_action: 等 Dietmar Eggemann 与 arm64 维护者对 v2 的回帖；若一周内无人再评，作者宜主动补一组非 GEMM 基准数据并 cc 调度器维护者。
contribution_opportunities:
- 在 cpuset 只放单 sibling / 整核独占 / isolcpus 拆分 sibling 三种配置下验证 placement 边界并回帖
- 提供 SMT4+ 非对称 packing 平台数据，判定 select_idle_smt() hook 是否真的改变放置
- 补跑 hackbench、单线程 spec 等对 sibling 交替不敏感的基准，确认无性能回退
- 梳理 OLK 回合所需的 select_idle_capacity()/preferred_core 与 topology.c 接口依赖
source_email_count: 3
related_articles:
- sched-20260903-009
tags:
- sched/fair
- topology
- affinity
---
