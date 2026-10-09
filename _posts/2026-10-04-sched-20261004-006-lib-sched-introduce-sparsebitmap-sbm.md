---
id: sched-20261004-006
date: '2026-10-04'
subject: 'lib, sched: Introduce sparsebitmap (sbm)'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261001192849.74788-1-kprateek.nayak@amd.com>
lore_url: https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/
authors:
- K Prateek Nayak
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261001192849.74788-1-kprateek.nayak@amd.com>
  date: '2026-10-02'
  summary: 13 补丁：sbm 核心 + 7 架构 + nohz 首用户
  review_outcome: 10-03 Chen Yu review；10-04 Prateek 逐点回复，三个候选优化方向
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - wakeup 路径 ~10% 维护开销未解
  - 架构 maintainer ACK 收集未开始
  next_action: LPC'26 Scheduling MC；落地 u8/64B/遍历顺序优化试验
contribution_opportunities:
- kind: extend
  description: 实现叶子内先 wrap 遍历变体并跑 nohz 均衡 benchmark
- kind: review
  description: 评审 64B 整行 vs 8 字节 sbm 的取舍并给对比表
generated_at: '2026-10-05T01:00:00'
source_email_count: 2
related_articles:
- sched-20261002-007
- sched-20261003-005
tags:
- cfs
- topology
- nohz
title: 'lib, sched: Introduce sparsebitmap (sbm)'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-007-lib-sched-introduce-sparsebitmap-sbm.html">sched-20261002-007</a>：K Prateek Nayak（AMD）13 补丁 RFC v3——大机器全局 cpumask C2C ping-pong 引入 sparsebitmap（sbm）：按 LLC/节点分片、写保持本地 cacheline；7 架构 enablement；`nohz.idle_cpus_mask` 首个用户；平均 ~1-2% 持平略好、最坏场景更新代价 1/100。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-005-lib-sched-introduce-sparsebitmap-sbm.html">sched-20261003-005</a>：Chen Yu（Intel）首个实质 review——追问 benchmark 归属、wakeup 路径与 Mel Gorman per-sd_share 掩码的趋同、u8 形态猜测、读者侧 LLC sibling 起扫、扩展候选（rto_mask/dlo_mask/tick_broadcast）。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-006-lib-sched-introduce-sparsebitmap-sbm.html">sched-20261004-006</a>（今天）：**Prateek 逐点回复 Chen Yu**：(1) benchmark 是自制的「每 CPU 双线程、一置一清、持续互相让出」负载——模拟「短暂 idle + 短暂运行循环」的最坏情况；(2) 承认 wakeup 路径形态仍贵——「维护该掩码就有 ~10% 开销，正是我想压的目标」；(3) 对 Mel Gorman 64B 整 cacheline 方案给出对比：64B 行可容纳 64 CPU 的数据（sbm 目前只用前 8 字节）；(4) u8 从原子 u64 写降为普通 u8 写可避开昂贵的原子路径（「Going from atomic u64 to plain u8 writes probably avoids an expensive atomic path in the H/W」）；(5) 采纳 LLC 内先 wrap 的扫描试验（「Let me see if wrapping within the bitmask leaf first and then going out makes any difference」）。另确认全部版本都在 16 CPUs/LLC 系统上测过；自嘲「I was just getting started somewhere to see if there is an appetite for sbm :-)」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-007-lib-sched-introduce-sparsebitmap-sbm.html">sched-20261002-007</a>）大容量多插槽/多节点机器上全局 cpumask 是所有核争写的共享 cacheline 集合（C2C ping-pong），`nohz.idle_cpus_mask` 是典型高频更新者。sbm 按 LLC/节点实例分片、每实例只表示少量 CPU。wakeup 路径的适配性（16 CPU/LLC 上叶子更新 ~8-10% 开销）是已知短板。

## 技术方案

（承接 v3 框架）今天回复新增的方案细节：

- **最坏情况基准**：双线程/CPU（一置一清持续互让）模拟「短 idle + 短运行」循环的极端更新频率。
- **候选优化方向**（讨论态）：64B 整 cacheline 利用（对比 sbm 只用前 8 字节，64B 行可容 64 CPU 数据——Mel Gorman per-sd_share 掩码思路）；u8 表示把原子 u64 写降为普通 u8 写（避开硬件原子路径）；扫描侧「先在本叶子内 wrap、再跳出」的遍历顺序试验。
- 全部测试基于 16 CPUs/LLC。

## 版本演进与当前进展

- v3（10-02）→ Chen Yu review（10-03）→ Prateek 逐点回复（10-04）。无新版本；LPC'26 Scheduling MC（下周）现场推进。

## Maintainer 意见与讨论焦点

- **Chen Yu ↔ K Prateek**：纯技术往还、无分歧；Chen Yu 的四点意见均获实质回应，其中三点（64B 利用、u8 写、叶子内 wrap）转化为候选优化方向。
- Peter Zijlstra（核心 3 补丁共同作者）仍未回帖；各架构 maintainer ACK 未开始。

## 合入评估

*likelihood=low*。仍是 RFC + 跨 7 架构 + wakeup 路径开销未解（作者自认 ~10% 目标就是要压它）；但 review 质量高、方向无反对、LPC 曝光在即。*blocking_issues*：wakeup 路径 ~10% 维护开销；架构 ACK 收集。*next_action*：LPC'26 Scheduling MC；按讨论落地 u8/64B/遍历顺序三个优化试验。

## 效果评估

（承接 v3）全局掩码 100% / per-NUMA 32.9% / per-LLC 1.3% / per-LLC u8 0.49% 空间对比；nohz 均衡平均 ~1-2%、最坏更新代价 1/100。今天新增：wakeup 路径掩码维护 ~10% 开销的自认数据（待压）；最坏情况负载的明确定义（双线程互让）。

## 我可以参与的点

- `extend`：实现「叶子内先 wrap」的遍历顺序变体并跑 nohz 均衡 benchmark（Prateek 自己都在找差异，外部数据能加速收敛）。
- `review`：评审 64B 整行方案 vs 现行 8 字节 sbm 的取舍（空间/局部性/遍历成本三角），给对比表回帖。

## 参考链接

- lore（Prateek 回复）: https://lore.kernel.org/all/08df1d81-7671-425b-85bb-51ee79c2eac7@amd.com/
- lore（v3 cover）: https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/
- lore（Chen Yu review）: https://lore.kernel.org/all/asDGbBEHkDouWOwC@three-body/
