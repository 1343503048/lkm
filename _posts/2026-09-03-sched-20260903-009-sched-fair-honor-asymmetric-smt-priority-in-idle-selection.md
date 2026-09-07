---
id: sched-20260903-009
date: '2026-09-03'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: <20260831181800.1668646-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260831181800.1668646-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
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
  - Eggemann 指出 select_idle_smt() 在 SMT2 上是未被测试覆盖的死路径，需删除或补 POWER7 SMT4 实测
  - 1/2 落在 arch/arm64 拓扑代码，尚无 arm64 维护者表态，合入路由未定
  - 收益仅单平台单 workload 的作者自报数据，缺第二方复测与迁移计数佐证
  - 本日无 Acked-by/Reviewed-by
  next_action: 等 v2 收敛 select_idle_smt() 与最低域判断，并推动 arm64 拓扑侧表态
contribution_opportunities:
- 构造无空闲核+部分空闲兄弟场景，统计 select_idle_smt() 与 select_idle_capacity() 命中次数
- 在无 SD_ASYM_PACKING SMT 域的机器上复核 sched_smt_asym_active() 关闭时快路径零开销
- 用 cpuset/isolcpus 拆分物理核兄弟线程，验证兄弟优先级在跨调度域场景是否仍成立
- 评估 OLK-6.6 回合面：三处空闲选择 hook 的同形态与拓扑提供者可用的前提
source_email_count: 1
related_articles: []
tags:
- sched/fair
- topology
- affinity
title: 'sched/fair: Honor asymmetric SMT priority in idle selection'
layout: article
---

## TL;DR

NVIDIA Olympus 的 SMT 两个 PE 稳态容量相等，但从双线程模式回到全资源单线程模式并不即时（Vera 实测需要兄弟空闲约 10 Ki cycles 的 qualification interval），因此反复切换活跃 PE 的代价被放大。Andrea Righi 的 2 patch 系列把 PE0 通过 `SD_ASYM_PACKING` 设成 Olympus 核的 preferred sibling，并让 fair 调度的空闲选择路径在选定核之后按非对称 SMT 优先级挑兄弟线程，作者自报 88 线程单精度 GEMM 从约 9.4 TFLOP/s 提升到约 10.1 TFLOP/s。本日（09-03）Dietmar Eggemann 对 2/2 给出三点实质意见：`for_each_domain()` 遍历多余、`select_idle_smt()` 这一 hook 在 SMT2 下是死路径且未被作者测试覆盖、`sched_domain_span()` 检查是否必要；作者尚未回帖。

## 背景与问题

`SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（`select_idle_sibling()` 及其下游扫描）并不参考该顺序，任务可以落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。

Olympus 的特殊性不在于容量非对称，而在于「换兄弟」这件事本身很贵：单 PE 活跃时核工作在 single-thread 模式并独占全部资源，双 PE 活跃时两者共享；从两线程退回单线程不是即时的。cover letter 直接引用了 commit 293f9611ae735（"sched/fair: Prefer fully idle cores for NOHZ balancing"）里的结论——ILB 结束并进入 WFI 后，兄弟需要持续空闲一段 qualification interval（在 Vera 上约 10 Ki cycles）才能恢复完整单线程性能。那个改动只挡住了 NOHZ 空闲负载均衡误唤醒兄弟，普通任务放置仍可能在同一核的两个 PE 之间来回切换，结果是核长期停留在两线程模式而两个线程之间几乎没有有效重叠。

因此这里的诉求是「稳定选中同一个兄弟」：PE0 与 PE1 稳态容量相等，PE0 只是两个兄弟都可用时的规范选择（canonical choice），一致选中它可让 PE1 更久空闲，从而让更多核保持或退回全资源单线程模式。

## 技术方案

系列共 2 patch，`arch/arm64/*` +3、`arch/arm64/kernel/topology.c` +62、`kernel/sched/fair.c` +81/-9、`kernel/sched/sched.h` +6、`kernel/sched/topology.c` +36：

- **1/2 `arm64: topology: Prefer PE0 on NVIDIA Olympus SMT cores`**：在 arm64 拓扑代码里为 Olympus 的 SMT 域打开 `SD_ASYM_PACKING` 并把 PE0 排为高优先级。通用逻辑只在架构提供带 `SD_ASYM_PACKING` 的 SMT 域时才生效。
- **2/2 `sched/fair: Honor asymmetric SMT priority in idle selection`**：新增 `sched_smt_asym_prefer(cpu, other)`——沿 `for_each_domain()` 只在带 `SD_SHARE_CPUCAPACITY` 的层（即 SMT 层）判断 `SD_ASYM_PACKING` 并转调既有 `sched_asym_prefer()`，注释明确说明更高层的 `SD_ASYM_PACKING` 可能描述的是核排序，不能混用；`__select_idle_smt_cpu()` 在 `cpu_smt_mask()` 与给定掩码的交集中挑「可用且优先级最高」的兄弟，外层 `select_idle_smt_cpu()` 由 `sched_smt_asym_active()` 静态分支保护，`select_idle_smt_priority()` 则以 `p->cpus_ptr` 作为约束掩码。
- hook 点覆盖空闲核扫描（`select_idle_core()`）、部分空闲核扫描（`select_idle_smt()`）、`select_idle_cpu()` 的两条返回路径、非对称容量扫描（`select_idle_capacity()` 的 `fits > 0 && preferred_core` 提前返回与最终 `best_cpu`），以及 `select_idle_sibling()` 的 target、prev、`prev_aff`、recent used CPU 快路径。
- 语义分层被刻意保持：物理核容量选择与 SMT 兄弟排序互不干涉——`SD_ASYM_CPUCAPACITY` 先在最大容量不同的核之间选，`SD_ASYM_PACKING` 再在选中的核内挑可用兄弟，同一核的兄弟容量仍相等。
- 作者对适用面的表述：SMT2 上只在「整核空闲」时改变选择（部分空闲时本就只有 1 个可用 CPU），更宽的 SMT 核则能在核部分忙时按优先级顺序填充可用兄弟。

## 版本演进与当前进展

- 09-01 02:10 首次投递，无版本号（`[PATCH 0/2] sched: Enable preferred SMT siblings on NVIDIA Olympus`），封面即给出测试平台（2 节点 Vera、NUMA node 0 的 88 物理核跑 88 线程单精度 GEMM）与收益数字。
- 09-03 18:59 Dietmar Eggemann 对 2/2 回帖，提出 1 个适用范围疑问与 3 个代码问题，其中 2 个被作者随后认定为需要修改。
- 本日报道口径为首次投递、单条 review、无 tag。作者对 Eggemann 的逐条回应与 `[PATCH v2 0/2]` 重投发生在本日之后（09-04），未计入本篇状态。
- 系列此前无 v1 之外的历史版本，也不存在 `Fixes:` 指向——这是新特性而非回归修复。

## Maintainer 意见与讨论焦点

- **Dietmar Eggemann（Arm，EAS/非对称拓扑维护者）** 本日四点：
  1. 适用范围：「I assume this sentence refers to Olympus/Vera and Power7?」——要求把「通用逻辑」的实际受影响平台讲清楚，因为 `SD_ASYM_PACKING` 出现在 SMT 层的机器极少。
  2. `sched_smt_asym_prefer()` 里 `cpumask_test_cpu(other, sched_domain_span(sd))` 这个判断：「Looks like 'other' is always part of the mask?」——怀疑是冗余检查。
  3. 域遍历本身：「SMT will always the lowest SD, so `for_each_domain()` is not necessary」，并直接给出替代实现：取最低域，判断 `(sd->flags & (SD_SHARE_CPUCAPACITY | SD_ASYM_PACKING)) == (SD_SHARE_CPUCAPACITY | SD_ASYM_PACKING)` 后 `return sched_asym_prefer(cpu, other)`。
  4. 最关键的一条，针对 `select_idle_smt()` 的 hook：「This one is weird for SMT2. AFAICS, `select_idle_smt()` is called when there are no idle cores. So if you find an idle CPU this is what you will return anyway. I guess your tests on Olympus/Vera do wakeups via `select_idle_capacity()` so you haven't touched this one.」——即该 hook 在作者的测试平台上是未被执行到的死路径，加它的正当性只有更宽 SMT 这一种论证。
- 作者的答复发生在本日之后（09-04）：确认平台是 Olympus/Vera 但 POWER7 同样在 SMT 层使用 `SD_ASYM_PACKING`、会改写描述；承认「walking the domain hierarchy is unnecessary. I'll use the lowest domain directly」；对第 2 点保留意见，理由是 `other` 虽总在同一硬件兄弟掩码内却不一定落在同一调度域 span（`isolcpus` 可能把兄弟拆到不同 SD），并指出 `select_idle_smt()` 里同样的 `sched_domain_span()` 检查是同一原因；对第 4 点承认「Correct, Vera also has `SD_ASYM_CPUCAPACITY`, so the scan path used by these tests is `select_idle_capacity()`」，转而以 POWER7 的 SMT4 部分空闲核仍可有多空闲线程来论证 hook 的价值。
- 讨论焦点因此不是方向而是「范围与代价」：新增的通用代码里有多少是被真实平台验证过的，多少是为假设中的 SMT4+ 平台预留的。
- 本 thread 中未见 Peter Zijlstra、Ingo Molnar、Vincent Guittot 发言；本日无 `Acked-by` / `Reviewed-by`。

## 合入评估

likelihood: **possible**。

依据：方向上无人生疑——放置层的兄弟偏好问题已有 `293f9611ae735` 这条同源前例，作者把它从 NOHZ 路径延伸到普通任务放置；改动被 `sched_smt_asym_active()` 静态分支和「架构必须提供带 `SD_ASYM_PACKING` 的 SMT 域」双重门控，x86 与绝大多数 arm64 平台行为不变，回归面小；作者给了明确的量化收益；EAS 维护者当天下场细读并给出可落地写法，属于良性推进节奏。

卡点：一是 Eggemann 指出的 `select_idle_smt()` 死路径必须在「删掉」与「给出 POWER7 SMT4 实测」之间二选一，若只靠文字论证，更宽的 SMT 分支很可能被要求整块拿掉；二是 2/2 之外还有 1/2 落在 `arch/arm64/`，`SD_ASYM_PACKING` 的拓扑语义变更需要 arm64 维护者表态，本 thread 中尚无他们的痕迹，合入路由（tip 还是 arm64+sched 两路）未定；三是收益只有单一 workload（88 线程 GEMM）、单一平台、作者自报，缺少 `hackbench`/`migrate` 计数等第二方数据佐证；四是本日无任何 tag，作者对 review 的响应从时间上发生在下一日。

## 效果评估

cover letter 给了唯一一组数据：在 2 节点 Vera 上，限制 workload 只用 NUMA node 0 的 88 个物理核跑 88 线程单精度 GEMM，允许它自由选用每个核的任一兄弟时，吞吐从基线内核的约 9.4 TFLOP/s 提升到打上本系列后的约 10.1 TFLOP/s（约 +7%），并说明重复运行的一致性变好——workload 稳定落在 PE0、PE1 保持安静。

需要标注的局限：这是作者自报的单平台单 workload 结果，邮件里没有给出运行次数、方差、频率/温度是否受控，也没有 `perf sched migrate`、上下文切换计数或 `sched_debug` 层面的证据来证明「核停留在单线程模式的时间变长」这条因果链。POWER7（SMT4 + SMT 层 `SD_ASYM_PACKING`）只在论证中被提到，没有实测数据。Eggemann 与作者都没有给出功耗或延迟敏感型负载的数据。

## 我可以参与的点

1. 替 Eggemann 的第 4 点补证据：构造「无空闲核但存在部分空闲兄弟」的场景（超过核数的中等并行度 + 高频短唤醒），分别统计 `select_idle_smt()` 与 `select_idle_capacity()` 两条路径的命中次数，直接回答这个 hook 在 SMT2 上到底会不会被执行、在 SMT4 上能否测出差异。
2. 静态分支与掩码开销复核：`select_idle_smt_cpu()` 会被插进 `select_idle_sibling()` 的三条快路径，可在不带 `SD_ASYM_PACKING` SMT 域的机器上测 `select_idle_sibling()` 热点占比（`perf record -g` 对比），确认 `sched_smt_asym_active()` 关闭时确实零开销。
3. cpuset / 分区视角（与本系列争议点直接相关）：作者对「`other` 是否总在 mask 内」的抗辩完全建立在 `isolcpus`/cpuset 会把同一物理核的兄弟拆进不同调度域这一前提上。用 `cpuset` 独占分区、`isolcpus`、以及把兄弟线程分到两个 cgroup 的配置去跑同一 GEMM，观察 `cpus_ptr` 约束下兄弟优先级是否仍生效，能给出社区目前没有的数据点。
4. 回合判断：OLK-6.6 上 `select_idle_core()`/`select_idle_smt()`/`select_idle_capacity()` 的形态与本补丁上下文差异较大，且缺少对应的 `SD_ASYM_PACKING` SMT 拓扑提供者，直接 cherry-pick 价值有限；值得移植的是「先选核、再在核内按固定优先级选兄弟」这条放置约束以及用它解释兄弟抖动引起的性能抖动的诊断思路。

## 参考链接

- 本系列邮件：
  - 封面（含测试数据）：https://lore.kernel.org/all/20260831181800.1668646-1-arighi@nvidia.com/
  - 2/2 补丁：https://lore.kernel.org/all/20260831181800.1668646-3-arighi@nvidia.com/
- 关键回帖：
  - Dietmar Eggemann 的四点意见：https://lore.kernel.org/all/0d02e284-9a07-4f54-bf63-8edaa5e224e5@arm.com/
