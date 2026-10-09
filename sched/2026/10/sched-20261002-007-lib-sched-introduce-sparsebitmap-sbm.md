# lib, sched: Introduce sparsebitmap (sbm)

> **subject**：`lib, sched: Introduce sparsebitmap (sbm)`

## TL;DR

K Prateek Nayak（AMD）的 13 补丁 RFC v3（10 K Prateek + 3 Peter Zijlstra）：大型多节点系统上频繁更新的全局 cpumask（如 nohz idle 掩码）存在严重 C2C ping-pong——方案是引入「sparsebitmap（sbm）」：按 LLC/节点实例分片的位图，每实例只表示少量 CPU，写操作保持在本地 cacheline，代价是遍历更贵。架构通过 `num_instances`（叶子数）+ `max_threads_per_instance` 声明拓扑，sbm 在 CPU 激活时动态分配索引（索引 = 数组下标 + 位偏移的拼装编码）。v3 新增 x86 之外的 7 个架构 enablement（LoongArch/MIPS/PowerPC/s390/sparc64 + 通用 arch_topology），并把 nohz.idle_cpus_mask 转换为 sbm 作为首个用户。实测与基线持平略好（平均 ~1-2%），最坏场景（每次上下文切换一个事件）更新代价降到全局掩码的 1/100。作者将在 LPC'26 Scheduling MC 讲此工作。当日无回帖。

## 背景与问题

大容量多插槽/多节点机器上，调度器与定时器状态用的全局 cpumask 是所有核争写的共享 cacheline 集合——每次置位/清位都要跨 socket 抢 cacheline（C2C ping-pong）。`nohz.idle_cpus_mask` 是典型的高频更新者。Steve Sistare 早近十年前提过 sparsemask（8 CPU/word，但无拓扑感知）；2026 年 3 月 Peter 给了一个最小 sparsebitmap 实现（利用 x86 拓扑解析推导 shift/mask），但未通用化。本系列把 Peter 的想法做成跨架构通用设施。作者自答「为什么不用 lib/sbitmap」：sbitmap 为块层设计、每叶占两个 cacheline 且带 "cleared" 区间语义；「sbm is to sbitmap what cpumask is to plain bitmap」。

## 技术方案

13 补丁（`<20261001192849.74788-1-kprateek.nayak@amd.com>`，20 文件 +883/−51，base tip sched/core @ 1fb28c664a19）：

**核心（lib/sbm.c 253 行 + include/linux/sbm.h 107 行，Peter 的 3 补丁）**
- 架构声明 `num_instances`（叶子/实例数）与 `max_threads_per_instance`（每实例最多 CPU 数），据此计算最坏情况大小的稀疏映射数组。
- CPU 激活时动态分配 sbm 索引；索引编码两段：`[ index in array | bit in that array element ]`，初始化时按拓扑推导 `__sbm_shift`（右移得数组下标）与 `__sbm_mask`（取元素内位偏移）。无架构拓扑时回退为按 BITS_PER_LONG 分块。
- helper：alloc/set/clear/遍历；元数据与 idx↔cpu 映射缓存在独立数组。

**架构 enablement（v3 新增，K Prateek 的 10 补丁中的 7 片）**
- x86（topology 解析后初始化）、drivers/base/arch_topology（通用 DT/ACPI 路径）、LoongArch（含 SRAT 里 disabled CPU 的 _PXM 关系初始化）、MIPS（多节点）、PowerPC（coregroup/NUMA 拓扑；pSeries 热插拔的 CPU↔node 关系可整体改变，按最坏情况构造）、s390（topology_init_early）、sparc64（多 LLC）。
- 各架构 maintainer 均被 CC。

**首个用户**
- 12/13：`nohz.idle_cpus_mask` 改为 sched_init_smp() 时分配；13/13：切换 nohz idle 掩码到 sbm（fair.c +72/−51 的遍历侧适配）。

**Future work（cover 自述）**：与 cpumask 的互操作（sbm 失去 `for_each_cpu_and()` 类优化）；u8 表示 + gather 聚合成稠密掩码；扩展到 wakeup 路径（16 CPU/LLC 系统上 sbm 叶子更新对 benchmark 仍有 ~8-10% 可见影响，尚远）。

## 版本演进与当前进展

- v2（Chenyu Tang 的前作，`<20260510155920.2587431-1-yu.c.chen@intel.com>`，被本系列称作「spiritual successor」；v1/v2 均未在既往分析窗口覆盖）。
- v3（10-01 发出、10-02 进缓存）：新增多架构 enablement；CPU↔sbm 索引关系动态建立。当日无任何回帖。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：3 补丁的作者（sbm 核心 helper + x86 + nohz 切换）——他的原始想法（2026-03-24 邮件）是系列的源头，署名参与本身是强信号，但当日无新表态。
- **K Prateek Nayak**（AMD，系列推动者）：自曝 LPC'26 Scheduling and Real-Time MC 有 talk，「If I have got some topology nuances for your architecture horribly wrong, you have a chance to punch me in the face directly :-)」——主动向各架构维护者要 review。
- 无反对；无维护者正式表态。潜在焦点（待评审暴露）：7 个架构的拓扑解析正确性、sbm 遍历成本对 nohz 侧的影响、与 cpumask API 生态的长期关系。

## 合入评估

*likelihood=low*。跨 7 架构 + lib + sched/fair 的 883 行新增、RFC 阶段、零回帖；即便 Peter 是核心补丁作者，架构侧 ACK 收集本身就是长周期。但它解决了真实且被反复讨论的大机器 C2C 问题、有量化收益、作者有 LPC 曝光计划，属于「方向被认可、工程量大」的典型慢轨。*blocking_issues*：无任何 review（尤其各架构 maintainer）；wakeup 路径的扩展可行性未证明（作者自认 8-10% 开销还差很远）。*next_action*：LPC'26（下周）Scheduling MC 现场收集意见；各架构 maintainer 逐个 ACK。

## 效果评估

cover 引用数据（来源 [3]，AMD 内部 micro-benchmark，%cycles 相对全局掩码操作）：

```
global mask                                : 100.0000%  (var: 3.28%)
per-NUMA mask                              :  32.9209%  (var: 7.77%)
per-LLC mask                               :   1.2977%  (var: 4.85%)
per-LLC mask (u8 operation; no LOCK prefix):   0.4930%  (var: 0.83%)
```

- nohz.idle_cpus_mask 转换后整机性能与基线持平、平均略好 ~1-2%。
- 最坏场景（每次上下文切换一个事件）分布式掩码更新代价为全局掩码的 1/100。
- 未提供目标工作负载（如 nohz-heavy RT 场景）的端到端延迟数据。

## 我可以参与的点

- `review`：核对 PowerPC pSeries 热插拔最坏情况构造（CPU↔node 关系可整体改变）与动态索引分配的交互——这是 cover 自认最难的架构点。
- `testing`：在多节点 x86/ARM 服务器上转换 `nohz.idle_cpus_mask` 跑 nohz-heavy 负载（大量短周期任务进出 idle），对比 sbm 与全局掩码的 C2C 流量（perf c2c）与端到端延迟，补充作者缺失的整机数据。
- `discussion`：sbm 与 cpumask 互操作（future work 第一条）的设计——遍历侧是否值得提供 `sbm_for_each_cpu` 转 cpumask 的批量 gather API。

## 参考链接

- RFC v3 cover: https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/
- 13/13（nohz 切换）: https://lore.kernel.org/all/20261001192849.74788-14-kprateek.nayak@amd.com/
- Peter 的原始想法: https://lore.kernel.org/lkml/20260324120008.GB3738010@noisy.programming.kicks-ass.net/
- Sistare 的 sparsemask（2015）: https://lore.kernel.org/lkml/1541767840-93588-2-git-send-email-steven.sistare@oracle.com/

---
id: sched-20261002-007
date: '2026-10-02'
subject: 'lib, sched: Introduce sparsebitmap (sbm)'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20261001192849.74788-1-kprateek.nayak@amd.com>'
lore_url: 'https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/'
authors:
  - 'K Prateek Nayak'
  - 'Peter Zijlstra'
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: '<20261001192849.74788-1-kprateek.nayak@amd.com>'
    date: '2026-10-02'
    summary: '13 补丁：sbm 核心库 + 7 架构 enablement + nohz.idle_cpus_mask 切换为首个用户'
    review_outcome: '当日无回帖；Peter 是其中 3 补丁作者（想法源自他 2026-03 的 sketch）'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '无任何 review（尤其 7 个架构的 maintainer ACK）'
    - 'wakeup 路径扩展可行性未证明（自认 8-10% 开销）'
  next_action: 'LPC''26 Scheduling MC 收集意见；架构 maintainer 逐个 ACK'
contribution_opportunities:
  - kind: review
    description: '核对 PowerPC pSeries 热插拔最坏情况构造与动态索引分配交互'
  - kind: testing
    description: '多节点服务器跑 nohz-heavy 负载对比 sbm 与全局掩码的 C2C 流量与延迟'
  - kind: discussion
    description: 'sbm 与 cpumask 互操作/gather API 设计'
generated_at: '2026-10-03T01:00:00'
source_email_count: 4
related_articles: []
tags:
  - nohz
  - topology
---
