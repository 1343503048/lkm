---
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
id: sched-20260901-004
date: '2026-09-01'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/ee97dce1db374f50b8e87e51ad133d96@hygon.cn/
authors:
- Jianyong Wu
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: null
  date: '2026-08-27'
  summary: 23 片 RFC v2 的拓扑数据结构层：02/23 两级 NUMA 距离矩阵（节点矩阵 + 节点内 LLC 矩阵，贪心边着色去重）、08/23
    rq 上的 llc_counts[]/numa_counts[] 偏好计数、09/23 percpu sd 记账、10/23 per-sd scratch
    数组
  review_outcome: Peter Zijlstra 逐片精读：numa_counts[] 记账被要求改成按需累加（作者采纳并将在 v3 删除）；per-sd
    数组需补 __counted_by_ptr(llc_max)/numa_max；质疑贪心着色 2Δ+1 上界并建议欧拉路径类算法；要求 commit message
    写清动机；提出 __build_all_zonelists() 可能复用该矩阵（无人回应）
- version: v1
  msgid: null
  date: null
  summary: v1 未在本日与相邻日缓存中出现，具体差异未获取到
  review_outcome: 未获取到
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - 23 片架构性 RFC，Peter Zijlstra 自述仍在通读（"I'll continue trying to digest the series"），未给出任何
    ack
  - v3 待落实的结构性改动：删除 numa_counts[] 记账、补 __counted_by_ptr 注解、重新选择距离矩阵去重算法
  - 无任何平台收益数据；"单张大矩阵代价过大" 仅为设计陈述
  - __build_all_zonelists() 复用去重矩阵的联动无人评估，若要做需 mm 维护者 ack
  - 09/23 的 per-node 记账动机依赖已被要求删除的 numa_counts，v3 需重新对齐
  next_action: 发 v3 落实本日意见并补跨平台 NUMA 敏感负载数据；就着色算法上界与 mm 侧联动给出明确回应
contribution_opportunities:
- kind: testing
  description: 在多节点 Hygon/其他非全对称互连机型上给出开启/关闭该系列的 NUMA 敏感负载对比数据，附节点间距离拓扑
- kind: discussion
  description: 评估真实服务器每层子图是否足够规则（hypercube/mesh 类）以让欧拉路径类着色达到 Δ，替 Peter 与作者解决着色算法这一未决点
- kind: review
  description: 评估 Peter 提出的 __build_all_zonelists() 复用去重矩阵以区分节点回退顺序的可行性与风险（目前无人回应）
source_email_count: 12
related_articles:
- sched-20260831-005
tags:
- topology
- numa_balancing
- load_balance
generated_at: '2026-09-07'
title: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
layout: article
---

## TL;DR

Jianyong Wu（海光）的 23 补丁 RFC v2（NUMA/LLC 两级亲和性打分负载均衡）在 09-01 进入 Peter Zijlstra 的逐片精读，本文覆盖其中**拓扑数据结构与记账层**的 4 个补丁（02/23、08/23、09/23、10/23）。结论已定型的有两处：per-node 的 `numa_counts[]` 记账被要求改成按需累加（作者同意删），per-sd 数组要补 `__counted_by_ptr` 注解；未定的是距离矩阵的去重算法（贪心边着色只能到 2Δ+1，Peter 希望更紧的上界）以及整个系列的 commit message 质量问题。

## 背景与问题

上游 cache-aware 负载均衡（`CONFIG_SCHED_CACHE`）目前只在 LLC 粒度做聚合与迁移决策，跨 NUMA 节点的放置交给独立的 NUMA balancing 机制，两者互不知情：一个任务在打分时看不到「离它的偏好内存有多远」，负载均衡也就无法在「跨节点」与「换 LLC」之间做统一取舍。该系列的做法是给拓扑加一张**去重后的 NUMA 距离矩阵**，再在 rq / sched_domain 上维护任务偏好计数，最终在 load balance 时用「任务数 × 距离差」算出 affinity score（patch 12）。

对海光这类多节点、非全对称互连的平台，节点间距离不是单一常数，因此需要一张能让每个节点的距离值**互不相同**的矩阵，affinity 打分才有区分度。这就是本补丁存在的理由。

## 技术方案

- **两级矩阵**：作者最初尝试单张完整 LLC 距离矩阵，发现内存与计算代价（尤其后面向量化的 affinity score 计算）无法接受，改成两级：NUMA 节点距离矩阵 + 只编码单节点内 LLC 距离的小矩阵。
- **去重算法**：用贪心边着色把距离值去重，保证每行无重复。Peter 指出上界差异：理论值应是 `Δ` 或 `Δ+1`，贪心的界是 `2Δ+1`；三角存储只省一半、仍是 O(n²)，不算出路；他提示存在实现不难且界更好的算法，并点名「利用超立方体 / 2D mesh 这类拓扑约束的欧拉路径类算法」仍可达到 `Δ`（他同时声明这块自己外行，答案来自 Gemini，要打折扣看待）。
- **偏好计数**（08/23、09/23）：在 rq/sd 上维护 `llc_counts[]` 与 `numa_counts[]`，`numa_counts[node]` 表示该 rq 上「偏好 LLC 落在该 node」的任务数，供 patch 12 的 `numa_counts[node] * distance_delta` 打分使用。
- **per-sd scratch**（10/23）：为负载均衡路径在 sched_domain 上开临时数组，避免热路径分配。

关键取舍与备选：**热路径记账 vs 慢路径重算**。Peter 的立场是记账把成本压到每次 enqueue/dequeue 上（多一次潜在 cache miss），而按需累加只影响本来就慢的 balance 路径；并且如果 `llc_counts[]` 按 node 顺序是稠密的，相关数值大概率落在同一条 cache line 里，累加本身很便宜。作者完全接受，宣布 v3 删掉 `numa_counts[]` 记账、改为按需累加其组成 LLC 计数。

## 版本演进与当前进展

v2 于 2026-08-27 发出（23 片），08-31 起 Peter 开始逐片回帖，09-01 是本系列当天讨论量最大的一天（本文覆盖的 4 片共 12 封）。已明确的 v3 动作项：

- 08/23：**删除 `numa_counts[]` 记账**，NUMA 层打分改为按需累加 `llc_counts[]`（`<80ded281acca43a28043b261e850250c@hygon.cn>`）。
- 08/23：`numa_counts` 按 `nr_node_ids` 定长，需在 `struct sched_domain` 增加 `numa_max` 并加 `__counted_by_ptr(numa_max)`。
- 10/23：per-sd scratch 数组补 `__counted_by_ptr(llc_max)`。
- 02/23：把「为什么不用单张大矩阵」的两级方案论证写进 commit message；调研欧拉路径类着色能否在自家每层子图上达到 `Δ`，再决定是否换算法。
- 09/23：在 commit message 里补上做这件事的**动机**。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra** 本日的四类意见，按分量排序：
  1. **记账位置（08/23）**：`Consider the trade-off. Adding the accounting adds a cache-miss to every enqueue/dequeue, while re-computing the value on-demand adds some little cost to the balancing (slow) path.` 作者当日完全采纳。
  2. **算法上界（02/23）**：贪心边着色 `2Δ+1` vs 理论 `Δ`，要求考虑更好的算法。作者回应会先判断更紧的矩阵对两个消费者是否真有收益，再决定是否增加复杂度——**这是本日唯一没给出确定结论的技术点**。
  3. **跨子系统联想（02/23）**：`I wonder if __build_all_zonelists() wants to use this, rather than the unmodified distance table. This would ensure the node fallback order is distinct between nodes.` 即让 mm 的节点回退顺序也用上这张去重矩阵。**当日无人回应**（作者只回了着色与 changelog 两点）。
  4. **元层面的批评（09/23）**：`So in general I would really appreciate a few words on *why* you're doing things. I mean, I can read the patch and see what it does, but I cannot divinate … This is esp. important for large series -- or series that do complicated things -- or like this case: both!` 作者承诺补 commit message。
- 一个隐含风险：09/23 的作者自述理由是「patch 12 需要 per-node 任务数」，而 08/23 上 `numa_counts[]` 已被要求删掉。同族的 per-node 记账在 v3 里如何自处，Peter 与作者当天没有对齐。
- 本日无 NAK，也无任何 `Reviewed-by`/`Acked-by`；Peter 的自我定位仍在读码阶段（`Right, fair enough. I'll continue trying to digest the series.`）。

## 合入评估

`likelihood = unclear`。这是 23 片规模、带新 CONFIG、改 `struct sched_domain` 布局与 enqueue/dequeue 热路径的架构性 RFC，v2 才刚开始被主评审人逐片读懂，距离可合入还差至少：v3 落实本日这批结构性改动、给出跨平台（不只海光）收益数据、以及 Peter 那句「continue trying to digest」所暗示的完整评审。09-01 当天唯一的确定性进展是**评审节奏很快、意见可执行**——这是正向信号，但不构成合入依据。要推进，作者下一版必须回答的是：删掉 `numa_counts[]` 后 NUMA 层打分的开销与形态、着色算法是否换、以及 `__build_all_zonelists()` 这条 mm 侧联动是否要做（涉及 mm 维护者 ack）。

## 效果评估

本日邮件中**完全没有效果数据**：没有 benchmark、没有机器规格、没有「两级矩阵 vs 单张大矩阵」的实测内存/耗时数字。作者关于「单张 LLC 大矩阵内存与计算时间代价过大」的表述是**设计动机陈述，未见测试数据**。可量化的只有静态事实：系列 23 片；矩阵理论元素数上界为 `Δ`/`Δ+1`，贪心实现为 `2Δ+1`；三角存储只能省一半且仍 O(n²)。NUMA 亲和性收益本身仍是待验证状态。

## 我可以参与的点

- **最有价值的是数据**：这个系列缺的正是跨平台收益证据。若手上有 Hygon 多节点机型，可以做「关闭/开启该系列」的 NUMA 敏感负载对比（SPECjbb、Redis、MySQL 等），并把节点间距离拓扑一并给出；这类回帖在 RFC 阶段对评审权重的影响比代码意见更大。
- **算法侧可参与**：贪心边着色 `2Δ+1` 这个点目前只有方向、没有结论。可以就真实服务器拓扑（每层子图是否接近 hypercube/mesh）给出可着色性与上界的具体判断，直接回应 Peter 与作者都悬而未决的那条。
- **`__build_all_zonelists()` 这条线目前无人回应**：如果你熟悉 mm 的节点回退顺序，帮作者评估「复用去重矩阵」的可行性与风险，是一个明确空缺的讨论位。
- **回合判断**：本系列改的是 `kernel/sched/topology.c` 与 `sched_domain` 结构，与 OLK-6.6 的调度域定制（尤其是自有的 NUMA/LLC 策略）冲突面很大，建议持续跟踪 v3 而不是提前回合。

## 参考链接

- 02/23 当日讨论（Jianyong Wu）: https://lore.kernel.org/all/ee97dce1db374f50b8e87e51ad133d96@hygon.cn/
- 02/23 Peter Zijlstra（上界与算法）: https://lore.kernel.org/all/20260901071322.GX687043@noisy.programming.kicks-ass.net/
- 02/23 Peter Zijlstra（__build_all_zonelists 联想，无人回应）: https://lore.kernel.org/all/20260901084800.GI4121339@noisy.programming.kicks-ass.net/
- 08/23 Peter Zijlstra（cache-miss 取舍）: https://lore.kernel.org/all/20260901102127.GY687043@noisy.programming.kicks-ass.net/
- 08/23 作者决定删除 numa_counts: https://lore.kernel.org/all/80ded281acca43a28043b261e850250c@hygon.cn/
- 09/23 Peter Zijlstra（要求写清动机）: https://lore.kernel.org/all/20260901075457.GO4120091@noisy.programming.kicks-ass.net/
- 10/23 Peter Zijlstra（__counted_by_ptr）: https://lore.kernel.org/all/20260901080210.GP4120091@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到（RFC）
- stable backport: 未获取到
