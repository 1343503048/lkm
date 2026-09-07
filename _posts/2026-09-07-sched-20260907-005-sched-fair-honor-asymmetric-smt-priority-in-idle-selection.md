---
id: sched-20260907-005
date: '2026-09-07'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831181800.1668646-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260904091838.3617894-3-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Andrea Righi
maintainers_involved:
- K Prateek Nayak
- Dietmar Eggemann
patch_series:
- version: v1
  msgid: <20260831181800.1668646-3-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 2/2：新增 sched_smt_asym_prefer()/__select_idle_smt_cpu()/select_idle_smt_cpu()/select_idle_smt_priority()，在空闲核扫描、空闲
    CPU 扫描、非对称容量扫描与 target/prev/recent_used_cpu 快路径上按 SD_ASYM_PACKING 优先级挑兄弟线程；用 for_each_domain()
    只在带 SD_SHARE_CPUCAPACITY 的层判断。kernel/sched/fair.c +81/-9。
  review_outcome: Dietmar Eggemann 09-03 提四点意见（适用范围、cpumask_test_cpu 是否冗余、for_each_domain
    多余、select_idle_smt() 在 SMT2 上是未被测试覆盖的死路径）。
- version: v1（09-04 重发；cover 标为 v2、补丁 subject 未带版本标签）
  msgid: <20260904091838.3617894-3-arighi@nvidia.com>
  date: '2026-09-04'
  summary: 按 Eggemann 意见改为直接看最低域 rcu_dereference_all(cpu_rq(cpu)->sd) 并要求 SD_SHARE_CPUCAPACITY
    与 SD_ASYM_PACKING 同时置位，保留 cpumask_test_cpu(other, sched_domain_span(sd))（isolcpus
    可把兄弟拆进不同域）；描述里明确覆盖 POWER7。fair.c +79/-9。
  review_outcome: K Prateek Nayak 09-07 建议把判断内联进 select_idle_sibling() 并用 for_each_cpu_and(sibling,
    sched_domain_span(sd), cpus) 省掉重复解引用；提出宽 SMT 收益疑问与「只在 select_idle_sibling() 收口做一次」的
    diff。作者接受并将以 goto out + 仅在有候选时跳转的形态重做，宣布随后发 v3。本日无 tag。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - SMT-4/SMT-8 上的收益与额外搜索开销完全没有数据，Prateek 只能拿 threads=8 的 VM 测且性能太飘，Shrikanth Hegde
    尚未回帖
  - v3 需重构成单一收口点（select_idle_sibling() 末尾一次调用），且内联后的候选集合从扫描掩码变为 p->cpus_ptr，语义等价性待验证
  - Eggemann 指出的 select_idle_smt() 死路径问题在本日讨论中未被单独结论化，需看 v3 如何消除
  - 1/2 落在 arch/arm64 拓扑代码，仍无 arm64 维护者表态，合入路由未定
  - 收益仅作者自报的单平台单 workload（88 线程 GEMM 9.4 → 10.1 TFLOP/s），本日无任何新数据
  next_action: 等作者测完发 v3（收口到 select_idle_sibling() + 内联域判断）；同时关注 Shrikanth Hegde/IBM
    是否给出宽 SMT 的实测回应，以及 arm64 拓扑侧是否表态
contribution_opportunities:
- kind: testing
  description: 在 SMT4/SMT-8 物理机上构造「无空闲核但有空闲兄弟」的高并行短唤醒负载，对比按 rank 排序与保持 !has_idle_core
    原路径两种配置，直接回答 Prateek 向 Shrikanth 提出的开销/收益问题
- kind: review
  description: 验证收口后的语义等价性：现版本 select_idle_core()/select_idle_capacity() 传扫描掩码 cpus，收口到
    select_idle_sibling() 末尾改用 p->cpus_ptr，两者在受限 cpuset/isolcpus 场景下可选兄弟集合可能不同
- kind: testing
  description: 用 cpuset 独占分区与 isolcpus 把同一物理核的兄弟拆进不同调度域，确认合并为 for_each_cpu_and(sibling,
    sched_domain_span(sd), cpus) 之后作者坚持保留的域 span 检查仍然成立
- kind: new_patch
  description: 评估内部 SMT4 平台是否需要该框架：只有架构侧提供带 SD_ASYM_PACKING 的 SMT 域并声明优先级才会生效，若内部微架构存在「退回单线程模式不即时」的同类行为，可复用该框架而非直接
    cherry-pick
source_email_count: 4
related_articles:
- sched-20260903-009
tags:
- cfs
- idle
- hyperthreading
- topology
title: 'sched/fair: Honor asymmetric SMT priority in idle selection'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 [[sched-20260903-009]]。09-07 上午 K Prateek Nayak（AMD）对 Andrea Righi（NVIDIA）这套「空闲选择时尊重非对称 SMT 优先级」的改动给出一个降开销的 nit——把 `sched_smt_asym_prefer()` 的判断内联进 `select_idle_sibling()` 路径，省掉每次 `cpu_rq(cpu)->sd` 解引用和 `cpumask_test_cpu()`；并抛出两个更实质的问题：宽 SMT（SMT-4/SMT-8）上核已经忙时 rank 排序还值不值得那点额外搜索开销，以及既然每条路径都要走 `select_idle_smt_priority()`，能否只在 `select_idle_sibling()` 收口处做一次。Andrea 全部接受（「Yes, agreed. I like this way more.」）并进一步修掉了 Prateek diff 里末尾 fallback 会白做一次优先级查找的问题，最后明确「I'm going to run some tests with this and will send a v3 later」。本日无新版本发出，收益数据仍停留在 v1/v2 cover 里那组 9.4 → 10.1 TFLOP/s。

## 背景与问题

问题本体（详见 [[sched-20260903-009]]）：`SD_ASYM_PACKING` 会给共享同一个 SMT 核的 CPU 排序，但空闲 CPU 选择不参考这个顺序，任务可以落在任意兄弟线程上并停留到负载均衡纠正为止。NVIDIA Olympus/Vera 的痛点不是容量非对称（PE0/PE1 稳态容量相等），而是「换活跃兄弟」本身很贵——从两线程模式退回全资源单线程模式需要兄弟持续空闲约 10 Ki cycles 的 qualification interval（`293f9611ae735` 的结论）。POWER7 在 SMT 层同样使用 `SD_ASYM_PACKING`，且是 SMT4，属于同一套通用逻辑的第二个用户。

本日新增的维度是**代价**：这套逻辑挂在 `select_idle_sibling()` 的多条快路径与 `select_idle_core()`/`select_idle_cpu()`/`select_idle_smt()`/`select_idle_capacity()` 的多个返回点上，AMD 侧关心的是这些 hook 在非 SMT-ASYM 机器上是否零成本、在宽 SMT 机器上多出来的搜索是否能被收益抵掉。

## 技术方案

当前版本（09-04 重发）的实现要点：`sched_smt_asym_prefer(cpu, other)` 直接取最低调度域 `rcu_dereference_all(cpu_rq(cpu)->sd)`，要求它同时带 `SD_SHARE_CPUCAPACITY` 与 `SD_ASYM_PACKING`，再用 `cpumask_test_cpu(other, sched_domain_span(sd))` 确认两者同域（作者的理由：`isolcpus` 可能把硬件兄弟拆进不同调度域），最后转调既有 `sched_asym_prefer()`；`__select_idle_smt_cpu()` 在 `cpu_smt_mask(cpu)` 与给定掩码的交集中挑优先级最高的可用兄弟；外层 `select_idle_smt_cpu()` 由 `sched_smt_asym_active()` 静态分支保护，`select_idle_smt_priority(p, cpu)` 以 `p->cpus_ptr` 为约束。规模 `kernel/sched/fair.c` +79/-9、`kernel/sched/sched.h` +6、`kernel/sched/topology.c` +36。

本日讨论中的两处重构（均出自 Prateek 贴出的 diff，他自己注明「Only build tested」）：

1. **内联判断、合并掩码遍历**：在调用点直接取 `sd = rcu_dereference_all(cpu_rq(cpu)->sd)`，`!sd` 或两个 flag 不齐时 `return cpu`，随后用 `for_each_cpu_and(sibling, sched_domain_span(sd), cpus)` 遍历。按他的说法「Both, domain span and task affinity will be covered at once」——域 span 检查与任务亲和性在一次交集中解决，因此不再需要每兄弟一次 `cpu_rq(cpu)->sd` 解引用与 `cpumask_test_cpu()`。
2. **收口到单一调用点**：把 `select_idle_sibling()` 里散落的 `return`（target 快路径、prev 快路径、`prev == smp_processor_id()` 路径、recent used CPU、`select_idle_capacity()`、`select_idle_smt()`、`select_idle_cpu()`）改成 `target = x; goto out`，在 `out:` 处统一做一次 `if (!sched_smt_asym_active()) return target; return select_idle_smt_priority(p, target);`。

Andrea 在此基础上又收了一刀：末尾 fallback 不应该无条件做这次查找。她的写法是 `i = select_idle_cpu(p, sd, has_idle_core, target);` 之后仅在 `(unsigned)i < nr_cpumask_bits` 时 `target = i; goto out;`，`prev_aff` 与 `recent_used_cpu` 两个 fallback 同样「已经验证过是合适候选」可直接跳 `out`；一条路径都没选中时保持原有 `return target` 不变。Prateek 确认的形态就是在 `return target;` 之后才放 `out:` 标签。

## 版本演进与当前进展

- 08-31 18:18 UTC 首发 2 补丁系列（cover `<20260831181800.1668646-1-arighi@nvidia.com>`），2/2 见 `<20260831181800.1668646-3-arighi@nvidia.com>`。
- 09-03 18:59 Dietmar Eggemann 对 2/2 提四点意见（适用范围是否含 POWER7、`other` 是否总在 mask 内、`for_each_domain()` 多余、`select_idle_smt()` 这个 hook 在 SMT2 上是未被测试覆盖的死路径）。
- 09-04 13:59 作者逐条回应：确认 POWER7 同样受影响并会改写描述、承认「walking the domain hierarchy is unnecessary」、坚持 `sched_domain_span()` 检查对 `isolcpus` 场景必要、承认 Vera 上的测试实际走的是 `select_idle_capacity()`。
- 09-04 17:18 重发（cover `<20260904091838.3617894-1-arighi@nvidia.com>` 标为 `[PATCH v2 0/2]`，changelog 只有两条：描述里补上 POWER7、按 Eggemann 意见直接看最低域；并注明 link to v1）。值得注意的是 **2/2 补丁自身的 subject 仍是 `[PATCH 2/2]`、不带版本标签**，而作者在 09-07 把下一版称为 **v3**，两处的版本编号口径并不一致（本篇按日报规范记 `current_version: v1`）。
- 09-07 本日 4 封邮件全部是评审讨论，无新版本贴出，无 `Acked-by`/`Reviewed-by`。1/2（`arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores`）本日无人评论，也仍无 arm64 维护者表态。

## Maintainer 意见与讨论焦点

- **K Prateek Nayak（AMD，11:57）**三点：
  1. `sched_smt_asym_prefer()` 只在这一处用、且 `rq->sd` 必然就是带 `SD_SHARE_CPUCAPACITY | SD_ASYM_PACKING` 的那个域，因此建议内联并换成 `for_each_cpu_and()`（省掉重复解引用与 `cpumask_test_cpu()`）。这是纯开销 nit，不是反对方向。
  2. 把问题甩给 Shrikanth Hegde（IBM，本日未回帖）：「On larger SMT (SMT-4, SMT-8), does the ranking make that big of a difference if the core is already busy?」以及额外搜索开销能否被「放到更好的线程」的收益抵掉，若抵不掉「maybe the paths for `!has_idle_core` can stay as is?」——即更宽 SMT 那部分代码有可能被要求整块留在原地或拿掉。
  3. 既然每条路径都会走 `select_idle_smt_priority()`，为何不在 `select_idle_sibling()` 里只做一次（附只做过 build test 的 diff）。
- **Andrea Righi（作者，17:11）**：同意 1 与 3；对第 2 点表态「On Olympus it'd be fine either way, since it's an SMT2」并把宽 SMT 的问题同样让给 Shrikanth（自己没有这类机器）。对 3 补了一个关键修正：idle scan 失败或 `SIS_UTIL` 扫描预算耗尽之后再做一次 `select_idle_smt_priority()` 可能是浪费，只在真正选出候选时才跳 `out`。
- **K Prateek Nayak（17:40）**：确认这个形状（`return target;` 之后才放 `out:`），并给出测试条件上的坦白——「Best I can do is a VM with -cpus ...,threads=8 but performance on those are super flaky to make any meaningful deductions.」
- **Andrea Righi（17:50）**：「Exactly.」/「Correct, I'm going to run some tests with this and will send a v3 later.」
- 焦点已经从 09-03 的「这个 hook 该不该存在」转成「这套逻辑放在哪里、做几次、在宽 SMT 上是否划算」。前者是正确性/覆盖面之争，后者是本日双方一致认可的收敛方向。
- 本日未见 Peter Zijlstra、Ingo Molnar、Vincent Guittot、Shrikanth Hegde 发言。

## 合入评估

`likelihood=medium`。

依据（正向）：AMD 与 NVIDIA 两边的调度开发者在同一封邮件线程里对最终形态达成了一致，且达成的形态比 v1/v2 更小（单一收口点 + 单次查找 + 一次掩码交集）；作者已公开宣布要发新版本并重测；方向本身在 09-03 之后没有再被质疑——改动被 `sched_smt_asym_active()` 静态分支和「架构必须提供带 `SD_ASYM_PACKING` 的 SMT 域」双重门控，x86 与绝大多数 arm64 平台行为不变。

卡点：一是宽 SMT（POWER7 的 SMT4、SMT-8）的收益与开销目前**没有任何一份数据**，Prateek 明确表示只能拿 8 线程虚拟机的 VM 测、性能太飘，这个问题若最终无人能答，`!has_idle_core` 相关分支可能按要求维持原样；二是 Eggemann 提的 `select_idle_smt()` 死路径问题在本日讨论中未被重新拾起，收口到 `select_idle_sibling()` 之后这条 hook 的存在形态本身会变化，需要在 v3 里看清是否被自然消除；三是 1/2 落在 `arch/arm64/`，合入路由（tip 还是 arm64 + sched 两路）仍未定；四是收益数字仍是作者自报的单平台单 workload（88 线程单精度 GEMM）。

## 效果评估

本日**没有新的性能数据**，四封邮件全部是设计/开销层面的讨论。可用的量化证据仍只有 cover letter 那一条：2 节点 Vera、限制在 NUMA node 0 的 88 个物理核上跑 88 线程单精度 GEMM，约 9.4 TFLOP/s → 约 10.1 TFLOP/s，重复运行一致性变好（稳定落在 PE0、PE1 保持安静）；无运行次数、方差、频率/温度受控说明，也没有 `perf` 或迁移计数层面的因果证据。

关于「额外搜索开销」这个本日核心争议点，唯一可参考的信息是 Prateek 自述的测试条件：`-cpus ...,threads=8` 的虚拟机上性能数字太不稳定，无法得出结论。SMT-4/SMT-8 物理机（POWER7 等）侧本日无人给出实测。收口成单次 `select_idle_sibling()` 调用带来的常数开销下降，邮件里也没有给出量化（双方都只从代码形状论证）。

## 我可以参与的点

- 直接回答线程里悬着的第二个问题，这是目前最缺、也最容易做出增量的贡献：手上若有 SMT4/SMT-8 物理机（arm64 SMT4 或 POWER），构造「核已满/无空闲核但存在空闲兄弟」的高并行短唤醒负载，分别测「按 rank 排序」与「保持 `!has_idle_core` 原路径」两种配置，同时采 select_idle 路径的命中次数与搜索耗时。Prateek 已明说他没有这类机器、虚拟机数据不可用，Shrikanth 尚未回帖——谁给数据谁定调。
- 复核收口后**语义是否等价**：现版本在 `select_idle_core()`/`select_idle_capacity()` 里传的是扫描掩码 `cpus`，而收口到 `select_idle_sibling()` 末尾时用的是 `p->cpus_ptr`；两者在受限 cpuset、`isolcpus`、cpus_share_resources/cluster 早退这些场景下能选出的兄弟集合不一定相同。把「内联 + 单次收口」这版实现出来并对比选中 CPU 的分布，是能直接进 v3 的意见。
- 顺带把 cpuset/分区视角的验证补上（这也是本简报读者最有优势的一块）：用独占 cpuset 分区、`isolcpus` 把同一物理核的兄弟拆进不同调度域，验证作者坚持保留的域 span 检查在合并成 `for_each_cpu_and(sibling, sched_domain_span(sd), cpus)` 之后仍然成立——这正是他与 Eggemann/Prateek 之间唯一保留意见的技术点。
- 跟进节奏：v3 出来后再判断是否值得回合。OLK 侧若无「换兄弟代价高」的 SMT 拓扑（即没有 `SD_ASYM_PACKING` 的 SMT 域提供者），这套通用逻辑对本方内核默认零影响，可只作为观察项；但若内部 SMT4 平台存在同类「退回单线程模式不即时」的微架构行为，本系列提供的正是可直接复用的框架（架构侧只需声明 `SD_ASYM_PACKING` + 优先级）。

## 参考链接

- 本日讨论：
  - K Prateek Nayak 的 nit、两个问题与收口 diff：https://lore.kernel.org/all/ff6763c9-f279-47d2-a279-58c54ab37ee6@amd.com/
  - Andrea Righi 同意并指出末尾 fallback 的问题：https://lore.kernel.org/all/ap5_3R2H80WsD1R5@gpd4/
  - Prateek 确认形态并说明只能测 8 线程 VM：https://lore.kernel.org/all/83b58943-f2ff-4bc5-84b7-a40f03d3c3bd@amd.com/
  - Andrea 宣布将发 v3：https://lore.kernel.org/all/ap6I55W7x_p0I1FE@gpd4/
- 补丁与历史评审：
  - 首发 2/2：https://lore.kernel.org/all/20260831181800.1668646-3-arighi@nvidia.com/
  - 首发 cover（含 9.4 → 10.1 TFLOP/s 数据）：https://lore.kernel.org/all/20260831181800.1668646-1-arighi@nvidia.com/
  - 09-04 重发 cover（`[PATCH v2 0/2]`）：https://lore.kernel.org/all/20260904091838.3617894-1-arighi@nvidia.com/
  - 09-04 重发 2/2：https://lore.kernel.org/all/20260904091838.3617894-3-arighi@nvidia.com/
  - Dietmar Eggemann 的四点意见：https://lore.kernel.org/all/0d02e284-9a07-4f54-bf63-8edaa5e224e5@arm.com/
  - 作者对 Eggemann 的逐条回应：https://lore.kernel.org/all/appeWCqxApU8NmuP@gpd4/
- 相关：[[sched-20260903-009]]、[[sched-20260904-002]]
